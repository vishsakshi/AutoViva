from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.models.feedback_module import FeedbackModule3Response, EvaluationSummary, CriterionFeedbackItem

class EvaluationStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"

class FacultyAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    OVERRIDE = "OVERRIDE"

class FacultyOverrideRequest(BaseModel):
    action: FacultyAction = Field(..., description="APPROVE, REJECT, or OVERRIDE")
    new_score: Optional[float] = Field(None, description="Updated total score if overriding")
    criterion_score_overrides: Optional[Dict[str, float]] = Field(None, description="Map of criterion_id to new earned marks")
    faculty_comment: Optional[str] = Field("", description="Comments or feedback from faculty")
    reason_for_change: Optional[str] = Field("", description="Explanation for score/classification modification")

class FacultyAuditLogEntry(BaseModel):
    log_id: str
    evaluation_id: str
    faculty_action: FacultyAction
    previous_score: float
    new_score: float
    reason_for_change: str
    faculty_comment: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FullEvaluationRecord(BaseModel):
    evaluation_id: str
    question_id: Optional[str] = "vq_com_ip_4198fe"
    student_id: Optional[str] = "std_10293"
    question_text: str
    ideal_answer: str
    student_answer: str
    status: EvaluationStatus = EvaluationStatus.PENDING_REVIEW
    current_version: int = 1
    ai_version_v1: FeedbackModule3Response
    faculty_version_v2: Optional[FeedbackModule3Response] = None
    audit_history: List[FacultyAuditLogEntry] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
