import unittest
import json
from unittest.mock import patch, MagicMock
from pydantic import BaseModel, Field, ValidationError

from app.services.structured_output import StructuredOutputService


# Define a mock schema to use in unit tests
class MockStudyTopic(BaseModel):
    title: str = Field(description="Title of the topic")
    hours: int = Field(description="Estimated study hours")


class TestStructuredOutput(unittest.TestCase):

    def test_extract_json_block_clean(self):
        raw = '{"title": "Algorithms", "hours": 4}'
        parsed = StructuredOutputService.extract_json_block(raw)
        self.assertEqual(parsed["title"], "Algorithms")
        self.assertEqual(parsed["hours"], 4)

    def test_extract_json_block_markdown(self):
        raw = 'Sure! Here is the JSON:\n```json\n{"title": "Algorithms", "hours": 4}\n```\nHope this helps!'
        parsed = StructuredOutputService.extract_json_block(raw)
        self.assertEqual(parsed["title"], "Algorithms")
        self.assertEqual(parsed["hours"], 4)

    def test_extract_json_block_braces(self):
        raw = 'Random prefix text { "title": "Data Structures", "hours": 8 } random suffix text'
        parsed = StructuredOutputService.extract_json_block(raw)
        self.assertEqual(parsed["title"], "Data Structures")
        self.assertEqual(parsed["hours"], 8)

    def test_extract_json_block_invalid(self):
        raw = 'Invalid response text without braces'
        with self.assertRaises(ValueError):
            StructuredOutputService.extract_json_block(raw)

    @patch("app.services.llm_service.LLMService.generate_answer")
    def test_generate_structured_success_first_attempt(self, mock_generate):
        mock_generate.return_value = '{"title": "Operating Systems", "hours": 6}'
        
        result = StructuredOutputService.generate_structured(
            response_model=MockStudyTopic,
            prompt="Generate a study topic details",
            max_retries=2
        )
        
        self.assertIsInstance(result, MockStudyTopic)
        self.assertEqual(result.title, "Operating Systems")
        self.assertEqual(result.hours, 6)
        mock_generate.assert_called_once()

    @patch("app.services.llm_service.LLMService.generate_answer")
    def test_generate_structured_self_correction_recovery(self, mock_generate):
        # First call returns invalid/malformed schema type (hours is a string that can't convert to int)
        # Second call returns corrected schema
        mock_generate.side_effect = [
            '{"title": "Networks", "hours": "five hours"}',
            '{"title": "Networks", "hours": 5}'
        ]
        
        result = StructuredOutputService.generate_structured(
            response_model=MockStudyTopic,
            prompt="Generate a study topic details",
            max_retries=2
        )
        
        self.assertIsInstance(result, MockStudyTopic)
        self.assertEqual(result.title, "Networks")
        self.assertEqual(result.hours, 5)
        self.assertEqual(mock_generate.call_count, 2)
        
        # Verify self-correction prompt contains error details
        retry_prompt = mock_generate.call_args_list[1][1]["question"]
        self.assertIn("validation", retry_prompt.lower())
        self.assertIn("networks", retry_prompt.lower())

    @patch("app.services.llm_service.LLMService.generate_answer")
    def test_generate_structured_exhausted_retries_fail(self, mock_generate):
        # All attempts return malformed schema (hours field missing)
        mock_generate.return_value = '{"title": "Database Systems"}'
        
        with self.assertRaises(ValidationError):
            StructuredOutputService.generate_structured(
                response_model=MockStudyTopic,
                prompt="Generate a study topic details",
                max_retries=2
            )
            
        self.assertEqual(mock_generate.call_count, 3)  # Initial call + 2 retries


if __name__ == "__main__":
    unittest.main()
