import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.quiz import Quiz, QuizQuestion
from app.schemas.quiz_schema import QuizSchema, QuestionSchema, QuizCreateRequestSchema
from app.services.quiz_generator import QuizGenerationService
from app.api.routes.quiz import generate_new_quiz, get_quiz_by_id, get_quizzes_by_file_id


class TestQuizGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.query(QuizQuestion).delete()
        self.db.query(Quiz).delete()
        self.db.commit()
        self.db.close()

    @patch("app.services.retrieval_service.RetrievalService.retrieve_context")
    @patch("app.services.structured_output.StructuredOutputService.generate_structured")
    def test_generate_quiz_success(self, mock_generate, mock_retrieve):
        # Set up mock RAG retrieval context response
        mock_retrieve.return_value = {
            "context": "Gravity is a fundamental force pulling objects together. Isaac Newton formulated gravity equations.",
            "retrieved_chunks": [{"document": "Gravity is...", "metadata": {"file_name": "physics.pdf", "chunk_index": 0}}]
        }

        # Set up mock structured output response
        mock_quiz_schema = QuizSchema(
            title="Intro to Gravity",
            questions=[
                QuestionSchema(
                    text="Who formulated gravity equations?",
                    type="mcq",
                    options=["Albert Einstein", "Isaac Newton", "Galileo Galilei"],
                    correct_answer_idx=1,
                    difficulty="easy",
                    explanation="Newton formulated gravity equations in his classical work.",
                    source_citation="Isaac Newton formulated gravity equations."
                )
            ]
        )
        mock_generate.return_value = mock_quiz_schema

        user_id = 1
        file_id = str(uuid.uuid4())

        # Call service
        db_quiz = QuizGenerationService.generate_quiz(
            db=self.db,
            user_id=user_id,
            file_id=file_id,
            topic="Gravity",
            difficulty="easy",
            num_questions=1
        )

        # Assertions
        self.assertIsNotNone(db_quiz.id)
        self.assertEqual(db_quiz.title, "Intro to Gravity")
        self.assertEqual(db_quiz.user_id, user_id)
        self.assertEqual(str(db_quiz.file_id), file_id)
        self.assertEqual(len(db_quiz.questions), 1)

        # Verify DB records
        saved_quiz = self.db.query(Quiz).filter(Quiz.id == db_quiz.id).first()
        self.assertIsNotNone(saved_quiz)
        self.assertEqual(len(saved_quiz.questions), 1)
        self.assertEqual(saved_quiz.questions[0].question_text, "Who formulated gravity equations?")
        self.assertEqual(saved_quiz.questions[0].correct_answer_idx, 1)

    @patch("app.services.retrieval_service.RetrievalService.retrieve_context")
    def test_generate_quiz_no_context_fails(self, mock_retrieve):
        # Return empty context to simulate empty RAG results
        mock_retrieve.return_value = {"context": "", "retrieved_chunks": []}

        with self.assertRaises(ValueError):
            QuizGenerationService.generate_quiz(
                db=self.db,
                user_id=1,
                file_id=str(uuid.uuid4()),
                topic="Quantum Mechanics",
                difficulty="hard",
                num_questions=5
            )

    @patch("app.services.retrieval_service.RetrievalService.retrieve_context")
    @patch("app.services.structured_output.StructuredOutputService.generate_structured")
    def test_generate_quiz_out_of_bounds_correct_idx_safe_fallback(self, mock_generate, mock_retrieve):
        mock_retrieve.return_value = {
            "context": "Context information.",
            "retrieved_chunks": []
        }

        # Mock out of bounds index (e.g. 5, but options has only 2 items)
        mock_generate.return_value = QuizSchema(
            title="Out of Bounds Test",
            questions=[
                QuestionSchema(
                    text="Sample Question",
                    type="true_false",
                    options=["True", "False"],
                    correct_answer_idx=5,  # Out of bounds
                    difficulty="easy",
                    explanation="Sample explanation",
                    source_citation="Citation"
                )
            ]
        )

        db_quiz = QuizGenerationService.generate_quiz(
            db=self.db,
            user_id=1,
            file_id=str(uuid.uuid4()),
            topic="Test",
            difficulty="easy",
            num_questions=1
        )

        # Correct answer index should safely default to 0
        self.assertEqual(db_quiz.questions[0].correct_answer_idx, 0)

    def test_quiz_cascade_deletion(self):
        # Create a quiz directly in DB
        db_quiz = Quiz(
            user_id=1,
            title="Cascade Test",
            file_id=uuid.uuid4()
        )
        self.db.add(db_quiz)
        self.db.commit()
        self.db.refresh(db_quiz)

        # Create a question linked to the quiz
        db_question = QuizQuestion(
            quiz_id=db_quiz.id,
            question_text="Sample text",
            question_type="mcq",
            options=["A", "B"],
            correct_answer_idx=0,
            difficulty="easy",
            explanation="Explanation"
        )
        self.db.add(db_question)
        self.db.commit()

        # Assert records exist
        self.assertEqual(self.db.query(Quiz).count(), 1)
        self.assertEqual(self.db.query(QuizQuestion).count(), 1)

        # Delete Quiz
        self.db.delete(db_quiz)
        self.db.commit()

        # Assert cascade deleted the question rows
        self.assertEqual(self.db.query(Quiz).count(), 0)
        self.assertEqual(self.db.query(QuizQuestion).count(), 0)

    @patch("app.services.quiz_generator.QuizGenerationService.generate_quiz")
    def test_api_generate_route(self, mock_generate):
        mock_quiz = Quiz(id=uuid.uuid4(), title="API Quiz", user_id=1)
        mock_generate.return_value = mock_quiz

        request = QuizCreateRequestSchema(
            file_id=str(uuid.uuid4()),
            topic="Math",
            difficulty="medium",
            num_questions=5,
            user_id=1
        )

        response = generate_new_quiz(request=request, db=self.db)
        self.assertEqual(response.title, "API Quiz")
        self.assertEqual(response.user_id, 1)
        mock_generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
