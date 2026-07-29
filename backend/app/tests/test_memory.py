import unittest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.chat_message import ChatMessage
from app.services.memory_service import MemoryService
from app.services.prompt_builder import PromptBuilderService
from app.services.llm_service import LLMService


class TestConversationMemory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up an in-memory SQLite database for testing database operations
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.query(ChatMessage).delete()
        self.db.commit()
        self.db.close()

    def test_save_and_retrieve_memory(self):
        session_id = str(uuid.uuid4())
        
        # Save messages
        msg1 = MemoryService.save_message(self.db, session_id, 1, "user", "What is gradient descent?")
        msg2 = MemoryService.save_message(self.db, session_id, 1, "assistant", "Gradient descent is an optimization algorithm...")
        msg3 = MemoryService.save_message(self.db, session_id, 1, "user", "What about SGD?")
        
        # Get history (sliding window of 2)
        history = MemoryService.get_session_history(self.db, session_id, 1, limit=2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "assistant")
        self.assertEqual(history[0].content, "Gradient descent is an optimization algorithm...")
        self.assertEqual(history[1].role, "user")
        self.assertEqual(history[1].content, "What about SGD?")

        # Get history (sliding window of 5 - gets all 3)
        history_all = MemoryService.get_session_history(self.db, session_id, 1, limit=5)
        self.assertEqual(len(history_all), 3)
        self.assertEqual(history_all[0].content, "What is gradient descent?")
        self.assertEqual(history_all[2].content, "What about SGD?")

    def test_session_history_user_isolation(self):
        session_id = str(uuid.uuid4())
        
        # Save messages for user_id = 1
        MemoryService.save_message(self.db, session_id, 1, "user", "What is gradient descent?")
        
        # Get history for user_id = 1 (owner)
        history_owner = MemoryService.get_session_history(self.db, session_id, 1, limit=5)
        self.assertEqual(len(history_owner), 1)

        # Get history for user_id = 2 (non-owner - should return empty due to tenant isolation)
        history_non_owner = MemoryService.get_session_history(self.db, session_id, 2, limit=5)
        self.assertEqual(len(history_non_owner), 0)

    def test_prompt_builder_history_formatting(self):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        prompt_payload = PromptBuilderService.build_rag_prompt(
            query="Tell me about SGD.",
            chunks=[{"document": "SGD convergence details.", "metadata": {"file_name": "optim.pdf", "chunk_index": 0}}],
            history=history
        )
        
        self.assertIn("history_block", prompt_payload)
        self.assertIn("hello", prompt_payload["history_block"].lower())
        self.assertIn("hi there!", prompt_payload["history_block"].lower())
        self.assertIn("<conversation_history>", prompt_payload["full_prompt"])

    @patch("app.services.llm_service.httpx.post")
    def test_llm_service_query_rewriter(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "What is SGD?"}
        mock_post.return_value = mock_response

        history = [
            {"role": "user", "content": "Explain Stochastic Gradient Descent."},
            {"role": "assistant", "content": "SGD updates weights per sample."}
        ]

        rewritten = LLMService.rewrite_query(
            question="How does it work?",
            history=history
        )

        self.assertEqual(rewritten, "What is SGD?")
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
