import unittest
from unittest.mock import patch, MagicMock
from app.services.retrieval_service import RetrievalService


class TestMetadataFiltering(unittest.TestCase):

    @patch("app.services.retrieval_service.EmbeddingService")
    @patch("app.services.retrieval_service.VectorStore")
    def test_retrieve_context_user_only(self, mock_vector_store, mock_embedding_service):
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_vector_store.similarity_search.return_value = []

        filter_params = {"user_id": 1}
        RetrievalService.retrieve_context(
            query="test query",
            collection_name="test_collection",
            top_k=4,
            filter_params=filter_params
        )

        mock_vector_store.similarity_search.assert_called_once_with(
            collection_name="test_collection",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=15,
            filter_metadata={"user_id": "1"}
        )

    @patch("app.services.retrieval_service.EmbeddingService")
    @patch("app.services.retrieval_service.VectorStore")
    def test_retrieve_context_single_file(self, mock_vector_store, mock_embedding_service):
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_vector_store.similarity_search.return_value = []

        filter_params = {"user_id": 1, "file_id": "file-uuid-abc"}
        RetrievalService.retrieve_context(
            query="test query",
            collection_name="test_collection",
            top_k=4,
            filter_params=filter_params
        )

        mock_vector_store.similarity_search.assert_called_once_with(
            collection_name="test_collection",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=15,
            filter_metadata={
                "$and": [
                    {"user_id": "1"},
                    {"file_id": "file-uuid-abc"}
                ]
            }
        )

    @patch("app.services.retrieval_service.EmbeddingService")
    @patch("app.services.retrieval_service.VectorStore")
    def test_retrieve_context_multiple_files(self, mock_vector_store, mock_embedding_service):
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_vector_store.similarity_search.return_value = []

        filter_params = {"user_id": 1, "file_ids": ["file-1", "file-2", ""]}
        RetrievalService.retrieve_context(
            query="test query",
            collection_name="test_collection",
            top_k=4,
            filter_params=filter_params
        )

        mock_vector_store.similarity_search.assert_called_once_with(
            collection_name="test_collection",
            query_embedding=[0.1, 0.2, 0.3],
            top_k=15,
            filter_metadata={
                "$and": [
                    {"user_id": "1"},
                    {"file_id": {"$in": ["file-1", "file-2"]}}
                ]
            }
        )


if __name__ == "__main__":
    unittest.main()
