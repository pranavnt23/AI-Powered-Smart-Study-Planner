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
        result = DocumentProcessor.process_document(str(file_path))

        return {
            "status": True,
            "message": "File uploaded successfully",
            "data": result
        }

    except Exception as e:
        logger.error(str(e))
        return {
            "status": False,
            "message": str(e)
        }