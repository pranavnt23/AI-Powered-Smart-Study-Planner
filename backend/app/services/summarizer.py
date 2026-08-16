import logging
import uuid
import httpx
import os
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.extracted_document import ExtractedDocument
from app.models.summary import Summary
from app.schemas.summary_schema import SummarySchema
from app.services.llm_service import LLMService
from app.services.structured_output import StructuredOutputService

logger = logging.getLogger(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")


class SummarizationService:
    """
    Service layer coordinating source-grounded summarization.
    Implements:
    - Ordered document chunk collection retrieval.
    - Map-Reduce parallelization workflows for long files.
    - Pydantic validation using StructuredOutputService.
    - PostgreSQL database persistence of structured JSON summary objects.
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
                    if "llama3.2:3b" in names:
                        model_name = "llama3.2:3b"
                    elif "llama3.2:latest" in names:
                        model_name = "llama3.2:latest"
                    else:
                        model_name = names[0]
        except Exception as error:
            logger.warning(f"Ollama tags lookup failed inside Summarizer, using default model '{model_name}': {str(error)}")
        return model_name

    @classmethod
    def generate_summary(
        cls,
        db: Session,
        user_id: int,
        file_id: str,
        granularity: str = "detailed"
    ) -> Summary:
        """
        Orchestrates RAG text ingestion, runs Map-Reduce summaries for large files,
        applies schema validation checks, and saves the final summary to PostgreSQL.
        """
        logger.info(f"Initiating summarization for user {user_id} on file {file_id} (granularity: {granularity})...")

        # 1. Fetch all document chunks sorted chronologically by chunk index
        chunks_db = (
            db.query(DocumentChunk)
            .join(ExtractedDocument, DocumentChunk.document_id == ExtractedDocument.id)
            .filter(ExtractedDocument.file_id == uuid.UUID(file_id))
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        if not chunks_db:
            raise ValueError("No document content found to summarize. Ensure the file has been processed.")

        model_name = cls.detect_model()
        context_text = ""

        # 2. Determine workflow: Direct Synthesis (small file) vs. Map-Reduce (large file)
        if len(chunks_db) <= 4:
            logger.info("Direct Synthesis active: Document size is small (<= 4 chunks). compiling context directly...")
            context_text = "\n\n".join([
                f"--- [Page {c.page_number}]: ---\n{c.chunk_text}" for c in chunks_db
            ])
        else:
            logger.info(f"Map-Reduce active: Document has {len(chunks_db)} chunks. initiating parallel segment summaries...")
            # Group chunks in groups of 3 to respect local context constraints
            chunk_groups = [chunks_db[i:i+3] for i in range(0, len(chunks_db), 3)]
            sub_summaries = []

            # Map Stage: Summarize each segment
            for idx, group in enumerate(chunk_groups, start=1):
                group_text = "\n\n".join([f"--- [Page {c.page_number}]: ---\n{c.chunk_text}" for c in group])
                
                map_prompt = (
                    f"Generate a concise, high-level summary of the following document segment. "
                    f"Retain all critical facts, definitions, and equations mentioned. "
                    f"Segment text:\n{group_text}"
                )
                
                system_instructions = (
                    "You are an academic fact-extraction assistant. Summarize the provided document text, "
                    "focusing strictly on core concepts, definitions, and formulas. Do not invent details."
                )
                
                sub_summary = LLMService.generate_answer(
                    question=map_prompt,
                    context="",
                    model_name=model_name,
                    temperature=0.0,
                    system_prompt=system_instructions
                )
                sub_summaries.append(sub_summary.strip())
                logger.info(f"Mapped segment summary {idx}/{len(chunk_groups)} complete.")

            # Reduce Stage: Fuse sub-summaries for structured synthesis
            logger.info("Reduce Stage: Fusing sub-summaries into final structured output prompt...")
            context_text = "\n\n".join([
                f"--- [Segment Summary #{i+1}] ---\n{summary}" for i, summary in enumerate(sub_summaries)
            ])

        # 3. Formulate structured prompts for the Pydantic schema
        system_prompt = (
            "You are an elite academic editor and synthesis assistant. "
            "Your goal is to parse the provided Context summaries and generate a clean, structured study guide matching the JSON Schema. "
            "Instructions:\n"
            f"1. Generate the overall summary and extract the key topics for a '{granularity}' study guide.\n"
            "2. For every topic, compile core concepts (with definitions) and formulas.\n"
            "3. Grounding: All summaries, concepts, and formulas MUST be directly inferred from the Context summaries.\n"
            "4. Citations: Add inline source indicators (e.g. '[Segment Summary #1]') showing which sections validated each topic."
        )

        user_prompt = (
            f"Granularity: {granularity}\n\n"
            f"Context Summaries:\n"
            f"{context_text}"
        )

        # 4. Invoke Structured Output validation with self-correction feedback loop
        structured_summary: SummarySchema = StructuredOutputService.generate_structured(
            response_model=SummarySchema,
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_retries=2,
            model_name=model_name,
            temperature=0.0
        )

        # 5. Persist the final validated structured summary to database
        db_summary = Summary(
            user_id=user_id,
            file_id=uuid.UUID(file_id),
            title=structured_summary.title,
            granularity=granularity,
            summary_data=structured_summary.model_dump()
        )
        db.add(db_summary)
        db.commit()
        db.refresh(db_summary)

        logger.info(f"Successfully generated and saved structured summary '{db_summary.title}' (ID: {db_summary.id}).")
        return db_summary
