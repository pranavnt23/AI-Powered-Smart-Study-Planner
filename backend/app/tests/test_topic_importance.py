import unittest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.extracted_document import ExtractedDocument
from app.models.document_chunk import DocumentChunk
from app.models.syllabus_topic import SyllabusTopic
from app.services.topic_importance import TopicImportanceService


class TestTopicImportance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.query(SyllabusTopic).delete()
        self.db.query(DocumentChunk).delete()
        self.db.query(ExtractedDocument).delete()
        self.db.commit()
        self.db.close()

    def test_calculate_and_save_importance_pipeline(self):
        # 1. Setup mock document metadata
        doc_id = uuid.uuid4()
        file_id = uuid.uuid4()
        doc = ExtractedDocument(
            id=doc_id,
            file_id=file_id,
            extracted_text="Some extracted syllabus text",
            syllabus_detected=True,
            total_topics=4
        )
        self.db.add(doc)

        # 2. Insert mock document chunks
        # SQL will appear 3 times, Normalization will appear 2 times, ACID 0 times, DBMS History 0 times
        chunks = [
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc_id,
                chunk_index=0,
                chunk_text="We will study Normalization and write SQL queries. Database Normalization theory."
            ),
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc_id,
                chunk_index=1,
                chunk_text="Advanced SQL queries, subqueries, and database index optimization with SQL commands."
            )
        ]
        self.db.add_all(chunks)

        # 3. Insert mock syllabus topics
        t_a = SyllabusTopic(
            document_id=doc_id,
            topic_name="Normalization",
            unit_title="Unit 3",
            importance_score=9.5,
            estimated_hours=3.5,
            difficulty_level="hard",
            priority_rank=3,
            dependencies="SQL"
        )
        t_b = SyllabusTopic(
            document_id=doc_id,
            topic_name="SQL",
            unit_title="Unit 2",
            importance_score=8.0,
            estimated_hours=2.0,
            difficulty_level="medium",
            priority_rank=2,
            dependencies=""
        )
        t_c = SyllabusTopic(
            document_id=doc_id,
            topic_name="ACID",
            unit_title="Unit 3",
            importance_score=8.5,
            estimated_hours=2.5,
            difficulty_level="hard",
            priority_rank=4,
            dependencies="SQL"
        )
        t_d = SyllabusTopic(
            document_id=doc_id,
            topic_name="DBMS History",
            unit_title="Unit 1",
            importance_score=2.0,
            estimated_hours=1.0,
            difficulty_level="easy",
            priority_rank=1,
            dependencies=""
        )
        self.db.add_all([t_a, t_b, t_c, t_d])
        self.db.commit()

        # 4. Trigger calculations
        results = TopicImportanceService.calculate_and_save_importance(self.db, doc_id)

        # 5. Verifications
        self.assertEqual(len(results), 4)

        db_topics = self.db.query(SyllabusTopic).filter(SyllabusTopic.document_id == doc_id).all()
        self.assertEqual(len(db_topics), 4)

        topic_map = {t.topic_name: t for t in db_topics}

        # Check model fields correctness
        for name, t in topic_map.items():
            self.assertIsNotNone(t.importance_score)
            self.assertTrue(0.0 <= t.importance_score <= 100.0)
            self.assertIn(t.priority, ["high", "medium", "low"])
            self.assertTrue(len(t.reasoning) > 10)

        # Verify relative ranking distribution: 25% high (1), 25% low (1), 50% medium (2)
        priorities = [t.priority for t in db_topics]
        self.assertEqual(priorities.count("high"), 1)
        self.assertEqual(priorities.count("low"), 1)
        self.assertEqual(priorities.count("medium"), 2)

        # Verify DBMS History maps to low priority
        self.assertEqual(topic_map["DBMS History"].priority, "low")
