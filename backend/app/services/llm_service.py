import os
import logging
import httpx
from typing import List, Dict, Any, Optional

from app.services.prompt_builder import PromptBuilderService

logger = logging.getLogger(__name__)

# Configurable local host URL for Ollama service
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")


class LLMService:
    """
    Service layer for local LLM inference using Ollama.
    Communicates with Ollama over HTTP. Adheres to Clean Architecture:
    delegates prompt construction to PromptBuilderService, executes generation,
    and returns the response.
    """

    @classmethod
    def rewrite_query(
        cls,
        question: str,
        history: List[Dict[str, Any]],
        model_name: str = "llama3"
    ) -> str:
        """
        Rewrites a follow-up user query containing pronouns or references to be a standalone,
        context-complete search query for vector retrieval.

        Args:
            question (str): The raw latest follow-up question.
            history (list[dict]): Chronologically sorted list of recent dialogue messages.
            model_name (str): Model name for execution in Ollama.

        Returns:
            str: Standalone rewritten query text.
        """
        if not history:
            return question

        url = f"{OLLAMA_URL}/api/generate"

        system_prompt = (
            "You are a search query expansion assistant. Given the rolling conversation history "
            "and the user's latest follow-up question, rewrite the follow-up question to be a "
            "completely standalone search query. Do NOT answer the question, do NOT add introductory text "
            "(like 'Here is the rewritten query:'), and only output the query text itself."
        )

        history_lines = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")
        history_text = "\n".join(history_lines)

        user_prompt = (
            f"<conversation_history>\n{history_text}\n</conversation_history>\n\n"
            f"Follow-up question to rewrite: '{question}'"
        )

        payload = {
            "model": model_name,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        }

        try:
            logger.info("Sending query rewrite request to Ollama...")
            response = httpx.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            rewritten = response.json().get("response", "").strip()
            # Clean up quotes if model wraps it in quotes
            if rewritten.startswith("'") and rewritten.endswith("'"):
                rewritten = rewritten[1:-1].strip()
            elif rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1].strip()
            logger.info(f"Query rewritten: '{question}' -> '{rewritten}'")
            return rewritten if rewritten else question
        except Exception as error:
            logger.error(f"Error during query rewriting: {str(error)}")
            return question

    @classmethod
    def generate_answer(
        cls,
        question: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None,
        model_name: str = "llama3",
        temperature: float = 0.0,
        history: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        """
        Sends a grounded QA request to the local Ollama LLM instance.
        """
        url = f"{OLLAMA_URL}/api/generate"

        if system_prompt is not None:
            actual_system_prompt = system_prompt
            user_prompt = question
        else:
            # Build production RAG prompt using PromptBuilderService
            if chunks is not None:
                prompt_payload = PromptBuilderService.build_rag_prompt(query=question, chunks=chunks, history=history)
                actual_system_prompt = prompt_payload["system_prompt"]
                if history:
                    user_prompt = f"{prompt_payload['formatted_context']}\n\n{prompt_payload['history_block']}\n\n{prompt_payload['user_prompt']}"
                else:
                    user_prompt = f"{prompt_payload['formatted_context']}\n\n{prompt_payload['user_prompt']}"
            elif context:
                actual_system_prompt = PromptBuilderService.DEFAULT_SYSTEM_PROMPT
                user_prompt = f"<context>\n{context}\n</context>\n\n<user_query>\n{question}\n</user_query>"
            else:
                actual_system_prompt = PromptBuilderService.DEFAULT_SYSTEM_PROMPT
                user_prompt = f"<user_query>\n{question}\n</user_query>"

        payload = {
            "model": model_name,
            "prompt": user_prompt,
            "system": actual_system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9
            }
        }

        if json_mode:
            payload["format"] = "json"

        logger.info(f"Sending request to Ollama ({model_name}) at: {url}...")
        try:
            response = httpx.post(url, json=payload, timeout=60.0)
            response.raise_for_status()

            data = response.json()
            answer = data.get("response", "")
            return answer.strip()
        except httpx.HTTPStatusError as error:
            logger.error(f"Ollama returned HTTP error status: {error.response.status_code}")
            raise RuntimeError(f"Ollama returned error: {error.response.text}")
        except httpx.RequestError as error:
            logger.error(f"Failed to communicate with Ollama at {url}: {str(error)}")
            raise RuntimeError(
                f"Ollama connection failed. Ensure Ollama is running (`ollama serve`) "
                f"and you have pulled the model using `ollama pull {model_name}`."
            )

    @classmethod
    async def stream_answer(
        cls,
        question: str,
        chunks: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None,
        model_name: str = "llama3",
        temperature: float = 0.0,
        history: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Asynchronously streams a grounded QA response from the local Ollama LLM instance
        using chunked SSE transfer. Suitable for real-time interactive user interfaces.
        """
        import json
        url = f"{OLLAMA_URL}/api/generate"

        # Build production RAG prompt using PromptBuilderService
        if chunks is not None:
            prompt_payload = PromptBuilderService.build_rag_prompt(query=question, chunks=chunks, history=history)
            system_prompt = prompt_payload["system_prompt"]
            if history:
                user_prompt = f"{prompt_payload['formatted_context']}\n\n{prompt_payload['history_block']}\n\n{prompt_payload['user_prompt']}"
            else:
                user_prompt = f"{prompt_payload['formatted_context']}\n\n{prompt_payload['user_prompt']}"
        elif context:
            system_prompt = PromptBuilderService.DEFAULT_SYSTEM_PROMPT
            user_prompt = f"<context>\n{context}\n</context>\n\n<user_query>\n{question}\n</user_query>"
        else:
            system_prompt = PromptBuilderService.DEFAULT_SYSTEM_PROMPT
            user_prompt = f"<user_query>\n{question}\n</user_query>"

        payload = {
            "model": model_name,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": 0.9
            }
        }

        logger.info(f"Initiating streaming connection to Ollama ({model_name}) at: {url}...")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                     response.raise_for_status()
                     async for line in response.aiter_lines():
                         if not line:
                             continue
                         try:
                             data = json.loads(line)
                             token = data.get("response", "")
                             if token:
                                 yield token
                         except Exception:
                             continue
        except Exception as error:
            logger.error(f"Error during Ollama stream: {str(error)}")
            yield f"\n[Generation Error: {str(error)}]"


