from sqlalchemy import Column, Text, Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class ExtractedDocument(Base):

    __tablename__ = "extracted_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    file_id = Column(UUID(as_uuid=True), nullable=False)
    extracted_text = Column(Text, nullable=False)
    summary = Column(Text)
    syllabus_detected = Column(Boolean, default=False)
    estimated_difficulty = Column(String)
    total_topics = Column(Integer)
    processed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())