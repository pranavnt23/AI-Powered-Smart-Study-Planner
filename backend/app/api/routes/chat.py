import logging
import httpx
import uuid
import json
import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from app.api.routes.upload import get_db
from app.models.conversation import Conversation
from app.models.chat_message import ChatMessage
from app.models.uploaded_file import UploadedFile
from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService, OLLAMA_URL
from app.services.memory_service import MemoryService
from app.services.intent_router import IntentRouterService
from app.services.summarizer import SummarizationService
from app.services.quiz_generator import QuizGenerationService
from app.services.prompt_builder import PromptBuilderService
from app.services.citation_service import CitationService
from app.services.syllabus_analyzer import SyllabusAnalyzerService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


class QueryRequestSchema(BaseModel):
    question: str
    session_id: Optional[str] = None
    file_id: Optional[str] = None
    file_ids: Optional[List[str]] = None
    user_id: Optional[int] = 1


class ConversationSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: int
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


@router.post("/query")
async def query_rag_pipeline(
    request: QueryRequestSchema,
    db: Session = Depends(get_db)
):
    """
    RAG Chat API endpoint with Chat-First Intent Detection.
    Classifies query, dynamically routes to Summary/Quiz engines, or handles general conversation.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Resolve and validate/create Session ID
    valid_session_id = None
    if request.session_id:
        try:
            valid_session_id = uuid.UUID(request.session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session_id format. Must be a valid UUID.")

    if not valid_session_id:
        valid_session_id = uuid.uuid4()

    # Retrieve or create Conversation record
    conv = db.query(Conversation).filter(Conversation.id == valid_session_id).first()
    if not conv:
        words = request.question.split()
        title = " ".join(words[:5]) if words else "New Study Session"
        conv = Conversation(
            id=valid_session_id,
            user_id=request.user_id or 1,
            title=title
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 2. Extract static properties before returning to prevent DetachedInstanceError on deferred streaming
    session_title = conv.title
    session_id_str = str(valid_session_id)

    # 3. Extract context file parameters
    target_file_id = request.file_id
    if not target_file_id and request.file_ids:
        target_file_id = request.file_ids[0]

    # Fallback to user's most recently uploaded file if none is specified
    if not target_file_id:
        recent_file = (
            db.query(UploadedFile)
            .filter(UploadedFile.user_id == (request.user_id or 1))
            .order_by(UploadedFile.uploaded_at.desc())
            .first()
        )
        if recent_file:
            target_file_id = str(recent_file.id)

    # 3. Detect intent classification
    intent = IntentRouterService.detect_intent(request.question)

    # 4. Route: 'summary' intent execution
    if intent == "summary":
        if target_file_id:
            try:
                summary_record = SummarizationService.generate_summary(
                    db=db,
                    user_id=request.user_id or 1,
                    file_id=target_file_id,
                    granularity="detailed"
                )
                MemoryService.save_message(
                    db=db,
                    session_id=str(valid_session_id),
                    user_id=request.user_id or 1,
                    role="user",
                    content=request.question
                )
                confirm_msg = (
                    f"I have successfully generated a structured study guide summary for the document: "
                    f"**{summary_record.title}**!\n\nYou can access, read, and review this guide anytime inside "
                    f"the **Study Library** tab."
                )
                MemoryService.save_message(
                    db=db,
                    session_id=str(valid_session_id),
                    user_id=request.user_id or 1,
                    role="assistant",
                    content=confirm_msg
                )

                async def summary_stream_generator():
                    # Stream new session metadata header
                    metadata_hdr = f"---METADATA---\n{json.dumps({'session_id': session_id_str, 'title': session_title})}\n\n"
                    yield metadata_hdr
                    yield confirm_msg

                return StreamingResponse(summary_stream_generator(), media_type="text/plain")
            except Exception as sum_err:
                logger.error(f"Failed summary intent routing, falling back to chat: {str(sum_err)}")
                intent = "chat"
        else:
            logger.warning("Summary intent detected but no active uploaded files exist.")

    # 5. Route: 'syllabus' intent execution
    if intent == "syllabus":
        if target_file_id:
            try:
                syllabus_record = SyllabusAnalyzerService.analyze_syllabus(
                    db=db,
                    file_id=target_file_id
                )
                MemoryService.save_message(
                    db=db,
                    session_id=str(valid_session_id),
                    user_id=request.user_id or 1,
                    role="user",
                    content=request.question
                )
                confirm_msg = (
                    f"I have successfully analyzed the syllabus and compiled a structured course map for "
                    f"**{syllabus_record['course_name']}** ({syllabus_record['subject_code']})!\n\n"
                    f"- **Total topics extracted**: {syllabus_record['total_topics']}\n"
                    f"- **Estimated difficulty**: {syllabus_record['estimated_difficulty'].capitalize()}\n\n"
                    f"You can explore, read, and track your study progress for this course in the "
                    f"**Study Library** tab under this document's Details."
                )
                MemoryService.save_message(
                    db=db,
                    session_id=str(valid_session_id),
                    user_id=request.user_id or 1,
                    role="assistant",
                    content=confirm_msg
                )

                async def syllabus_stream_generator():
                    metadata_hdr = f"---METADATA---\n{json.dumps({'session_id': session_id_str, 'title': session_title})}\n\n"
                    yield metadata_hdr
                    yield confirm_msg

                return StreamingResponse(syllabus_stream_generator(), media_type="text/plain")
            except Exception as syl_err:
                logger.error(f"Failed syllabus intent routing, falling back to chat: {str(syl_err)}")
                intent = "chat"
        else:
            logger.warning("Syllabus intent detected but no active uploaded files exist.")

    # 6. Route: 'quiz' intent execution
    if intent == "quiz":
        if target_file_id:
            try:
                quiz_params = IntentRouterService.extract_quiz_params(request.question)
                quiz_record = QuizGenerationService.generate_quiz(
                    db=db,
                    user_id=request.user_id or 1,
                    file_id=target_file_id,
                    topic=request.question[:40],
                    difficulty=quiz_params["difficulty"],
                    num_questions=quiz_params["num_questions"]
                )
                MemoryService.save_message(
                    db=db,
                    session_id=str(valid_session_id),
                    user_id=request.user_id or 1,
                    role="user",
                    content=request.question
                )
                confirm_msg = (
                    f"I have generated a new practice quiz for you on topic: **{quiz_record.title}**!\n\n"
                    f"- **Difficulty**: {quiz_params['difficulty'].capitalize()}\n"
                    f"- **Questions**: {quiz_params['num_questions']}\n\n"
                    f"You can test your knowledge and see explanations inside the **Study Library** tab."
                )
                MemoryService.save_message(
                    db=db,
                    session_id=str(valid_session_id),
                    user_id=request.user_id or 1,
                    role="assistant",
                    content=confirm_msg
                )

                async def quiz_stream_generator():
                    metadata_hdr = f"---METADATA---\n{json.dumps({'session_id': session_id_str, 'title': session_title})}\n\n"
                    yield metadata_hdr
                    yield confirm_msg

                return StreamingResponse(quiz_stream_generator(), media_type="text/plain")
            except Exception as quiz_err:
                logger.error(f"Failed quiz intent routing, falling back to chat: {str(quiz_err)}")
                intent = "chat"
        else:
            logger.warning("Quiz intent detected but no active uploaded files exist.")

    # 6. Route: Standard RAG Chat Generation
    # Detect available model from local Ollama server dynamically
    model_name = "llama3"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    if "llama3.2:3b" in models:
                        model_name = "llama3.2:3b"
                    else:
                        model_name = models[0]
                    logger.info(f"Dynamically selected model '{model_name}' for RAG inference.")
    except Exception as error:
        logger.warning(f"Ollama tags lookup failed, using default model '{model_name}': {str(error)}")

    # Retrieve history
    history_records = MemoryService.get_session_history(
        db=db,
        session_id=str(valid_session_id),
        user_id=request.user_id or 1,
        limit=6
    )
    history = [{"role": r.role, "content": r.content} for r in history_records]

    search_query = request.question
    if history:
        search_query = LLMService.rewrite_query(request.question, history, model_name=model_name)

    filter_params = {
        "user_id": request.user_id,
        "file_id": target_file_id,
        "file_ids": [target_file_id] if target_file_id else None
    }

    # Retrieve context chunks
    retrieved_chunks = []
    try:
        retrieval = RetrievalService.retrieve_context(
            query=search_query,
            collection_name="study_materials",
            top_k=4,
            filter_params=filter_params,
            db=db
        )
        retrieved_chunks = retrieval.get("retrieved_chunks", [])
    except Exception as error:
        logger.error(f"Retrieval failure during RAG query: {str(error)}")
        retrieved_chunks = []

    # Save user message to history
    try:
        MemoryService.save_message(
            db=db,
            session_id=str(valid_session_id),
            user_id=request.user_id or 1,
            role="user",
            content=request.question
        )
    except Exception as error:
        logger.error(f"Failed to save user message: {str(error)}")

    async def response_generator():
        # Stream metadata header first
        metadata_hdr = f"---METADATA---\n{json.dumps({'session_id': session_id_str, 'title': session_title})}\n\n"
        yield metadata_hdr

        accumulated_text = ""
        try:
            async for token in LLMService.stream_answer(
                question=request.question,
                chunks=retrieved_chunks,
                model_name=model_name,
                history=history if history else None
            ):
                if token.startswith("\n[Generation Error:"):
                    yield token
                    return
                accumulated_text += token
                yield token

            # Compile citations suffix
            prompt_payload = PromptBuilderService.build_rag_prompt(
                query=request.question,
                chunks=retrieved_chunks,
                history=history if history else None
            )
            included_chunks = prompt_payload.get("included_chunks", retrieved_chunks)

            _, citations = CitationService.parse_citations(
                answer_text=accumulated_text,
                context_chunks=included_chunks
            )
            citations_suffix = f"\n\n---CITATIONS---\n{json.dumps(citations)}"
            yield citations_suffix

            # Save assistant response to history
            if accumulated_text.strip():
                MemoryService.save_message(
                    db=db,
                    session_id=str(valid_session_id),
                    user_id=request.user_id or 1,
                    role="assistant",
                    content=accumulated_text
                )
        except Exception as err:
            logger.error(f"Error in query stream generator: {str(err)}")
            yield f"\n[Stream Error: {str(err)}]"

    return StreamingResponse(
        response_generator(),
        media_type="text/plain"
    )


@router.get("/sessions", response_model=List[ConversationSessionResponse])
def get_user_chat_sessions(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """
    Retrieves all conversation sessions for the target user.
    Used to populate the sidebar chat history pane.
    """
    sessions = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return sessions


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Purges a conversation and cascades to delete all associated messages.
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    conv = db.query(Conversation).filter(Conversation.id == sid).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found.")

    db.delete(conv)
    db.commit()
    return


@router.get("/session/{session_id}/messages")
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve all chat messages for a specific conversation session chronologically.
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == sid)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "from": m.role,
            "message": m.content,
            "time": m.created_at.strftime("%H:%M") if m.created_at else "Now"
        }
        for m in messages
    ]
