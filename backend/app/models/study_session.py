from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    String,
    Date,
    Time,
    ForeignKey
)

from app.core.database import Base, GUID


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)

    study_plan_id = Column(
        GUID(),
        ForeignKey("study_plans.id"),
        nullable=False
    )

    topic_id = Column(
        Integer,
        ForeignKey("syllabus_topics.id"),
        nullable=False
    )

    study_date = Column(Date)

    start_time = Column(Time)

    end_time = Column(Time)

    session_type = Column(String)

    completion_status = Column(Boolean)