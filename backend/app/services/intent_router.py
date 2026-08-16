import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class IntentRouterService:
    """
    Evaluates user queries and classifies intent to route request blocks to the proper service:
    - 'quiz': Generates dynamic assessments.
    - 'summary': Generates structured summary sheets.
    - 'chat': Normal grounded RAG conversation.
    """

    @classmethod
    def detect_intent(cls, query: str) -> str:
        q_lower = query.lower().strip()
        logger.info(f"Classifying user query intent for: '{q_lower}'")

        # Syllabus classification patterns
        syllabus_patterns = [
            r"\bsyllabus\b",
            r"\bcourse\s*map\b",
            r"\bsubject\s*outline\b",
            r"\bcurriculum\b",
            r"\bunit\s*layout\b"
        ]

        # Summary classification patterns
        summary_patterns = [
            r"\bsummariz(e|ation)\b",
            r"\bsummary\b",
            r"\bnotes\b",
            r"\boutline\b",
            r"\bcheat\s*sheet\b",
            r"\brevision\b"
        ]

        # Quiz classification patterns
        quiz_patterns = [
            r"\bquiz\b",
            r"\btest\b",
            r"\bmcqs?\b",
            r"\bquestions?\b",
            r"\bexam\b",
            r"\bassessment\b",
            r"\bpractice\b"
        ]

        # Evaluate syllabus keywords
        for pattern in syllabus_patterns:
            if re.search(pattern, q_lower):
                logger.info("Classified intent as: 'syllabus'")
                return "syllabus"

        # Evaluate summary keywords
        for pattern in summary_patterns:
            if re.search(pattern, q_lower):
                logger.info("Classified intent as: 'summary'")
                return "summary"

        # Evaluate quiz keywords
        for pattern in quiz_patterns:
            if re.search(pattern, q_lower):
                logger.info("Classified intent as: 'quiz'")
                return "quiz"

        logger.info("Classified intent as: 'chat'")
        return "chat"

    @classmethod
    def extract_quiz_params(cls, query: str) -> Dict[str, Any]:
        """
        Helper method to extract quiz customization parameters from user's natural language input.
        """
        q_lower = query.lower()
        params = {
            "num_questions": 5,
            "difficulty": "medium"
        }

        # Match difficulty levels
        if "easy" in q_lower:
            params["difficulty"] = "easy"
        elif "hard" in q_lower or "difficult" in q_lower or "challenging" in q_lower:
            params["difficulty"] = "hard"

        # Match question counts (e.g. "10 questions", "3 mcqs", "15 hard mcqs")
        count_match = re.search(r"(\d+)\s*(?:easy|medium|hard|difficult|challenging|practice)?\s*(questions?|mcqs?|tests?)", q_lower)
        if count_match:
            try:
                params["num_questions"] = int(count_match.group(1))
            except ValueError:
                pass

        logger.info(f"Extracted quiz params: {params}")
        return params
