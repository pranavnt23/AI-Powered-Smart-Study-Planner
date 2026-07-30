import os
import logging
import httpx

logger = logging.getLogger(__name__)

# Configurable local host URL for Ollama service
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")


class LLMService:
    """
    Service layer for local LLM inference using Ollama.
    Communicates with Ollama over HTTP. Adheres to Clean Architecture:
    receives query text and pre-formatted context, constructs the prompt,
    executes generation, and returns the response.
    """

    SYSTEM_PROMPT_TEMPLATE = (
        "You are an elite academic AI assistant and study planner. Your goal is to help "
        "the user study, revise, and schedule their learning based on actual facts.\n\n"
        "Instructions:\n"
        "1. Answer the user's question USING ONLY the facts provided in the Context block below.\n"
        "2. If the Context block is empty or does not contain the answer, say honestly that you "
        "cannot find the answer in the uploaded files. Do not fabricate or invent facts.\n"
        "3. Provide structured, clear, and highly readable answers using markdown (lists, bolding, code formats).\n\n"
        "Context:\n"
        "{context}"
    )

    @classmethod
    def generate_answer(
        cls,
        question: str,
        context: str,
        model_name: str = "llama3",
        temperature: float = 0.0
    ) -> str:
        """
        Sends a grounded QA request to the local Ollama LLM instance.

        Args:
            question (str): User's natural language question.
            context (str): Retrieved text chunks formatted with sources.
            model_name (str): Model name pulled in Ollama (default is 'llama3').
            temperature (float): Controls response determinism. Default is 0.0 (grounded).

        Returns:
            str: Generated response text from the local LLM.
        """
        url = f"{OLLAMA_URL}/api/generate"

        system_prompt = cls.SYSTEM_PROMPT_TEMPLATE.format(context=context)

        payload = {
            "model": model_name,
            "prompt": question,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9
            }
        }

        logger.info(f"Sending request to Ollama ({model_name}) at: {url}...")
        try:
            # Setting a 60-second timeout to accommodate local CPU inference
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
        context: str,
        model_name: str = "llama3",
        temperature: float = 0.0
    ):
        """
        Asynchronously streams a grounded QA response from the local Ollama LLM instance
        using chunked SSE transfer. Suitable for real-time interactive user interfaces.
        """
        import json
        url = f"{OLLAMA_URL}/api/generate"
        system_prompt = cls.SYSTEM_PROMPT_TEMPLATE.format(context=context)

        payload = {
            "model": model_name,
            "prompt": question,
            "system": system_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": 0.9
            }
        }

        logger.info(f"Initiating streaming connection to Ollama ({model_name}) at: {url}...")
        try:
            # Using HTTPX async client to stream line-by-line
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
