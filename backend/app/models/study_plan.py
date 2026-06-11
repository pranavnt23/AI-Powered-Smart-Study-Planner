from sqlalchemy import Column, Integer, Boolean, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base, GUID


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(
        GUID(),
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    document_id = Column(
        GUID(),
        ForeignKey("extracted_documents.id"),
        nullable=False
    )

    total_days = Column(Integer, nullable=False)

    generated_by_ai = Column(Boolean)

    status = Column(String)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )