from typing import Optional, List
from pydantic import BaseModel, Field

class QuestionDifficulty(str):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionBase(BaseModel):
    viva_id: str
    topic: str
    question_text: str
    difficulty: str = "medium"
    expected_key_points: List[str] = []

class QuestionCreate(QuestionBase):
    pass

class QuestionInDB(QuestionBase):
    id: Optional[str] = Field(default=None, alias="_id")
