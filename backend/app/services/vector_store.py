import os
import logging
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)

# Define persistent storage location relative to this service file
CHROMA_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
)


class VectorStore:
    """
    Service interface for ChromaDB vector database interactions.
    Adheres strictly to the Single Responsibility Principle:
    handles CRUD operations and Approximate Nearest Neighbor similarity search,
    accepting pre-computed embedding vectors (lists of floats) from the caller.

    Similarity metric: Cosine Similarity (Cosine Distance space).
    """

    _client: ClientAPI | None = None

    @classmethod
    def _get_client(cls) -> ClientAPI:
        """
        Lazily instantiates the persistent ChromaDB client.
        """
        if cls._client is None:
            logger.info(f"Initializing persistent ChromaDB client at: {CHROMA_DATA_DIR}")
            cls._client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
        return cls._client

    @classmethod
    def get_or_create_collection(cls, collection_name: str) -> Collection:
        """
        Retrieves an existing ChromaDB collection or creates a new one.
        Sets the similarity search metric space to 'cosine' in HNSW configuration.

        Args:
            collection_name (str): The name of the collection.

        Returns:
            Collection: The ChromaDB collection object.
        """
        client = cls._get_client()
        # Enforce Cosine Similarity for the index space
        return client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    @classmethod
    def insert_vectors(
        cls,
        collection_name: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict]
    ) -> bool:
        """
        Inserts new vectors and documents into the specified collection.

        Args:
            collection_name (str): Target collection name.
            ids (list[str]): Unique string identifiers for each document chunk.
            embeddings (list[list[float]]): Array of 384-dimensional floating point vectors.
            documents (list[str]): The raw text content of the chunks.
            metadatas (list[dict]): Associated metadata attributes.

        Returns:
            bool: True if successful, raises exception otherwise.
        """
        try:
            collection = cls.get_or_create_collection(collection_name)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully inserted {len(ids)} vectors into collection '{collection_name}'")
            return True
        except Exception as error:
            logger.error(f"Error inserting vectors: {str(error)}")
            raise error

    @classmethod
    def update_vectors(
        cls,
        collection_name: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict]
    ) -> bool:
        """
        Updates existing vectors, documents, and metadatas by their ID.

        Args:
            collection_name (str): Target collection name.
            ids (list[str]): Unique string identifiers to update.
            embeddings (list[list[float]]): Updated vector arrays.
            documents (list[str]): Updated raw text contents.
            metadatas (list[dict]): Updated metadata parameters.

        Returns:
            bool: True if successful.
        """
        try:
            collection = cls.get_or_create_collection(collection_name)
            collection.update(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully updated {len(ids)} vectors in collection '{collection_name}'")
            return True
        except Exception as error:
            logger.error(f"Error updating vectors: {str(error)}")
            raise error

    @classmethod
    def delete_vectors(cls, collection_name: str, ids: list[str]) -> bool:
        """
        Deletes vector records by their ID strings from the specified collection.

        Args:
            collection_name (str): Target collection name.
            ids (list[str]): List of IDs to remove.

        Returns:
            bool: True if successful.
        """
        try:
            collection = cls.get_or_create_collection(collection_name)
            collection.delete(ids=ids)
            logger.info(f"Successfully deleted {len(ids)} vectors from collection '{collection_name}'")
            return True
        except Exception as error:
            logger.error(f"Error deleting vectors: {str(error)}")
            raise error

    @classmethod
    def similarity_search(
        cls,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict | None = None
    ) -> list[dict]:
        """
        Performs Approximate Nearest Neighbor (ANN) search using HNSW inside ChromaDB.

        Args:
            collection_name (str): Target collection name.
            query_embedding (list[float]): The vector representation of the search query.
            top_k (int): Number of top matches to retrieve. Defaults to 5.
            filter_metadata (dict): Metadata attributes for pre-filtering results.

        Returns:
            list[dict]: List of matches sorted by score, containing:
                        - id (str): Unique chunk ID.
                        - distance (float): Cosine distance (1 - CosineSimilarity).
                          Lower is closer/more similar.
                        - document (str): Text chunk content.
                        - metadata (dict): Associated metadata.
        """
        try:
            collection = cls.get_or_create_collection(collection_name)
            
            # Query ChromaDB collection
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            formatted_matches = []
            if result and result.get("ids") and len(result["ids"]) > 0:
                # Query was a list of one query_embedding, so we index the first output [0]
                ids = result["ids"][0]
                distances = result["distances"][0] if result.get("distances") else [0.0] * len(ids)
                documents = result["documents"][0] if result.get("documents") else [""] * len(ids)
                metadatas = result["metadatas"][0] if result.get("metadatas") else [{}] * len(ids)
                
                for idx in range(len(ids)):
                    formatted_matches.append({
                        "id": ids[idx],
                        "distance": distances[idx],
                        "document": documents[idx],
                        "metadata": metadatas[idx]
                    })
                    
            return formatted_matches
        except Exception as error:
            logger.error(f"Error performing similarity search: {str(error)}")
            raise error

    @classmethod
    def get_collections_info(cls) -> list[dict]:
        """
        Retrieves debugging information about all collections in ChromaDB.
        """
        try:
            client = cls._get_client()
            collections = client.list_collections()
            
            info = []
            for col in collections:
                count = col.count()
                sample = col.get(limit=10)
                
                info.append({
                    "name": col.name,
                    "total_vectors": count,
                    "metadata": col.metadata,
                    "sample_documents": sample.get("documents", []),
                    "sample_metadatas": sample.get("metadatas", []),
                    "sample_ids": sample.get("ids", [])
                })
            return info
        except Exception as error:
            logger.error(f"Error fetching collections info: {str(error)}")
            raise error
