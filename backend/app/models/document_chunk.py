from sqlalchemy import (
    Column,
    Integer,
    Text,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.sql import func

from app.core.database import Base, GUID
import uuid

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4
    )

    document_id = Column(
        GUID(),
        ForeignKey("extracted_documents.id"),
        nullable=False,
        index=True
    )

    chunk_index = Column(
        Integer,
        nullable=False
    )

    chunk_text = Column(
        Text,
        nullable=False
    )

    word_count = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )