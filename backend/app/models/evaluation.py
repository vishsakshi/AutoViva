from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class AnswerEvaluation(BaseModel):
    question_id: str
    student_answer: str
    score: float = 0.0
    feedback: str = ""
    key_points_covered: List[str] = []

class EvaluationBase(BaseModel):
    viva_id: str
    student_id: str
    total_score: float = 0.0
    evaluations: List[AnswerEvaluation] = []
    summary_feedback: str = ""
    completed_at: datetime = Field(default_factory=datetime.utcnow)

class EvaluationInDB(EvaluationBase):
    id: Optional[str] = Field(default=None, alias="_id")
