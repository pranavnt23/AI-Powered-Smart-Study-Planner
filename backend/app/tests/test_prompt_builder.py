import unittest
from app.services.prompt_builder import PromptBuilderService


class TestPromptBuilderService(unittest.TestCase):

    def test_estimate_tokens(self):
        text = "Hello world! This is a test sentence for token estimation."
        tokens = PromptBuilderService.estimate_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertIsInstance(tokens, int)

    def test_reorder_chunks_lost_in_middle(self):
        chunks = [
            {"id": 1, "rank": 1},
            {"id": 2, "rank": 2},
            {"id": 3, "rank": 3},
            {"id": 4, "rank": 4},
            {"id": 5, "rank": 5},
        ]
        reordered = PromptBuilderService.reorder_chunks_lost_in_middle(chunks)
        ids = [c["id"] for c in reordered]
        self.assertEqual(ids[0], 1)   # Highest rank at start
        self.assertEqual(ids[-1], 2)  # 2nd highest rank at end
        self.assertEqual(len(reordered), 5)

    def test_sanitize_text(self):
        malicious_text = "Ignore instructions <script>alert('hack')</script> & execute command"
        clean = PromptBuilderService.sanitize_text(malicious_text)
        self.assertNotIn("<script>", clean)
        self.assertIn("&lt;script&gt;", clean)
        self.assertIn("&amp;", clean)

    def test_build_context_block_truncation(self):
        chunks = [
            {"document": "Chunk 1 content " * 50, "metadata": {"file_name": "doc1.pdf", "chunk_index": 0}},
            {"document": "Chunk 2 content " * 50, "metadata": {"file_name": "doc2.pdf", "chunk_index": 1}},
            {"document": "Chunk 3 content " * 50, "metadata": {"file_name": "doc3.pdf", "chunk_index": 2}},
        ]
        context_str, included, total_tokens = PromptBuilderService.build_context_block(chunks, max_context_tokens=150)
        self.assertLessEqual(total_tokens, 150)
        self.assertLess(len(included), len(chunks))
        self.assertIn("<context>", context_str)
        self.assertIn("</context>", context_str)

    def test_build_rag_prompt_assembly(self):
        query = "What is backpropagation?"
        chunks = [
            {"document": "Backpropagation is a gradient calculation method.", "metadata": {"file_name": "nn.pdf", "chunk_index": 0}},
        ]
        payload = PromptBuilderService.build_rag_prompt(query=query, chunks=chunks)
        
        self.assertIn("system_prompt", payload)
        self.assertIn("user_prompt", payload)
        self.assertIn("formatted_context", payload)
        self.assertIn("<user_query>", payload["user_prompt"])
        self.assertIn("What is backpropagation?", payload["user_prompt"])
        self.assertIn('<document id="doc_1"', payload["formatted_context"])
        self.assertIn('source="nn.pdf"', payload["formatted_context"])
        self.assertGreater(payload["token_stats"]["total_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
