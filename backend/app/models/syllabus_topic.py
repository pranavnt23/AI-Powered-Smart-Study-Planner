from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey

from app.core.database import Base, GUID


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        GUID(),
        ForeignKey("extracted_documents.id"),
        nullable=False
    )

    topic_name = Column(Text, nullable=False)

    importance_score = Column(Float)
    estimated_hours = Column(Float)
    difficulty_level = Column(String)
    priority_rank = Column(Integer)
    unit_title = Column(String(255), nullable=True)
    dependencies = Column(Text, nullable=True)
    priority = Column(String(50), nullable=True)
    reasoning = Column(Text, nullable=True)