from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class VivaStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class VivaBase(BaseModel):
    title: str
    subject: str
    faculty_id: str
    duration_minutes: int = 30
    total_questions: int = 5
    status: VivaStatus = VivaStatus.DRAFT

class VivaCreate(VivaBase):
    pass

class VivaInDB(VivaBase):
    id: Optional[str] = Field(default=None, alias="_id")
    student_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
