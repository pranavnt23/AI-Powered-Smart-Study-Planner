import unittest
from unittest.mock import patch, MagicMock

from app.services.rerank_service import RerankService
from app.services.retrieval_service import RetrievalService


class TestRerankService(unittest.TestCase):

    @patch("app.services.rerank_service.RerankService._get_model")
    def test_rerank_logic(self, mock_get_model):
        # Set up mock predict scores
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.12, 0.95, 0.45]
        mock_get_model.return_value = mock_model

        candidates = [
            {"id": "doc_1", "document": "First candidate text.", "metadata": {}},
            {"id": "doc_2", "document": "Second candidate text.", "metadata": {}},
            {"id": "doc_3", "document": "Third candidate text.", "metadata": {}}
        ]

        # Call re-ranker
        re_ranked = RerankService.rerank(query="how to optimize", candidates=candidates)

        # Expected output sorted descending by score:
        # Index 1 (doc_2) scored 0.95 -> Rank 1
        # Index 2 (doc_3) scored 0.45 -> Rank 2
        # Index 0 (doc_1) scored 0.12 -> Rank 3
        self.assertEqual(len(re_ranked), 3)
        self.assertEqual(re_ranked[0]["id"], "doc_2")
        self.assertEqual(re_ranked[1]["id"], "doc_3")
        self.assertEqual(re_ranked[2]["id"], "doc_1")
        self.assertEqual(re_ranked[0]["metadata"]["rerank_score"], 0.95)

    @patch("app.services.retrieval_service.EmbeddingService")
    @patch("app.services.retrieval_service.VectorStore")
    @patch("app.services.retrieval_service.RerankService")
    def test_retrieve_context_two_stage(self, mock_rerank_service, mock_vector_store, mock_embedding_service):
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2]
        
        # 1st stage search results
        mock_vector_store.similarity_search.return_value = [
            {"id": "c1", "document": "sem doc 1", "metadata": {"file_name": "x.pdf"}},
            {"id": "c2", "document": "sem doc 2", "metadata": {"file_name": "x.pdf"}},
        ]

        # Reranker re-scores and reorders them (reverses order: c2 first)
        mock_rerank_service.rerank.return_value = [
            {"id": "c2", "document": "sem doc 2", "metadata": {"file_name": "x.pdf"}},
            {"id": "c1", "document": "sem doc 1", "metadata": {"file_name": "x.pdf"}},
        ]

        retrieval = RetrievalService.retrieve_context(
            query="test query",
            collection_name="test_collection",
            top_k=1,  # Select top 1 final matches
            filter_params={"user_id": 1}
        )

        # The retrieval context should only contain c2 since top_k=1 and c2 was ranked 1st
        self.assertEqual(len(retrieval["retrieved_chunks"]), 1)
        self.assertEqual(retrieval["retrieved_chunks"][0]["id"], "c2")


if __name__ == "__main__":
    unittest.main()
