import json
import logging
import re
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class StructuredOutputService:
    """
    Service layer responsible for:
    - Enforcing JSON schema generation using Pydantic models.
    - Extracting JSON structures from LLM raw text responses.
    - Validating JSON payloads against target models.
    - Managing self-correction retry loops when validation fails.
    """

    @classmethod
    def extract_json_block(cls, text: str) -> dict:
        """
        Robustly parses a JSON dictionary from raw LLM output strings,
        handling surrounding text wrappers and markdown code fences.
        """
        clean = text.strip()

        # 1. Direct parsing attempt
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # 2. Extract content from markdown json blocks: ```json ... ``` or ``` ... ```
        markdown_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean, re.DOTALL | re.IGNORECASE)
        if markdown_match:
            try:
                return json.loads(markdown_match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. Find bracket bounds { ... }
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = clean[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        raise ValueError("Raw LLM response does not contain a valid JSON block.")

    @classmethod
    def generate_structured(
        cls,
        response_model: Type[T],
        prompt: str,
        system_prompt: str | None = None,
        max_retries: int = 2,
        model_name: str = "llama3",
        temperature: float = 0.0
    ) -> T:
        """
        Executes structured generation using LLMService, validates outputs against
        response_model, and triggers self-correction loops if schemas/syntax are malformed.
        """
        # Generate JSON schema guidelines
        schema_dict = response_model.model_json_schema()
        schema_str = json.dumps(schema_dict, indent=2)

        # Build structural instructions instruction suffix
        instructions = (
            f"\n\nYou MUST return the response strictly in JSON format matching this JSON Schema:\n"
            f"{schema_str}\n"
            f"Do NOT wrap the JSON block in introductory or conversational text. Output ONLY the raw JSON block."
        )

        base_system = system_prompt or "You are a precise study assistance engine."
        full_system = f"{base_system.strip()}{instructions}"

        current_prompt = prompt

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Structured output generation attempt {attempt + 1}/{max_retries + 1}...")
                raw_response = LLMService.generate_answer(
                    question=current_prompt,
                    context="",
                    model_name=model_name,
                    temperature=temperature,
                    system_prompt=full_system,
                    json_mode=True
                )

                # Parse JSON block
                parsed_data = cls.extract_json_block(raw_response)

                # Validate against schema
                validated_object = response_model.model_validate(parsed_data)
                logger.info("Structured output parsed and validated successfully!")
                return validated_object

            except (ValueError, ValidationError, json.JSONDecodeError) as err:
                logger.warning(
                    f"Validation failed on attempt {attempt + 1}/{max_retries + 1}. "
                    f"Error: {type(err).__name__} - {str(err)}"
                )

                if attempt == max_retries:
                    logger.error("Maximum structured output generation retries exceeded. Raising exception.")
                    raise err

                # Self-correction: Build a feedback loop prompt showing the model its own mistake
                error_message = str(err)
                if isinstance(err, ValidationError):
                    # Compile Pydantic error details clearly
                    error_message = json.dumps(err.errors(), indent=2)

                logger.info("Initiating self-correction retry prompt...")
                current_prompt = (
                    f"Your previous response was invalid. "
                    f"It caused the following error during schema validation:\n"
                    f"```\n{error_message}\n```\n\n"
                    f"Your previous response was:\n"
                    f"```json\n{raw_response}\n```\n\n"
                    f"Please correct your formatting and generate a valid JSON response matching the schema. "
                    f"Original instructions:\n{prompt}"
                )
