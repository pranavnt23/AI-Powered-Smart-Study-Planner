import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.upload import get_db
from app.models.summary import Summary
from app.schemas.summary_schema import (
    SummaryCreateRequestSchema,
    SummaryResponseSchema
)
from app.services.summarizer import SummarizationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/summary", tags=["Summary"])


@router.post("/generate", response_model=SummaryResponseSchema, status_code=status.HTTP_201_CREATED)
def generate_new_summary(
    request: SummaryCreateRequestSchema,
    db: Session = Depends(get_db)
):
    """
    Generates a structured, source-grounded summary of an uploaded file.
    Runs Map-Reduce loops for long files and validates outputs against Pydantic models.
    """
    try:
        db_summary = SummarizationService.generate_summary(
            db=db,
            user_id=request.user_id,
            file_id=request.file_id,
            granularity=request.granularity
        )
        return db_summary
    except ValueError as val_err:
        logger.warning(f"Bad Request during summary generation: {str(val_err)}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        logger.error(f"Failed to generate summary: {str(err)}")
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(err)}"
        )


@router.get("/file/{file_id}", response_model=SummaryResponseSchema)
def get_summary_by_file_id(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the most recently generated structured summary for a specific study document.
    """
    try:
        fid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file UUID format."
        )

    db_summary = (
        db.query(Summary)
        .filter(Summary.file_id == fid)
        .order_by(Summary.created_at.desc())
        .first()
    )
    if not db_summary:
        raise HTTPException(
            status_code=404,
            detail="No summaries found for the requested file."
        )
    return db_summary


@router.get("/{summary_id}", response_model=SummaryResponseSchema)
def get_summary_by_id(
    summary_id: str,
    db: Session = Depends(get_db)
):
    """
    Loads a previously generated structured summary guide by its unique summary ID.
    """
    try:
        sid = uuid.UUID(summary_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid summary UUID format."
        )

    db_summary = db.query(Summary).filter(Summary.id == sid).first()
    if not db_summary:
        raise HTTPException(
            status_code=404,
            detail="Requested summary guide could not be found."
        )
    return db_summary
