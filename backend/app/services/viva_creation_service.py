import os
import uuid
import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.knowledge_service import knowledge_service
from app.services.question_generator import question_generator_engine
from app.models.question_gen import VivaQuestionSchema

logger = logging.getLogger("autoviva.services.viva_creation")

class VivaCreateRequest(BaseModel):
    subject: str = Field(..., description="Subject Name")
    course_code: str = Field(..., description="Course Code (e.g. CS301)")
    topic: str = Field(..., description="Topic / Unit Name")
    difficulty: str = Field(default="medium")
    question_count: int = Field(default=3, ge=1, le=10)
    duration_minutes: int = Field(default=15, ge=5, le=60)
    batch: str = Field(default="Batch 2026", description="Student Batch")

class VivaSessionRecord(BaseModel):
    viva_id: str
    subject: str
    course_code: str
    topic: str
    difficulty: str
    question_count: int
    duration_minutes: int
    batch: str
    uploaded_files: List[str] = []
    generated_questions: List[Dict[str, Any]] = []
    approved_questions: List[Dict[str, Any]] = []
    status: str = "DRAFT"  # DRAFT -> QUESTIONS_GENERATED -> PUBLISHED
    created_at: str

viva_sessions_db: Dict[str, VivaSessionRecord] = {}

class VivaCreationService:
    def create_viva(self, req: VivaCreateRequest) -> VivaSessionRecord:
        v_id = f"viva_{uuid.uuid4().hex[:8]}"
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        record = VivaSessionRecord(
            viva_id=v_id,
            subject=req.subject.strip(),
            course_code=req.course_code.strip(),
            topic=req.topic.strip(),
            difficulty=req.difficulty,
            question_count=req.question_count,
            duration_minutes=req.duration_minutes,
            batch=req.batch.strip(),
            created_at=now
        )
        viva_sessions_db[v_id] = record
        return record

    def add_uploaded_file(self, viva_id: str, filename: str) -> VivaSessionRecord:
        record = viva_sessions_db.get(viva_id)
        if not record:
            raise ValueError(f"Viva session {viva_id} not found.")
        record.uploaded_files.append(filename)
        return record

    def generate_questions_for_viva(self, viva_id: str) -> VivaSessionRecord:
        record = viva_sessions_db.get(viva_id)
        if not record:
            raise ValueError(f"Viva session {viva_id} not found.")

        # Question generation using ChromaDB retrieved context
        results = question_generator_engine.generate_questions(
            subject=record.subject,
            topic=record.topic,
            difficulty=record.difficulty,
            count=record.question_count
        )

        q_list = []
        for q in results.get("generated_questions", []):
            q_dict = q.model_dump() if hasattr(q, "model_dump") else q.dict()
            q_list.append(q_dict)

        record.generated_questions = q_list
        record.status = "QUESTIONS_GENERATED"
        return record

    def review_viva_question(self, viva_id: str, question_id: str, action: str, edited_text: Optional[str] = None) -> VivaSessionRecord:
        record = viva_sessions_db.get(viva_id)
        if not record:
            raise ValueError(f"Viva session {viva_id} not found.")

        if action.upper() == "APPROVE":
            for q in record.generated_questions:
                if q["question_id"] == question_id:
                    if edited_text and edited_text.strip():
                        q["question_text"] = edited_text.strip()
                    if q not in record.approved_questions:
                        record.approved_questions.append(q)
                    break
        elif action.upper() == "REJECT":
            record.generated_questions = [q for q in record.generated_questions if q["question_id"] != question_id]
            record.approved_questions = [q for q in record.approved_questions if q["question_id"] != question_id]

        return record

    def publish_viva(self, viva_id: str) -> VivaSessionRecord:
        record = viva_sessions_db.get(viva_id)
        if not record:
            raise ValueError(f"Viva session {viva_id} not found.")

        if len(record.approved_questions) == 0:
            record.approved_questions = list(record.generated_questions)

        record.status = "PUBLISHED"
        return record

    def get_published_vivas(self) -> List[VivaSessionRecord]:
        return [v for v in viva_sessions_db.values() if v.status == "PUBLISHED" or len(v.approved_questions) > 0]

viva_creation_service = VivaCreationService()
