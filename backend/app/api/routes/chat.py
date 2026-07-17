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


class QueryRequestSchema(BaseModel):
    question: str
    file_id: Optional[str] = None
    user_id: Optional[int] = 1


@router.post("/query")
async def query_rag_pipeline(request: QueryRequestSchema):
    """
    RAG Chat API endpoint.
    Performs query embedding, similarity search on ChromaDB,
    context compilation, and streams the grounded answer from local Ollama.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Compile metadata filters to isolate queries by user and file
    filter_metadata = {}
    if request.user_id:
        filter_metadata["user_id"] = str(request.user_id)
    if request.file_id:
        filter_metadata["file_id"] = str(request.file_id)

    # 2. Retrieve grounded context
    try:
        logger.info(f"Retrieving context for RAG query: '{request.question}'")
        retrieval = RetrievalService.retrieve_context(
            query=request.question,
            collection_name="study_materials",
            top_k=4,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        context = retrieval.get("context", "")
    except Exception as error:
        logger.error(f"Retrieval failure during RAG query: {str(error)}")
        # Fallback to empty context instead of failing the request
        context = ""

    # 3. Detect available model from local Ollama server dynamically
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

    # 4. Stream response back using StreamingResponse
    logger.info(f"Initiating RAG response stream using model '{model_name}'...")
    return StreamingResponse(
        LLMService.stream_answer(
            question=request.question,
            context=context,
            model_name=model_name
        ),
        media_type="text/plain"
    )
