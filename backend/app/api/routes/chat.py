import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.services.retrieval_service import RetrievalService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


from typing import Optional, List
from sqlalchemy.orm import Session
from app.api.routes.upload import get_db
from app.services.memory_service import MemoryService
import uuid

class QueryRequestSchema(BaseModel):
    question: str
    session_id: Optional[str] = None
    file_id: Optional[str] = None
    file_ids: Optional[List[str]] = None
    user_id: Optional[int] = 1


@router.post("/query")
async def query_rag_pipeline(
    request: QueryRequestSchema,
    db: Session = Depends(get_db)
):
    """
    RAG Chat API endpoint.
    Performs query embedding, similarity search on ChromaDB,
    context compilation, and streams the grounded answer from local Ollama.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Validate session_id format if provided
    valid_session_id = None
    if request.session_id:
        try:
            valid_session_id = uuid.UUID(request.session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session_id format. Must be a valid UUID.")

    # 1. Detect available model from local Ollama server dynamically
    # Falls back to "llama3" if connection fails or no tags exist
    model_name = "llama3"
    try:
        # Check local Ollama server config dynamically
        from app.services.llm_service import OLLAMA_URL
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    model_name = models[0]
                    logger.info(f"Dynamically selected model '{model_name}' for RAG inference.")
    except Exception as error:
        logger.warning(f"Ollama tags lookup failed, using default model '{model_name}': {str(error)}")

    # 2. Retrieve history and rewrite query for semantic search (if session history exists)
    history = []
    search_query = request.question
    if valid_session_id:
        history_records = MemoryService.get_session_history(
            db=db,
            session_id=str(valid_session_id),
            user_id=request.user_id or 1,
            limit=6
        )
        history = [{"role": r.role, "content": r.content} for r in history_records]
        if history:
            search_query = LLMService.rewrite_query(request.question, history, model_name=model_name)

    # 3. Compile metadata filters to isolate queries by user and files
    filter_params = {
        "user_id": request.user_id,
        "file_id": request.file_id,
        "file_ids": request.file_ids
    }

    # 4. Retrieve grounded context using the rewritten search query
    retrieved_chunks = []
    try:
        logger.info(f"Retrieving context for RAG query: '{search_query}' (original: '{request.question}')")
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
        # Fallback to empty chunks list instead of failing the request
        retrieved_chunks = []

    # 5. Save the user message to history
    if valid_session_id:
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

    # 6. Stream response back using StreamingResponse
    logger.info(f"Initiating RAG response stream using model '{model_name}'...")

    async def response_generator():
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

            # Extract cited source chunks using CitationService on completion
            from app.services.prompt_builder import PromptBuilderService
            from app.services.citation_service import CitationService
            import json

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

            # Append structured citations separator and JSON string payload
            citations_suffix = f"\n\n---CITATIONS---\n{json.dumps(citations)}"
            yield citations_suffix

            # Save generated assistant response to history
            if valid_session_id and accumulated_text.strip():
                try:
                    MemoryService.save_message(
                        db=db,
                        session_id=str(valid_session_id),
                        user_id=request.user_id or 1,
                        role="assistant",
                        content=accumulated_text
                    )
                except Exception as db_err:
                    logger.error(f"Failed to save assistant response message: {str(db_err)}")

        except Exception as err:
            logger.error(f"Error in query stream generator: {str(err)}")
            yield f"\n[Stream Error: {str(err)}]"

    return StreamingResponse(
        response_generator(),
        media_type="text/plain"
    )



