import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.uploaded_file import UploadedFile
from app.models.extracted_document import ExtractedDocument
from app.models.document_chunk import DocumentChunk
from app.models.summary import Summary
from app.schemas.summary_schema import (
    SummarySchema,
    KeyTopicSchema,
    CoreConceptSchema,
    FormulaSchema,
    SummaryCreateRequestSchema
)
from app.services.summarizer import SummarizationService
from app.api.routes.summary import generate_new_summary, get_summary_by_file_id, get_summary_by_id


class TestSummarizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        
        # Setup mock file structure in SQLite DB
        self.user_id = 1
        self.file_id = uuid.uuid4()
        
        db_file = UploadedFile(
            id=self.file_id,
            user_id=self.user_id,
            file_name="physics.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="/tmp/physics.pdf",
            processing_status="processed"
        )
        self.db.add(db_file)
        self.db.commit()
        
        self.doc_id = uuid.uuid4()
        db_doc = ExtractedDocument(
            id=self.doc_id,
            file_id=self.file_id,
            extracted_text="Sample text"
        )
        self.db.add(db_doc)
        self.db.commit()

    def tearDown(self):
        self.db.query(DocumentChunk).delete()
        self.db.query(ExtractedDocument).delete()
        self.db.query(UploadedFile).delete()
        self.db.query(Summary).delete()
        self.db.commit()
        self.db.close()

    def add_mock_chunks(self, num_chunks: int):
        for i in range(num_chunks):
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                document_id=self.doc_id,
                chunk_index=i,
                chunk_text=f"This is the text for chunk #{i}. Content detail.",
                word_count=10,
                page_number=1
            )
            self.db.add(chunk)
        self.db.commit()

    @patch("app.services.structured_output.StructuredOutputService.generate_structured")
    def test_generate_summary_direct_synthesis(self, mock_generate):
        # Insert 3 chunks (triggers direct synthesis <= 4 chunks)
        self.add_mock_chunks(3)

        mock_schema = SummarySchema(
            title="Physics Summary",
            overall_summary="Overview of physics concepts.",
            key_topics=[
                KeyTopicSchema(
                    name="Force",
                    summary="Detailed summary of force.",
                    core_concepts=[CoreConceptSchema(name="Gravity", definition="Pulling force", explanation="Isaac Newton")],
                    formulas=[FormulaSchema(equation="F=ma", description="Newton second law")],
                    citations=["physics.pdf (Chunk #0)"]
                )
            ]
        )
        mock_generate.return_value = mock_schema

        db_summary = SummarizationService.generate_summary(
            db=self.db,
            user_id=self.user_id,
            file_id=str(self.file_id),
            granularity="detailed"
        )

        self.assertIsNotNone(db_summary.id)
        self.assertEqual(db_summary.title, "Physics Summary")
        self.assertEqual(db_summary.granularity, "detailed")
        self.assertEqual(db_summary.summary_data["overall_summary"], "Overview of physics concepts.")
        mock_generate.assert_called_once()

    @patch("app.services.llm_service.LLMService.generate_answer")
    @patch("app.services.structured_output.StructuredOutputService.generate_structured")
    def test_generate_summary_map_reduce(self, mock_generate, mock_llm):
        # Insert 6 chunks (triggers Map-Reduce > 4 chunks)
        self.add_mock_chunks(6)

        # Mock segment summaries for 2 groups (6 chunks grouped by 3 = 2 map runs)
        mock_llm.side_effect = [
            "Summary of segment 1",
            "Summary of segment 2"
        ]

        mock_schema = SummarySchema(
            title="Map Reduce Summary",
            overall_summary="Synthesized summary.",
            key_topics=[]
        )
        mock_generate.return_value = mock_schema

        db_summary = SummarizationService.generate_summary(
            db=self.db,
            user_id=self.user_id,
            file_id=str(self.file_id),
            granularity="detailed"
        )

        self.assertIsNotNone(db_summary.id)
        self.assertEqual(db_summary.title, "Map Reduce Summary")
        self.assertEqual(mock_llm.call_count, 2)  # Should map 2 segments
        mock_generate.assert_called_once()

    def test_generate_summary_no_chunks_fails(self):
        # No chunks in DB
        with self.assertRaises(ValueError):
            SummarizationService.generate_summary(
                db=self.db,
                user_id=self.user_id,
                file_id=str(self.file_id),
                granularity="bullet"
            )

    @patch("app.services.summarizer.SummarizationService.generate_summary")
    def test_api_generate_route(self, mock_gen_summary):
        mock_sum = Summary(id=uuid.uuid4(), user_id=1, file_id=self.file_id, title="API Summary", granularity="detailed", summary_data={})
        mock_gen_summary.return_value = mock_sum

        request = SummaryCreateRequestSchema(
            file_id=str(self.file_id),
            granularity="detailed",
            user_id=1
        )

        response = generate_new_summary(request=request, db=self.db)
        self.assertEqual(response.title, "API Summary")
        self.assertEqual(response.user_id, 1)
        mock_gen_summary.assert_called_once()


if __name__ == "__main__":
    unittest.main()
