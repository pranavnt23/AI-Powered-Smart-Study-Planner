from sqlalchemy import (
    Column,
    Integer,
    Float,
    TIMESTAMP,
    ForeignKey
)

from app.core.database import Base


class ProgressTracking(Base):
    __tablename__ = "progress_tracking"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    topic_id = Column(
        Integer,
        ForeignKey("syllabus_topics.id"),
        nullable=False
    )

    completion_percentage = Column(Float)

    confidence_level = Column(Float)

    last_reviewed = Column(TIMESTAMP(timezone=True))