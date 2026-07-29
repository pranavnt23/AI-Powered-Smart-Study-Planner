import logging
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RerankService:
    """
    Service responsible for neural re-ranking using a local Cross-Encoder.
    Improves retrieval precision by evaluating exact relational alignment
    between the search query and the text chunks.
    """

    _model: CrossEncoder | None = None

    @classmethod
    def _get_model(cls) -> CrossEncoder:
        """
        Lazily loads and caches the Cross-Encoder model.
        On first invocation, sentence-transformers downloads the model
        and caches it in the user's home directory.
        """
        if cls._model is None:
            logger.info("Initializing Cross-Encoder reranker model (cross-encoder/ms-marco-MiniLM-L-6-v2)...")
            cls._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return cls._model

    @classmethod
    def rerank(
        cls,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Re-scores and re-ranks a candidate list of chunks using the Cross-Encoder.

        Args:
            query (str): The natural language query.
            candidates (list[dict]): A list of dictionaries representing first-stage chunks.

        Returns:
            list[dict]: Candidates sorted descending by their Cross-Encoder relevance score.
        """
        if not candidates or not query.strip():
            return candidates

        try:
            # 1. Lazily load model
            model = cls._get_model()

            # 2. Build input pairs: (query, document_text)
            pairs = []
            for item in candidates:
                doc_text = item.get("document", "")
                pairs.append((query, doc_text))

            # 3. Compute relevance scores
            logger.info(f"Neural Re-ranking: scoring {len(candidates)} candidates...")
            scores = model.predict(pairs)

            # 4. Map scores back to candidate dictionaries
            scored_candidates = []
            for idx, item in enumerate(candidates):
                score = float(scores[idx])
                # Copy document structure and update relevance score in metadata
                updated_item = item.copy()
                updated_item["metadata"] = updated_item.get("metadata", {}).copy()
                updated_item["metadata"]["rerank_score"] = score
                # Store normalized score in distance key (negated so sorting ascending is uniform)
                updated_item["distance"] = -score
                scored_candidates.append((score, updated_item))

            # 5. Sort candidates descending by Cross-Encoder score
            scored_candidates.sort(key=lambda x: x[0], reverse=True)

            # Extract the sorted matches
            fused_matches = [item for _, item in scored_candidates]
            logger.info("Neural Re-ranking complete.")
            return fused_matches

        except Exception as error:
            logger.error(f"Error during neural re-ranking: {str(error)}")
            return candidates
