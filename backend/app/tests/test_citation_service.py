import unittest
from app.services.citation_service import CitationService


class TestCitationService(unittest.TestCase):

    def test_parse_citations_valid(self):
        answer_text = "Backpropagation calculates gradients using the chain rule [doc_1]. Optimizers like Adam speed up convergence [doc_2]."
        context_chunks = [
            {"document": "Backpropagation uses the chain rule to calculate gradients.", "metadata": {"file_name": "nn.pdf", "file_id": "file_uuid_1", "page_number": 12}},
            {"document": "Adam is a robust optimization algorithm.", "metadata": {"file_name": "optim.pdf", "file_id": "file_uuid_2", "page_number": 5}},
        ]

        formatted_answer, citations = CitationService.parse_citations(answer_text, context_chunks)

        self.assertEqual(
            formatted_answer,
            "Backpropagation calculates gradients using the chain rule [1]. Optimizers like Adam speed up convergence [2]."
        )
        self.assertEqual(len(citations), 2)
        self.assertEqual(citations[0]["citation_id"], 1)
        self.assertEqual(citations[0]["doc_id"], "doc_1")
        self.assertEqual(citations[0]["file_name"], "nn.pdf")
        self.assertEqual(citations[0]["page_number"], 12)
        self.assertEqual(citations[1]["citation_id"], 2)
        self.assertEqual(citations[1]["doc_id"], "doc_2")
        self.assertEqual(citations[1]["file_name"], "optim.pdf")
        self.assertEqual(citations[1]["page_number"], 5)

    def test_parse_citations_hallucinated(self):
        answer_text = "Gradients are calculated using backpropagation [doc_1], but also using momentum [doc_5]."
        context_chunks = [
            {"document": "Backpropagation calculates gradients.", "metadata": {"file_name": "nn.pdf", "file_id": "file_uuid_1", "page_number": 12}},
        ]

        formatted_answer, citations = CitationService.parse_citations(answer_text, context_chunks)

        # [doc_5] is hallucinated, so it should be stripped.
        self.assertEqual(
            formatted_answer,
            "Gradients are calculated using backpropagation [1], but also using momentum ."
        )
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["citation_id"], 1)
        self.assertEqual(citations[0]["doc_id"], "doc_1")
        self.assertEqual(citations[0]["file_name"], "nn.pdf")

    def test_parse_citations_sequential_ordering(self):
        # Even if doc_2 is cited first, it should become citation [1], and doc_1 becomes citation [2].
        answer_text = "Optimizers like Adam speed up convergence [doc_2]. Backpropagation calculates gradients [doc_1]."
        context_chunks = [
            {"document": "Backpropagation details.", "metadata": {"file_name": "nn.pdf", "file_id": "file_uuid_1", "page_number": 12}},
            {"document": "Adam details.", "metadata": {"file_name": "optim.pdf", "file_id": "file_uuid_2", "page_number": 5}},
        ]

        formatted_answer, citations = CitationService.parse_citations(answer_text, context_chunks)

        self.assertEqual(
            formatted_answer,
            "Optimizers like Adam speed up convergence [1]. Backpropagation calculates gradients [2]."
        )
        self.assertEqual(len(citations), 2)
        self.assertEqual(citations[0]["citation_id"], 1)
        self.assertEqual(citations[0]["doc_id"], "doc_2")
        self.assertEqual(citations[0]["file_name"], "optim.pdf")
        self.assertEqual(citations[1]["citation_id"], 2)
        self.assertEqual(citations[1]["doc_id"], "doc_1")
        self.assertEqual(citations[1]["file_name"], "nn.pdf")


if __name__ == "__main__":
    unittest.main()
