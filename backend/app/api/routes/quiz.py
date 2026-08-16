import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.upload import get_db
from app.models.quiz import Quiz
from app.schemas.quiz_schema import (
    QuizCreateRequestSchema,
    QuizResponseSchema
)
from app.services.quiz_generator import QuizGenerationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.post("/generate", response_model=QuizResponseSchema, status_code=status.HTTP_201_CREATED)
def generate_new_quiz(
    request: QuizCreateRequestSchema,
    db: Session = Depends(get_db)
):
    """
    Generates a new educational quiz based on a specific study document context.
    Runs structured output parsing and validation, and persists the quiz in PostgreSQL.
    """
    try:
        db_quiz = QuizGenerationService.generate_quiz(
            db=db,
            user_id=request.user_id,
            file_id=request.file_id,
            topic=request.topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions
        )
        return db_quiz
    except ValueError as val_err:
        logger.warning(f"Bad Request during quiz generation: {str(val_err)}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        logger.error(f"Failed to generate quiz: {str(err)}")
        raise HTTPException(
            status_code=500,
            detail=f"Quiz generation failed: {str(err)}"
        )


@router.get("/{quiz_id}", response_model=QuizResponseSchema)
def get_quiz_by_id(
    quiz_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetches a previously generated quiz and its matching questions by unique quiz ID.
    """
    try:
        uid = uuid.UUID(quiz_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid quiz UUID format."
        )

    db_quiz = db.query(Quiz).filter(Quiz.id == uid).first()
    if not db_quiz:
        raise HTTPException(
            status_code=404,
            detail="Requested quiz could not be found."
        )
    return db_quiz


@router.get("/file/{file_id}", response_model=List[QuizResponseSchema])
def get_quizzes_by_file_id(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all quizzes generated for a specific study document.
    """
    try:
        fid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file UUID format."
        )

    quizzes = db.query(Quiz).filter(Quiz.file_id == fid).order_by(Quiz.created_at.desc()).all()
    return quizzes
