from sqlalchemy import Column, String, Text, Integer, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base, GUID
import uuid


import datetime

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4
    )

    session_id = Column(
        GUID,
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False
    )  # 'user' or 'assistant'

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )

