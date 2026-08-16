from sqlalchemy import Column, String, Integer, TIMESTAMP, JSON
from sqlalchemy.sql import func
from app.core.database import Base, GUID
import uuid
import datetime


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        Integer,
        nullable=False
    )

    file_id = Column(
        GUID,
        nullable=False,
        index=True
    )

    title = Column(
        String(255),
        nullable=False
    )

    granularity = Column(
        String(50),
        nullable=False
    )  # 'bullet', 'detailed'

    summary_data = Column(
        JSON,
        nullable=False
    )  # Structured JSON matching Pydantic SummarySchema

    created_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )
