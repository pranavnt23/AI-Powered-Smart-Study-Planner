import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.conversation import Conversation
from app.models.chat_message import ChatMessage
from app.models.uploaded_file import UploadedFile
from app.models.extracted_document import ExtractedDocument
from app.models.document_chunk import DocumentChunk
from app.services.intent_router import IntentRouterService
from app.api.routes.chat import query_rag_pipeline, QueryRequestSchema


class TestIntentRouterAndPersistence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        
        # Enforce foreign key constraints in SQLite for cascade deletion testing
        from sqlalchemy import event
        @event.listens_for(cls.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.query(ChatMessage).delete()
        self.db.query(Conversation).delete()
        self.db.query(DocumentChunk).delete()
        self.db.query(ExtractedDocument).delete()
        self.db.query(UploadedFile).delete()
        self.db.commit()
        self.db.close()

    def test_intent_detection(self):
        # Assert quiz intent detection keywords
        self.assertEqual(IntentRouterService.detect_intent("generate 5 hard mcqs"), "quiz")
        self.assertEqual(IntentRouterService.detect_intent("give me a practice test"), "quiz")
        self.assertEqual(IntentRouterService.detect_intent("what are some assessment questions?"), "quiz")

        # Assert summary intent detection keywords
        self.assertEqual(IntentRouterService.detect_intent("summarize this chapter"), "summary")
        self.assertEqual(IntentRouterService.detect_intent("write some revision notes"), "summary")
        self.assertEqual(IntentRouterService.detect_intent("create a cheat sheet for exam"), "summary")

        # Assert chat default RAG intent
        self.assertEqual(IntentRouterService.detect_intent("explain Newton's second law of motion"), "chat")
        self.assertEqual(IntentRouterService.detect_intent("what is the definition of force?"), "chat")

    def test_quiz_parameter_extraction(self):
        # Count extraction
        params_1 = IntentRouterService.extract_quiz_params("generate 15 hard mcqs")
        self.assertEqual(params_1["num_questions"], 15)
        self.assertEqual(params_1["difficulty"], "hard")

        # Fallback values
        params_2 = IntentRouterService.extract_quiz_params("generate questions")
        self.assertEqual(params_2["num_questions"], 5)
        self.assertEqual(params_2["difficulty"], "medium")

        # Easy difficulty check
        params_3 = IntentRouterService.extract_quiz_params("give me 3 easy questions")
        self.assertEqual(params_3["num_questions"], 3)
        self.assertEqual(params_3["difficulty"], "easy")

    def test_cascade_delete_conversations_to_messages(self):
        # Create a conversation
        session_id = uuid.uuid4()
        conv = Conversation(id=session_id, user_id=1, title="Test Session")
        self.db.add(conv)
        self.db.commit()

        # Add linked messages
        msg1 = ChatMessage(session_id=session_id, user_id=1, role="user", content="Hello")
        msg2 = ChatMessage(session_id=session_id, user_id=1, role="assistant", content="Hi")
        self.db.add(msg1)
        self.db.add(msg2)
        self.db.commit()

        # Assert initial state
        self.assertEqual(self.db.query(Conversation).count(), 1)
        self.assertEqual(self.db.query(ChatMessage).count(), 2)

        # Delete conversation
        self.db.delete(conv)
        self.db.commit()

        # Assert cascade deleted linked messages
        self.assertEqual(self.db.query(Conversation).count(), 0)
        self.assertEqual(self.db.query(ChatMessage).count(), 0)


if __name__ == "__main__":
    unittest.main()
