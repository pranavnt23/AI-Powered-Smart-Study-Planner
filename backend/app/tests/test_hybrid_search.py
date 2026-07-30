import unittest
from unittest.mock import patch, MagicMock

from app.services.hybrid_search_service import HybridSearchService
from app.services.retrieval_service import RetrievalService


class DummyChunk:
    def __init__(self, id, document_id, chunk_index, chunk_text, page_number=1):
        self.id = id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.chunk_text = chunk_text
        self.page_number = page_number


class TestHybridSearch(unittest.TestCase):

    def test_score_lexical_bm25(self):
        # Set up dummy document chunks
        chunk1 = DummyChunk("c1", "doc1", 0, "Stochastic Gradient Descent is an optimizer.")
        chunk2 = DummyChunk("c2", "doc1", 1, "Backpropagation calculates errors.")
        chunk3 = DummyChunk("c3", "doc2", 0, "Optimizers update network weights.")

        db_tuples = [
            (chunk1, "nn_notes.pdf"),
            (chunk2, "nn_notes.pdf"),
            (chunk3, "optim_notes.pdf")
        ]

        # Query matches "Gradient Descent"
        results = HybridSearchService.score_lexical_bm25(
            query="Gradient Descent",
            db_tuples=db_tuples,
            top_k=2
        )

        self.assertEqual(len(results), 1)  # Only chunk1 should match terms
        self.assertEqual(results[0]["id"], "c1")
        self.assertEqual(results[0]["metadata"]["file_name"], "nn_notes.pdf")

    def test_reciprocal_rank_fusion(self):
        vector_results = [
            {"id": "doc_a", "document": "vector doc a", "metadata": {}},
            {"id": "doc_b", "document": "vector doc b", "metadata": {}},
            {"id": "doc_c", "document": "vector doc c", "metadata": {}}
        ]

        lexical_results = [
            {"id": "doc_b", "document": "lexical doc b", "metadata": {}},
            {"id": "doc_a", "document": "lexical doc a", "metadata": {}},
            {"id": "doc_d", "document": "lexical doc d", "metadata": {}}
        ]

        fused = HybridSearchService.reciprocal_rank_fusion(
            vector_results=vector_results,
            lexical_results=lexical_results,
            k=60,
            top_k=3
        )

        # doc_a ranks 1st in vector and 2nd in lexical -> RRF score: 1/(60+1) + 1/(60+2)
        # doc_b ranks 2nd in vector and 1st in lexical -> RRF score: 1/(60+2) + 1/(60+1)
        # Therefore, doc_a and doc_b should be the top-ranked candidates
        self.assertEqual(len(fused), 3)
        top_ids = [m["id"] for m in fused]
        self.assertIn("doc_a", top_ids[:2])
        self.assertIn("doc_b", top_ids[:2])
        self.assertIn("rrf_score", fused[0]["metadata"])

    @patch("app.services.retrieval_service.EmbeddingService")
    @patch("app.services.retrieval_service.VectorStore")
    def test_retrieve_context_hybrid(self, mock_vector_store, mock_embedding_service):
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2]
        
        # ChromaDB semantic search matches
        mock_vector_store.similarity_search.return_value = [
            {"id": "c1", "document": "semantic matches text", "metadata": {"file_name": "src.pdf", "chunk_index": 0}}
        ]

        # Set up mock database session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        chunk = DummyChunk("c2", "doc2", 0, "lexical matches text")
        mock_query.all.return_value = [
            (chunk, "lexical_src.pdf")
        ]

        retrieval = RetrievalService.retrieve_context(
            query="lexical matches",
            collection_name="test_collection",
            top_k=2,
            filter_params={"user_id": 1},
            db=mock_db
        )

        self.assertEqual(len(retrieval["retrieved_chunks"]), 2)
        retrieved_ids = [m["id"] for m in retrieval["retrieved_chunks"]]
        self.assertIn("c1", retrieved_ids)
        self.assertIn("c2", retrieved_ids)


if __name__ == "__main__":
    unittest.main()
