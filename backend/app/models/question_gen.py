from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class BloomTaxonomy(str, Enum):
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"
    EVALUATE = "Evaluate"
    CREATE = "Create"

class QuestionStatus(str, Enum):
    GENERATED = "generated"
    VALIDATED = "validated"
    FACULTY_REVIEW = "faculty_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    PUBLISHED = "published"

class RubricCriterion(BaseModel):
    criterion: str
    marks: float = Field(..., description="Mark allocation for criterion")

class VivaQuestionSchema(BaseModel):
    question_id: str
    document_id: str = ""
    viva_id: str = ""
    filename: str = ""
    subject: str
    topic: str
    section: str = ""
    difficulty: str = "Medium"
    blooms_level: BloomTaxonomy = BloomTaxonomy.UNDERSTAND
    question_text: str
    question: str = ""
    ideal_answer: str
    options: Dict[str, str] = Field(default_factory=dict)
    correct_answer: str = "A"
    source_quote: str = ""
    key_concepts: List[str] = Field(default_factory=list)
    expected_keywords: List[str] = Field(default_factory=list)
    evaluation_rubric: List[RubricCriterion] = Field(default_factory=list)
    rubric: List[Dict[str, Any]] = Field(default_factory=list)
    total_marks: float = 10.0
    source_page: str = "Page 1"
    source_section: str = ""
    source_chunk_ids: List[str] = Field(default_factory=list)
    reference_source: str = ""
    confidence: float = 0.90
    llm_model: str = "gpt-4o-mini"
    validation_status: str = "VERIFIED"
    validation_report: Dict[str, Any] = Field(default_factory=dict)
    estimated_answer_time_seconds: int = 120
    status: QuestionStatus = QuestionStatus.FACULTY_REVIEW
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GenerateQuestionsRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str = "medium"
    question_count: int = 3
    bloom_level: Optional[BloomTaxonomy] = BloomTaxonomy.UNDERSTAND
    document_id: Optional[str] = None
    viva_id: Optional[str] = None

class ReviewActionRequest(BaseModel):
    question_id: str
    action: str = Field(..., description="'approve', 'reject', or 'edit'")
    edited_question: Optional[VivaQuestionSchema] = None
