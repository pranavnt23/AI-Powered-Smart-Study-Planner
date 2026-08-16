import logging
from sqlalchemy.orm import Session
from app.models.document_chunk import DocumentChunk
from app.models.extracted_document import ExtractedDocument
from app.models.uploaded_file import UploadedFile
from app.services.hybrid_search_service import HybridSearchService
from app.services.rerank_service import RerankService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Service layer coordinating semantic, lexical, and neural re-ranking retrieval.
    Adheres strictly to the Clean Architecture:
    translates queries to embeddings, queries the vector database,
    triggers local BM25 indexing, re-scores candidates with a local Cross-Encoder,
    and formats the fused snippets into context.

    Does NOT contain generation/LLM execution logic.
    """

    @classmethod
    def retrieve_context(
        cls,
        query: str,
        collection_name: str,
        top_k: int = 4,
        filter_params: dict | None = None,
        db: Session | None = None
    ) -> dict:
        """
        Coordinates embedding generation, parallel vector/lexical search,
        neural re-ranking, and final Top-N selection to build context.

        Args:
            query (str): The natural language search query.
            collection_name (str): The ChromaDB collection to search.
            top_k (int): Number of top matches to retrieve. Defaults to 4.
            filter_params (dict): Dynamic user and file filter parameters.
            db (Session): Optional database session for lexical candidate matching.

        Returns:
            dict: Containing:
                  - "context" (str): Multi-source formatted context string.
                  - "retrieved_chunks" (list[dict]): Fused list of matching documents.
        """
        if not query:
            return {"context": "", "retrieved_chunks": []}

        # First stage retrieval size (cast a larger net to ensure high recall)
        first_stage_k = 15

        # Build filter_metadata dictionary from filter_params for ChromaDB
        filter_metadata = None
        user_id = None
        file_id = None
        file_ids = None

        if filter_params:
            user_id = filter_params.get("user_id")
            file_id = filter_params.get("file_id")
            file_ids = filter_params.get("file_ids")

            and_filters = []
            if user_id is not None:
                and_filters.append({"user_id": str(user_id)})

            if file_id is not None:
                and_filters.append({"file_id": str(file_id)})
            elif file_ids is not None:
                clean_fids = [str(fid) for fid in file_ids if fid]
                if clean_fids:
                    and_filters.append({"file_id": {"$in": clean_fids}})

            if len(and_filters) == 1:
                filter_metadata = and_filters[0]
            elif len(and_filters) > 1:
                filter_metadata = {"$and": and_filters}

        try:
            # 1. Generate query embedding vector using EmbeddingService
            logger.info(f"Generating query embedding for search: '{query}'")
            query_embedding = EmbeddingService.generate_embedding(query)

            # 2. Perform similarity search in VectorStore (ChromaDB) requesting first_stage_k
            logger.info(f"Performing vector similarity search in collection '{collection_name}' (top_k={first_stage_k})...")
            vector_matches = VectorStore.similarity_search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                top_k=first_stage_k,
                filter_metadata=filter_metadata
            )

            # 3. Perform lexical search and run Reciprocal Rank Fusion (RRF) if DB session is supplied
            matches = vector_matches
            if db is not None:
                try:
                    logger.info("Lexical path active: querying database candidates...")
                    query_db = (
                        db.query(DocumentChunk, UploadedFile.file_name)
                        .join(ExtractedDocument, DocumentChunk.document_id == ExtractedDocument.id)
                        .join(UploadedFile, ExtractedDocument.file_id == UploadedFile.id)
                    )

                    sql_filters = []
                    if user_id is not None:
                        sql_filters.append(UploadedFile.user_id == int(user_id))

                    if file_id is not None:
                        sql_filters.append(UploadedFile.id == str(file_id))
                    elif file_ids is not None:
                        clean_fids = [str(fid) for fid in file_ids if fid]
                        if clean_fids:
                            sql_filters.append(UploadedFile.id.in_(clean_fids))

                    if sql_filters:
                        query_db = query_db.filter(*sql_filters)

                    db_tuples = query_db.all()

                    # Compute lexical matches using BM25Okapi
                    lexical_matches = HybridSearchService.score_lexical_bm25(
                        query=query,
                        db_tuples=db_tuples,
                        top_k=first_stage_k
                    )

                    # Fuse semantic and lexical lists using RRF
                    matches = HybridSearchService.reciprocal_rank_fusion(
                        vector_results=vector_matches,
                        lexical_results=lexical_matches,
                        top_k=first_stage_k
                    )
                except Exception as db_error:
                    logger.error(f"Failed to query database for lexical matches: {str(db_error)}")
                    # Fallback to vector search results only
                    matches = vector_matches

            # 4. Neural Re-ranking Stage (Cross-Encoder)
            if matches:
                try:
                    logger.info(f"Re-ranking {len(matches)} hybrid candidates using Cross-Encoder...")
                    matches = RerankService.rerank(query=query, candidates=matches)
                except Exception as rerank_err:
                    logger.error(f"Neural re-ranking pipeline failed: {str(rerank_err)}")
                    # Fallback to hybrid matches without reranking

            # Select Top-N results
            matches = matches[:top_k]

            # 5. Construct formatted context block
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

