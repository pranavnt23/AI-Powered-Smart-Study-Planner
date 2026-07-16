from fastapi import APIRouter
from app.services.vector_store import VectorStore

router = APIRouter(
    prefix="/debug",
    tags=["Debug"]
)


@router.get("/chroma")
def get_chroma_debug_info():
    """
    Debug endpoint to inspect the contents of ChromaDB collections,
    counts, and sample documents without direct database file access.
    """
    try:
        collections_info = VectorStore.get_collections_info()
        return {
            "status": True,
            "collections": collections_info
        }
    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }
