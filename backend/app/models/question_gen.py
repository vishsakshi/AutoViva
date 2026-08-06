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
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"

class RubricCriterion(BaseModel):
    criterion: str
    marks: float = Field(..., description="Mark allocation for criterion")

class VivaQuestionSchema(BaseModel):
    question_id: str
    subject: str
    topic: str
    difficulty: str = "medium"
    blooms_level: BloomTaxonomy = BloomTaxonomy.UNDERSTAND
    learning_objective: str
    question_text: str
    ideal_answer: str
    key_concepts: List[str] = []
    evaluation_rubric: List[RubricCriterion] = []
    total_marks: float = 10.0
    reference_source: str
    estimated_answer_time_seconds: int = 120
    status: QuestionStatus = QuestionStatus.DRAFT
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GenerateQuestionsRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str = "medium"
    question_count: int = 3
    bloom_level: Optional[BloomTaxonomy] = BloomTaxonomy.UNDERSTAND

class ReviewActionRequest(BaseModel):
    question_id: str
    action: str = Field(..., description="'approve', 'reject', or 'edit'")
    edited_question: Optional[VivaQuestionSchema] = None
