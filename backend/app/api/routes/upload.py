from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from pathlib import Path
import shutil
import uuid
import logging

from app.core.database import SessionLocal
from app.services.document_processor import DocumentProcessor
from app.schemas.upload_schema import UploadResponseSchema
from app.models.uploaded_file import UploadedFile
from app.models.extracted_document import ExtractedDocument
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore


router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

logger = logging.getLogger(__name__)
UPLOAD_DIR = "app/uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=UploadResponseSchema
)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    try:
        extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = Path(UPLOAD_DIR) / unique_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_file = UploadedFile(
            user_id=1,
            file_name=file.filename,
            file_type=extension,
            file_size=file.size,
            storage_path=str(file_path),
            processing_status="uploaded"
        )

        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        result = DocumentProcessor.process_document(
            str(file_path)
        )

        if result["status"]:

            extracted_document = ExtractedDocument(
                file_id=uploaded_file.id,
                extracted_text=result["data"]["clean_text"]
            )

            db.add(extracted_document)
            db.commit()
            db.refresh(extracted_document)

            chunk_records = []
            for chunk in result["data"]["chunks"]:
                chunk_record = DocumentChunk(
                    document_id=extracted_document.id,
                    chunk_index=chunk["chunk_index"],
                    chunk_text=chunk["chunk_text"],
                    word_count=chunk["word_count"],
                    page_number=chunk.get("page_number", 1)
                )
                db.add(chunk_record)
                chunk_records.append(chunk_record)

            db.commit()

            # End-to-end RAG Integration: Generate embeddings and store in ChromaDB
            try:
                texts = [c.chunk_text for c in chunk_records]
                if texts:
                    logger.info(f"Generating embeddings for {len(texts)} chunks of file: {uploaded_file.file_name}")
                    embeddings = EmbeddingService.generate_embeddings_batch(texts)

                    chroma_ids = []
                    chroma_embeddings = []
                    chroma_documents = []
                    chroma_metadatas = []

                    for idx, chunk_rec in enumerate(chunk_records):
                        chroma_ids.append(f"chunk_{chunk_rec.id}")
                        chroma_embeddings.append(embeddings[idx])
                        chroma_documents.append(chunk_rec.chunk_text)
                        chroma_metadatas.append({
                            "file_id": str(uploaded_file.id),
                            "user_id": str(uploaded_file.user_id),
                            "file_name": uploaded_file.file_name,
                            "chunk_index": chunk_rec.chunk_index
                        })

                    logger.info(f"Storing vectors in ChromaDB collection 'study_materials' for: {uploaded_file.file_name}")
                    VectorStore.insert_vectors(
                        collection_name="study_materials",
                        ids=chroma_ids,
                        embeddings=chroma_embeddings,
                        documents=chroma_documents,
                        metadatas=chroma_metadatas
                    )

                uploaded_file.processing_status = "processed"
                db.commit()
            except Exception as embed_err:
                logger.error(f"Failed to generate/store embeddings for file {uploaded_file.file_name}: {str(embed_err)}")
                uploaded_file.processing_status = "failed"
                db.commit()
                raise embed_err

        # Unwrap processor nested result and inject key properties for frontend compatibility
        processed_data = result["data"] if isinstance(result, dict) and "data" in result else result
        if isinstance(processed_data, dict):
            processed_data["content"] = processed_data.get("clean_text", "")
            processed_data["text"] = processed_data.get("clean_text", "")

        return {
            "status": True,
            "message": "File uploaded successfully",
            "data": processed_data
        }

    except Exception as e:
        logger.error(str(e))
        return {
            "status": False,
            "message": str(e)
        }