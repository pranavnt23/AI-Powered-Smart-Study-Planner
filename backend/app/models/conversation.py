from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base, GUID
import uuid
import datetime


class Conversation(Base):
    __tablename__ = "conversations"

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

    created_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )

    # Relationship back to ChatMessages (cascades delete)
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
