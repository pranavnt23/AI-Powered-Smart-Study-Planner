from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import datetime


class CoreConceptSchema(BaseModel):
    name: str = Field(description="Name of the core concept or terminology definition")
    definition: str = Field(description="Strict definition of the concept as stated in the text context")
    explanation: str = Field(description="A brief explanation expanding on the significance of the concept")


class FormulaSchema(BaseModel):
    equation: str = Field(description="Scientific formula, mathematical equation, or programming function expression")
    description: str = Field(description="Explanation of variables and usage details for the formula")


class KeyTopicSchema(BaseModel):
    name: str = Field(description="Name of the topic or document chapter section")
    summary: str = Field(description="A concise summary of the topic section")
    core_concepts: List[CoreConceptSchema] = Field(default=[], description="Core concepts and terminology definitions introduced in this topic")
    formulas: List[FormulaSchema] = Field(default=[], description="Relevant mathematical or scientific formulas mentioned under this topic")
    citations: List[str] = Field(default=[], description="List of source indicators (e.g. ['physics.pdf (Chunk #1)']) grounding this topic section")


class SummarySchema(BaseModel):
    title: str = Field(description="A descriptive title for this study summary guide")
    overall_summary: str = Field(description="A comprehensive, high-level summary overview of the entire document")
    key_topics: List[KeyTopicSchema] = Field(description="A structured list of all core topics extracted from the document chunks")


class SummaryCreateRequestSchema(BaseModel):
    file_id: str
    granularity: str = "detailed"  # 'bullet', 'detailed'
    user_id: int = 1


class SummaryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    file_id: str
    title: str
    granularity: str
    summary_data: dict  # Direct dictionary representation of SummarySchema structure
    created_at: datetime.datetime
