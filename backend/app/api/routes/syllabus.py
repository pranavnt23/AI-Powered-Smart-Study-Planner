import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.upload import get_db
from app.models.extracted_document import ExtractedDocument
from app.models.syllabus_topic import SyllabusTopic
from app.services.syllabus_analyzer import SyllabusAnalyzerService
from app.services.topic_importance import TopicImportanceService

router = APIRouter(
    prefix="/syllabus",
    tags=["Syllabus"]
)


class TopicResponseSchema(BaseModel):
    id: int
    topic_name: str
    unit_title: Optional[str] = None
    importance_score: float
    estimated_hours: float
    difficulty_level: str
    priority_rank: int
    dependencies: List[str]
    priority: Optional[str] = None
    reasoning: Optional[str] = None


class SyllabusDetailsResponse(BaseModel):
    file_id: str
    syllabus_detected: bool
    estimated_difficulty: Optional[str] = None
    total_topics: Optional[int] = None
    topics: List[TopicResponseSchema]


@router.get("/file/{file_id}", response_model=SyllabusDetailsResponse)
def get_file_syllabus(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve structured syllabus details for the target document.
    """
    try:
        fid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_id format. Must be a valid UUID.")

    extracted_doc = db.query(ExtractedDocument).filter(ExtractedDocument.file_id == fid).first()
    if not extracted_doc:
        raise HTTPException(status_code=404, detail="Document metadata not found in database.")

    db_topics = (
        db.query(SyllabusTopic)
        .filter(SyllabusTopic.document_id == extracted_doc.id)
        .order_by(SyllabusTopic.priority_rank.asc())
        .all()
    )

    return {
        "file_id": str(fid),
        "syllabus_detected": extracted_doc.syllabus_detected,
        "estimated_difficulty": extracted_doc.estimated_difficulty,
        "total_topics": extracted_doc.total_topics,
        "topics": [
            {
                "id": t.id,
                "topic_name": t.topic_name,
                "unit_title": t.unit_title,
                "importance_score": t.importance_score,
                "estimated_hours": t.estimated_hours,
                "difficulty_level": t.difficulty_level,
                "priority_rank": t.priority_rank,
                "dependencies": t.dependencies.split(",") if t.dependencies else [],
                "priority": t.priority,
                "reasoning": t.reasoning
            }
            for t in db_topics
        ]
    }


@router.post("/file/{file_id}/analyze", response_model=SyllabusDetailsResponse)
def trigger_syllabus_analysis(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    Explicitly trigger structured AI syllabus analysis on the target document text.
    """
    try:
        # 1. Structure the initial syllabus topics
        SyllabusAnalyzerService.analyze_syllabus(db, file_id)

        # 2. Trigger Stage 12 calculations
        fid = uuid.UUID(file_id)
        extracted_doc = db.query(ExtractedDocument).filter(ExtractedDocument.file_id == fid).first()
        if not extracted_doc:
            raise HTTPException(status_code=404, detail="Document metadata not found.")

        TopicImportanceService.calculate_and_save_importance(db, extracted_doc.id)

        # 3. Reload topics from db to capture newly calculated columns
        db_topics = (
            db.query(SyllabusTopic)
            .filter(SyllabusTopic.document_id == extracted_doc.id)
            .order_by(SyllabusTopic.priority_rank.asc())
            .all()
        )

        return {
            "file_id": str(fid),
            "syllabus_detected": True,
            "estimated_difficulty": extracted_doc.estimated_difficulty,
            "total_topics": extracted_doc.total_topics,
            "topics": [
                {
                    "id": t.id,
                    "topic_name": t.topic_name,
                    "unit_title": t.unit_title,
                    "importance_score": t.importance_score,
                    "estimated_hours": t.estimated_hours,
                    "difficulty_level": t.difficulty_level,
                    "priority_rank": t.priority_rank,
                    "dependencies": t.dependencies.split(",") if t.dependencies else [],
                    "priority": t.priority,
                    "reasoning": t.reasoning
                }
                for t in db_topics
            ]
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Syllabus analysis failed: {str(err)}")
