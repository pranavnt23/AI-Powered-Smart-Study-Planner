from sqlalchemy import Column, Integer, Float, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    sleep_hours = Column(Float)
    break_duration = Column(Integer)
    revision_time = Column(Integer)
    preferred_study_hours = Column(Integer)
    learning_speed = Column(String)
    daily_focus_capacity = Column(Integer)

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )