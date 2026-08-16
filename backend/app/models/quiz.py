from sqlalchemy import Column, String, Text, Integer, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base, GUID
import uuid
import datetime


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        Integer,
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    file_id = Column(
        GUID,
        nullable=True,
        index=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )

    # Relationship to QuizQuestions (cascades delete)
    questions = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan"
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4
    )

    quiz_id = Column(
        GUID,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    question_text = Column(
        Text,
        nullable=False
    )

    question_type = Column(
        String(50),
        nullable=False
    )  # 'mcq', 'true_false', 'scenario'

    options = Column(
        JSON,
        nullable=False
    )  # JSON list of strings

    correct_answer_idx = Column(
        Integer,
        nullable=False
    )

    difficulty = Column(
        String(50),
        nullable=False
    )  # 'easy', 'medium', 'hard'

    explanation = Column(
        Text,
        nullable=False
    )

    source_citation = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )

    # Reference back to Quiz
    quiz = relationship(
        "Quiz",
        back_populates="questions"
    )
