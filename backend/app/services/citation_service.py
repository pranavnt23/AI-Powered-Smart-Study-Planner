import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class CitationService:
    """
    Service responsible for parsing, validating, and formatting citations
    from LLM generated responses against retrieved context chunks.
    """

    @classmethod
    def parse_citations(
        cls,
        answer_text: str,
        context_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parses inline document citation tags (e.g., [doc_1], [doc_2]) from LLM answer.
        Validates references against provided context chunks.
        Maps valid citation tags to sequential integers [1], [2], etc.
        Removes invalid or hallucinated citations.

        Args:
            answer_text (str): Raw generated answer text from the LLM.
            context_chunks (list[dict]): List of retrieved chunks actually included in the prompt.

        Returns:
            Tuple[str, list[dict]]: A tuple containing the updated answer text and the citations metadata list.
        """
        if not answer_text:
            return "", []

        # Find all citation tags in the answer text using regex
        # Matches formats like [doc_1], [doc_12], etc.
        tag_pattern = re.compile(r"\[doc_(\d+)\]")
        matches = tag_pattern.findall(answer_text)

        # 1. Determine valid document indices cited in order of appearance
        used_doc_indices = []
        num_chunks = len(context_chunks)

        for match in matches:
            try:
                doc_idx = int(match)
                # Verify document index is valid (1-based indexing matching PromptBuilder doc_{idx})
                if 1 <= doc_idx <= num_chunks:
                    if doc_idx not in used_doc_indices:
                        used_doc_indices.append(doc_idx)
                else:
                    logger.warning(f"LLM cited a document index out of range: [doc_{doc_idx}] (Total chunks: {num_chunks})")
            except ValueError:
                continue

        # 2. Build mapping from document index to user-friendly sequential citation index
        # Example: if doc_2 is cited first, it maps to citation ID 1.
        doc_idx_to_seq = {doc_idx: seq_id for seq_id, doc_idx in enumerate(used_doc_indices, start=1)}

        # 3. Replace [doc_x] tags with [seq_id] or strip them if invalid
        def replacement_handler(match_obj):
            try:
                doc_idx = int(match_obj.group(1))
                if doc_idx in doc_idx_to_seq:
                    seq_id = doc_idx_to_seq[doc_idx]
                    return f"[{seq_id}]"
                else:
                    # Strip out invalid / out-of-bounds citations
                    return ""
            except ValueError:
                return ""

        formatted_answer = tag_pattern.sub(replacement_handler, answer_text)

        # 4. Construct structured citation metadata objects
        citations_list = []
        for doc_idx in used_doc_indices:
            chunk = context_chunks[doc_idx - 1]
            meta = chunk.get("metadata", {})

            citations_list.append({
                "doc_id": f"doc_{doc_idx}",
                "citation_id": doc_idx_to_seq[doc_idx],
                "file_id": meta.get("file_id", "unknown"),
                "file_name": meta.get("file_name", "Unknown Document"),
                "page_number": meta.get("page_number", 1)
            })


        logger.info(f"Parsed {len(citations_list)} valid citations from LLM answer.")
        return formatted_answer, citations_list
