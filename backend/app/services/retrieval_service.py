import logging
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service layer coordinating semantic retrieval.
    Adheres strictly to the Single Responsibility Principle:
    translates queries to embeddings, queries the vector database,
    and formats the retrieved snippets into context.

    Does NOT contain generation/LLM execution logic.
    """

    @classmethod
    def retrieve_context(
        cls,
        query: str,
        collection_name: str,
        top_k: int = 4,
        filter_metadata: dict | None = None
    ) -> dict:
        """
        Coordinates embedding generation and vector search to build a
        formatted context string.

        Args:
            query (str): The natural language search query.
            collection_name (str): The ChromaDB collection to search.
            top_k (int): Number of top matches to retrieve. Defaults to 4.
            filter_metadata (dict): Metadata key-value filters.

        Returns:
            dict: Containing:
                  - "context" (str): Multi-source formatted context string.
                  - "retrieved_chunks" (list[dict]): Raw list of matching documents.
        """
        if not query:
            return {"context": "", "retrieved_chunks": []}

        try:
            # 1. Generate query embedding vector using EmbeddingService
            logger.info(f"Generating query embedding for search: '{query}'")
            query_embedding = EmbeddingService.generate_embedding(query)

            # 2. Perform similarity search in VectorStore (ChromaDB)
            logger.info(f"Performing vector similarity search in collection '{collection_name}' (top_k={top_k})...")
            matches = VectorStore.similarity_search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filter_metadata
            )

            # 3. Construct formatted context block
            context_blocks = []
            for idx, match in enumerate(matches, start=1):
                doc_content = match["document"]
                meta = match["metadata"]
                
                # Fetch reference indicators from metadata
                file_name = meta.get("file_name", "Unknown Document")
                chunk_idx = meta.get("chunk_index", idx - 1)
                
                # Build context snippet with source headers
                block = (
                    f"--- [Source {idx}]: {file_name} (Chunk #{chunk_idx}) ---\n"
                    f"{doc_content.strip()}"
                )
                context_blocks.append(block)

            combined_context = "\n\n".join(context_blocks)
            logger.info(f"Successfully constructed context from {len(matches)} retrieved chunks.")

            return {
                "context": combined_context,
                "retrieved_chunks": matches
            }

        except Exception as error:
            logger.error(f"Error during retrieval orchestration: {str(error)}")
            raise error
