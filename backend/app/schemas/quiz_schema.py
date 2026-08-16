from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import datetime


class QuestionSchema(BaseModel):
    text: str = Field(description="The text of the question, or case study scenario text followed by the question")
    type: str = Field(description="Question type: 'mcq' (Multiple Choice), 'true_false', or 'scenario'")
    options: List[str] = Field(description="List of choices. For true_false, this must contain exactly ['True', 'False']")
    correct_answer_idx: int = Field(description="0-based index of the correct option in the options list")
    difficulty: str = Field(description="Difficulty level of the question: 'easy', 'medium', or 'hard'")
    explanation: str = Field(description="A brief explanation of why the correct option is right and incorrect options are wrong")
    source_citation: Optional[str] = Field(None, description="A direct short text quote from the context validating the correct answer")


class QuizSchema(BaseModel):
    title: str = Field(description="A short, descriptive, subject-appropriate title for the quiz based on the study topic")
    questions: List[QuestionSchema] = Field(description="List of generated quiz questions")


class QuizCreateRequestSchema(BaseModel):
    file_id: str
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5
    user_id: int = 1


class QuizQuestionResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_text: str
    question_type: str
    options: List[str]
    correct_answer_idx: int
    difficulty: str
    explanation: str
    source_citation: Optional[str] = None
    created_at: datetime.datetime


class QuizResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    title: str
    file_id: Optional[str] = None
    created_at: datetime.datetime
    questions: List[QuizQuestionResponseSchema]
