from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.models.evaluation_module import EvaluationModule1Response, EvaluatorClassification
from app.models.scoring_module import ScoringModule2Response

class EvidenceValidationItem(BaseModel):
    criterion_id: str
    evidence_quote: str
    is_verbatim: bool
    validation_status: str = Field(..., description="'VALID_VERBATIM', 'EMPTY_NOT_MENTIONED', or 'INVALID_EVIDENCE'")

class CriterionFeedbackItem(BaseModel):
    criterion_id: str
    criterion_text: str
    allocated_marks: float
    earned_marks: float
    classification: EvaluatorClassification
    confidence: float
    evidence_quote: str
    evidence_valid: bool
    feedback_note: str

class EvaluationSummary(BaseModel):
    evaluation_id: str
    final_score: float
    max_score: float = 10.0
    percentage: float
    pending_faculty_review: bool
    evidence_validity_status: str = Field(..., description="'ALL_EVIDENCE_VALID' or 'CONTAINS_INVALID_EVIDENCE'")

class GenerateFeedbackRequest(BaseModel):
    question_text: str
    ideal_answer: str
    student_answer: str
    module1_result: EvaluationModule1Response
    module2_result: ScoringModule2Response

class FeedbackModule3Response(BaseModel):
    status: str = "success"
    evaluation_summary: EvaluationSummary
    criterion_feedback: List[CriterionFeedbackItem]
    strengths: List[str] = []
    improvements: List[Dict[str, str]] = []
    misconceptions: List[Dict[str, str]] = []
    evidence_validation: List[EvidenceValidationItem] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
