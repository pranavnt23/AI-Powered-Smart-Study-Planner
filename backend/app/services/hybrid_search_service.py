import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Service responsible for lexical retrieval using BM25 and merging multiple
    retrieval sources (vector + lexical) using Reciprocal Rank Fusion (RRF).
    """

    @classmethod
    def score_lexical_bm25(
        cls,
        query: str,
        db_tuples: List[Any],  # List of tuples (DocumentChunk, file_name)
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Executes BM25 scoring on database chunks.

        Args:
            query (str): Search query string.
            db_tuples (list): List of tuples containing (DocumentChunk, file_name).
            top_k (int): Number of top matches to return.

        Returns:
            list[dict]: List of matching chunk dictionaries formatted like ChromaDB outputs.
        """
        if not isinstance(db_tuples, list) or len(db_tuples) == 0 or not query.strip():
            return []

        try:
            # Tokenize query (lowercase word splitting)
            tokenized_query = query.lower().split()

            # Tokenize documents
            tokenized_corpus = []
            for chunk, _ in db_tuples:
                doc_text = chunk.chunk_text or ""
                tokenized_corpus.append(doc_text.lower().split())

            # Initialize BM25Okapi engine
            bm25 = BM25Okapi(tokenized_corpus)

            # Get scores
            scores = bm25.get_scores(tokenized_query)

            # Zip scores with candidates
            scored_candidates = []
            for idx, (chunk, file_name) in enumerate(db_tuples):
                # Ensure document actually contains at least one query token (lexical overlap check)
                doc_tokens = tokenized_corpus[idx]
                if not any(token in doc_tokens for token in tokenized_query):
                    continue
                score = float(scores[idx])
                scored_candidates.append((score, chunk, file_name))

            # Sort descending by score
            scored_candidates.sort(key=lambda x: x[0], reverse=True)

            # Format top candidates
            formatted_matches = []
            for score, chunk, file_name in scored_candidates[:top_k]:
                formatted_matches.append({
                    "id": str(chunk.id),
                    # Store negated score as distance so sorting ascending is uniform
                    "distance": -score,
                    "document": chunk.chunk_text,
                    "metadata": {
                        "file_name": file_name,
                        "file_id": str(chunk.document_id),
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number
                    }
                })

            logger.info(f"BM25 scored {len(db_tuples)} chunks; matched {len(formatted_matches)} above threshold.")
            return formatted_matches

        except Exception as error:
            logger.error(f"Error during lexical BM25 scoring: {str(error)}", exc_info=True)
            return []

    @classmethod
    def reciprocal_rank_fusion(
        cls,
        vector_results: List[Dict[str, Any]],
        lexical_results: List[Dict[str, Any]],
        k: int = 60,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Merges results using Reciprocal Rank Fusion (RRF) on rankings.

        Args:
            vector_results (list[dict]): Matches from the semantic search path.
            lexical_results (list[dict]): Matches from the lexical search path.
            k (int): Smoothing factor constant (default 60).
            top_k (int): Number of final merged matches to return.

        Returns:
            list[dict]: Merged and sorted list of top match dictionaries.
        """
        rrf_scores = {}
        candidate_details = {}

        # 1. Process Vector Results
        for rank, match in enumerate(vector_results, start=1):
            chunk_id = match["id"]
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
            candidate_details[chunk_id] = match

        # 2. Process Lexical Results
        for rank, match in enumerate(lexical_results, start=1):
            chunk_id = match["id"]
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
            # Store detail if not already present (prefer vector detail format but keep lexical fallback)
            if chunk_id not in candidate_details:
                candidate_details[chunk_id] = match

        # 3. Sort candidates by final score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        # 4. Compile final list
        fused_results = []
        for cid in sorted_ids[:top_k]:
            match = candidate_details[cid].copy()
            # Store fusion score and source rankings in metadata for verification/auditing
            match["metadata"] = match.get("metadata", {}).copy()
            match["metadata"]["rrf_score"] = rrf_scores[cid]
            fused_results.append(match)

        logger.info(f"RRF combined {len(vector_results)} vector & {len(lexical_results)} lexical candidates -> {len(fused_results)} final hits.")
        return fused_results
