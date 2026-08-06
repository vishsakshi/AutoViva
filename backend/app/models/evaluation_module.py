from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.models.question_gen import RubricCriterion

class EvaluatorClassification(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_MENTIONED = "NOT_MENTIONED"
    CONTRADICTED = "CONTRADICTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

class EvaluateAnswerRequest(BaseModel):
    question_text: str = Field(..., description="The viva question text")
    ideal_answer: str = Field(..., description="Reference ideal answer for context")
    evaluation_rubric: List[RubricCriterion] = Field(..., description="List of rubric criteria with allocated marks")
    student_answer: str = Field(..., description="Student's submitted oral/written answer")
    subject: Optional[str] = "Computer Networks"
    topic: Optional[str] = "IP Addressing & NAT"

class CriterionEvaluationOutput(BaseModel):
    criterion_id: str
    criterion_text: str
    allocated_marks: float
    classification: EvaluatorClassification
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evaluator confidence score between 0.0 and 1.0")
    evidence_quote: str = Field(default="", description="Verbatim quote from student answer supporting classification")
    reasoning: str = Field(default="", description="Brief semantic explanation for classification")

class EvaluationModule1Response(BaseModel):
    status: str = "success"
    evaluation_id: str
    question_text: str
    student_answer: str
    criterion_evaluations: List[CriterionEvaluationOutput]
    overall_confidence: float
    processing_latency_ms: float
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
