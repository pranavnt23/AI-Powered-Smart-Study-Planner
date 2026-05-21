from sqlalchemy import Column, Integer, String, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class UploadedFile(Base):

    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    storage_path = Column(Text, nullable=False)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processing_status = Column(String, default="pending")