import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.extracted_document import ExtractedDocument
from app.models.syllabus_topic import SyllabusTopic
from app.services.intent_router import IntentRouterService
from app.services.syllabus_analyzer import SyllabusAnalyzerService, SyllabusAnalysisSchema


class TestSyllabusAnalyzer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.query(SyllabusTopic).delete()
        self.db.query(ExtractedDocument).delete()
        self.db.commit()
        self.db.close()

    def test_intent_detection(self):
        # Assert syllabus intent detection keywords
        self.assertEqual(IntentRouterService.detect_intent("analyze the syllabus"), "syllabus")
        self.assertEqual(IntentRouterService.detect_intent("generate a course map for physics"), "syllabus")
        self.assertEqual(IntentRouterService.detect_intent("what is the unit layout?"), "syllabus")
        self.assertEqual(IntentRouterService.detect_intent("explain the curriculum outline"), "syllabus")

    @patch("app.services.structured_output.StructuredOutputService.generate_structured")
    def test_analyze_syllabus_saves_to_db(self, mock_generate):
        # Mock LLM response matching SyllabusAnalysisSchema
        mock_data = MagicMock()
        mock_data.course_name = "Algorithms 101"
        mock_data.subject_code = "CS201"
        mock_data.estimated_difficulty = "hard"
        
        topic1 = MagicMock()
        topic1.topic_name = "Quick Sort"
        topic1.unit_title = "Unit 1: Sorting"
        topic1.importance_score = 9.5
        topic1.estimated_hours = 2.0
        topic1.difficulty_level = "medium"
        topic1.dependencies = []
        topic1.priority_rank = 1

        topic2 = MagicMock()
        topic2.topic_name = "Merge Sort"
        topic2.unit_title = "Unit 1: Sorting"
        topic2.importance_score = 8.0
        topic2.estimated_hours = 1.5
        topic2.difficulty_level = "easy"
        topic2.dependencies = ["Quick Sort"]
        topic2.priority_rank = 2

        mock_data.topics = [topic1, topic2]
        mock_generate.return_value = mock_data

        # Create ExtractedDocument record
        file_uuid = uuid.uuid4()
        doc = ExtractedDocument(
            file_id=file_uuid,
            extracted_text="Introduction to Algorithms Course Syllabus. Unit 1 covers sorting algorithms like Quick Sort and Merge Sort.",
            syllabus_detected=False
        )
        self.db.add(doc)
        self.db.commit()

        # Run service analysis
        res = SyllabusAnalyzerService.analyze_syllabus(self.db, str(file_uuid))

        # Asserts
        self.assertEqual(res["course_name"], "Algorithms 101")
        self.assertEqual(res["subject_code"], "CS201")
        self.assertEqual(res["total_topics"], 2)

        # Confirm saved database records
        db_topics = self.db.query(SyllabusTopic).filter(SyllabusTopic.document_id == doc.id).all()
        self.assertEqual(len(db_topics), 2)
        
        quick_sort_t = next(t for t in db_topics if t.topic_name == "Quick Sort")
        self.assertEqual(quick_sort_t.unit_title, "Unit 1: Sorting")
        self.assertEqual(quick_sort_t.importance_score, 9.5)
        self.assertEqual(quick_sort_t.estimated_hours, 2.0)
        self.assertEqual(quick_sort_t.difficulty_level, "medium")
        self.assertEqual(quick_sort_t.priority_rank, 1)
        self.assertEqual(quick_sort_t.dependencies, "")

        merge_sort_t = next(t for t in db_topics if t.topic_name == "Merge Sort")
        self.assertEqual(merge_sort_t.dependencies, "Quick Sort")


if __name__ == "__main__":
    unittest.main()
