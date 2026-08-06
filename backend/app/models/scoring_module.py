from typing import List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.models.evaluation_module import EvaluatorClassification

class CriterionScoringResult(BaseModel):
    criterion_id: str
    criterion_text: str
    allocated_marks: float
    earned_marks: float
    classification: EvaluatorClassification
    confidence: float
    multiplier_applied: float

class ScoringModule2Response(BaseModel):
    status: str = "success"
    evaluation_id: str
    criterion_scores: List[CriterionScoringResult]
    total_score: float
    max_score: float = 10.0
    percentage: float
    pending_faculty_review: bool
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
