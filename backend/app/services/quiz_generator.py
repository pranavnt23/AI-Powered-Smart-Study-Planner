import logging
import uuid
import httpx
import os
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.quiz import Quiz, QuizQuestion
from app.schemas.quiz_schema import QuizSchema, QuestionSchema
from app.services.retrieval_service import RetrievalService
from app.services.structured_output import StructuredOutputService

logger = logging.getLogger(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")


class QuizGenerationService:
    """
    Service layer responsible for:
    - Retrieving relevant document chunks for a target topic.
    - Formatting instructions and schemas for structured LLM parsing.
    - Persisting generated quizzes and associated questions to the database.
    """

    @classmethod
    def detect_model(cls) -> str:
        """
        Queries the local Ollama instance dynamically to pick the best active model.
        Falls back to 'llama3' if query fails.
        """
        model_name = "llama3"
        try:
            resp = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                tags = resp.json().get("models", [])
                if tags:
                    names = [m["name"] for m in tags]
                    # Check for llama3.2:3b which is local standard for fast inference
                    if "llama3.2:3b" in names:
                        model_name = "llama3.2:3b"
                    elif "llama3.2:latest" in names:
                        model_name = "llama3.2:latest"
                    else:
                        model_name = names[0]
        except Exception as error:
            logger.warning(f"Ollama tags lookup failed inside Quiz generator, using default model '{model_name}': {str(error)}")
        return model_name

    @classmethod
    def generate_quiz(
        cls,
        db: Session,
        user_id: int,
        file_id: str,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5
    ) -> Quiz:
        """
        Retrieves relevant grounded document context, invokes structured AI validation,
        runs self-correction loops on syntax/schema issues, and saves the final quiz to PostgreSQL.
        """
        logger.info(f"Initiating quiz generation for user {user_id} on file {file_id} (topic: '{topic}', difficulty: {difficulty})...")

        # 1. Retrieve grounded text context
        filter_params = {
            "user_id": user_id,
            "file_ids": [file_id]
        }
        
        retrieval = RetrievalService.retrieve_context(
            query=topic,
            collection_name="study_materials",
            top_k=8,  # Retrieve larger context window for high recall
            filter_params=filter_params,
            db=db
        )
        context = retrieval.get("context", "")

        if not context.strip():
            raise ValueError("No matching document chunks found for the target topic. Cannot generate quiz.")

        # 2. Build structured system prompt
        system_prompt = (
            "You are an expert curriculum designer and academic evaluation engine. "
            "Your task is to generate a high-quality educational quiz based on the provided Context block. "
            "Instructions:\n"
            f"1. Generate exactly {num_questions} questions for the topic '{topic}' matching the difficulty level '{difficulty}'.\n"
            "2. Choose appropriate question types: 'mcq' (Multiple Choice), 'true_false', or 'scenario' (Scenario-Based).\n"
            "3. For every question, generate plausible, high-quality incorrect distractors. Do not use obvious, trivial, or silly options.\n"
            "4. For true_false questions, options list MUST be exactly ['True', 'False'].\n"
            "5. Validate that correct_answer_idx is a valid 0-based index pointing to the correct option in the options list.\n"
            "6. Anchored Grounding: Ensure every question is directly supported by the context. Fabricating facts or questions outside the context is strictly prohibited.\n"
            "7. Supply clear explanations for every question explaining why the correct choice is right and incorrect choices are wrong.\n"
            "8. Extract an inline text citation validating the correct answer and save it under the source_citation field."
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Target Difficulty: {difficulty}\n\n"
            f"Context Documents:\n"
            f"{context}"
        )

        # 3. Detect Ollama model
        model_name = cls.detect_model()

        # 4. Generate structured output with self-correction retry safety
        structured_quiz: QuizSchema = StructuredOutputService.generate_structured(
            response_model=QuizSchema,
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_retries=2,
            model_name=model_name,
            temperature=0.0  # Grounded/deterministic output
        )

        # 5. Save Quiz details to database
        db_quiz = Quiz(
            user_id=user_id,
            title=structured_quiz.title,
            file_id=uuid.UUID(file_id) if file_id else None
        )
        db.add(db_quiz)
        db.commit()
        db.refresh(db_quiz)

        # 6. Save Quiz Questions
        for q in structured_quiz.questions:
            # Basic validation fallback
            correct_idx = q.correct_answer_idx
            if correct_idx < 0 or correct_idx >= len(q.options):
                logger.warning(f"Correct answer index {correct_idx} out of bounds for options {q.options}. Defaulting to 0.")
                correct_idx = 0

            db_question = QuizQuestion(
                quiz_id=db_quiz.id,
                question_text=q.text,
                question_type=q.type,
                options=q.options,
                correct_answer_idx=correct_idx,
                difficulty=q.difficulty,
                explanation=q.explanation,
                source_citation=q.source_citation
            )
            db.add(db_question)

        db.commit()
        db.refresh(db_quiz)
        
        logger.info(f"Successfully generated and saved quiz '{db_quiz.title}' with {len(db_quiz.questions)} questions.")
        return db_quiz
