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
    allocated_marks: Optional[float] = Field(default=10.0, gt=0)
    subject: Optional[str] = "Computer Networks"
    topic: Optional[str] = "IP Addressing & NAT"
    # Passed by the student frontend so evaluations are keyed to the right question/student
    question_id: Optional[str] = "vq_com_ip_4198fe"
    student_id: Optional[str] = "std_anonymous"
    viva_id: Optional[str] = None
    attempt_id: Optional[str] = None
    attempt_started_at: Optional[str] = None
    question_number: Optional[int] = None

class CriterionEvaluationOutput(BaseModel):
    criterion_id: str
    criterion_text: str
    allocated_marks: float
    awarded_marks: Optional[float] = Field(default=None, ge=0)
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
