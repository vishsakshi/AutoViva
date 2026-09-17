import os
import uuid
import time
import logging
import pymongo
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.question_generator import question_generator_engine
from app.models.question_gen import VivaQuestionSchema

logger = logging.getLogger("autoviva.services.viva_creation")

class VivaCreateRequest(BaseModel):
    subject: str = Field(..., description="Subject Name")
    course_code: str = Field(..., description="Course Code (e.g. CS301)")
    topic: str = Field(..., description="Topic / Unit Name")
    difficulty: str = Field(default="balanced")
    question_count: int = Field(default=3, ge=1, le=10)
    duration_minutes: int = Field(default=15, ge=5, le=60)
    batch: str = Field(default="Batch 2026", description="Student Batch")

class VivaSessionRecord(BaseModel):
    viva_id: str
    subject: str
    course_code: str
    topic: str
    difficulty: str = "balanced"
    question_count: int
    duration_minutes: int
    batch: str
    document_id: Optional[str] = None
    uploaded_files: List[str] = []
    topic_map: Optional[Dict[str, Any]] = None
    generated_questions: List[Dict[str, Any]] = []
    approved_questions: List[Dict[str, Any]] = []
    status: str = "DRAFT"  # DRAFT -> QUESTIONS_GENERATED -> PUBLISHED
    created_at: str

viva_sessions_db: Dict[str, VivaSessionRecord] = {}

class VivaCreationService:
    def __init__(self):
        self._init_mongo()

    def _init_mongo(self):
        try:
            self.client = pymongo.MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
            self.db = self.client[settings.DB_NAME]
            self.sessions_col = self.db["viva_sessions"]
            self.sessions_col.create_index("viva_id", unique=True)
            logger.info("VivaCreationService connected to MongoDB 'viva_sessions' collection.")
        except Exception as e:
            logger.warning(f"VivaCreationService Mongo connection notice: {e}")
            self.sessions_col = None

    def _sync_to_mongo(self, record: VivaSessionRecord):
        if self.sessions_col is not None:
            try:
                rec_dict = record.model_dump()
                self.sessions_col.update_one(
                    {"viva_id": record.viva_id},
                    {"$set": rec_dict},
                    upsert=True
                )
                logger.info(f"Synced Viva Session {record.viva_id} to MongoDB.")
            except Exception as e:
                logger.error(f"Failed to sync viva session {record.viva_id} to MongoDB: {e}")

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
        self._sync_to_mongo(record)
        return record

    def get_viva(self, viva_id: str) -> Optional[VivaSessionRecord]:
        if viva_id in viva_sessions_db:
            return viva_sessions_db[viva_id]

        if self.sessions_col is not None:
            doc = self.sessions_col.find_one({"viva_id": viva_id})
            if doc:
                doc.pop("_id", None)
                record = VivaSessionRecord(**doc)
                viva_sessions_db[viva_id] = record
                return record

        return None

    def add_uploaded_file(self, viva_id: str, filename: str, document_id: Optional[str] = None, topic_map: Optional[Dict[str, Any]] = None) -> VivaSessionRecord:
        record = self.get_viva(viva_id)
        if not record:
            raise ValueError(f"Viva session '{viva_id}' not found in database.")
        if filename not in record.uploaded_files:
            record.uploaded_files.append(filename)
        if document_id:
            record.document_id = document_id
        if topic_map:
            record.topic_map = topic_map
        self._sync_to_mongo(record)
        return record

    def generate_questions_for_viva(self, viva_id: str) -> VivaSessionRecord:
        logger.info(f"[QUESTION GEN PIPELINE START] Fetching viva session '{viva_id}'...")
        record = self.get_viva(viva_id)
        if not record:
            err_msg = f"Viva session '{viva_id}' not found in MongoDB or memory. Please configure Step 1 metadata first."
            logger.error(f"[QUESTION GEN ERROR] {err_msg}")
            raise ValueError(err_msg)

        logger.info(f"[SESSION VERIFIED] Viva ID: {record.viva_id}, Document ID: {record.document_id}, Subject: '{record.subject}', Topic: '{record.topic}', Question Count: {record.question_count}")

        # Document-Grounded RAG Question Generation with Verification Gate
        results = question_generator_engine.generate_document_grounded_questions(
            document_id=record.document_id,
            viva_id=record.viva_id,
            subject=record.subject,
            topic=record.topic,
            requested_count=record.question_count
        )

        if results.get("status") == "INSUFFICIENT_CONTEXT":
            raise ValueError(results.get("message", "Insufficient relevant evidence found in the uploaded document."))

        q_list = results.get("generated_questions", [])
        if not q_list:
            raise ValueError("No questions could be generated because no academic context was retrieved from the uploaded syllabus.")

        record.generated_questions = q_list
        record.topic_map = results.get("topic_map", record.topic_map)
        record.status = "QUESTIONS_GENERATED"
        self._sync_to_mongo(record)
        logger.info(f"[QUESTION GEN SUCCESS] Generated & verified {len(q_list)} grounded questions for session {viva_id}.")
        return record

    def review_viva_question(self, viva_id: str, question_id: str, action: str, edited_text: Optional[str] = None) -> VivaSessionRecord:
        record = self.get_viva(viva_id)
        if not record:
            raise ValueError(f"Viva session '{viva_id}' not found.")

        if action.upper() == "APPROVE":
            for q in record.generated_questions:
                if q.get("question_id") == question_id:
                    if edited_text and edited_text.strip():
                        q["question_text"] = edited_text.strip()
                        q["question"] = edited_text.strip()
                    if q not in record.approved_questions:
                        record.approved_questions.append(q)
                    break
        elif action.upper() == "REJECT":
            record.generated_questions = [q for q in record.generated_questions if q.get("question_id") != question_id]
            record.approved_questions = [q for q in record.approved_questions if q.get("question_id") != question_id]

        self._sync_to_mongo(record)
        return record

    def publish_viva(self, viva_id: str) -> VivaSessionRecord:
        record = self.get_viva(viva_id)
        if not record:
            raise ValueError(f"Viva session '{viva_id}' not found.")

        if len(record.approved_questions) == 0:
            record.approved_questions = list(record.generated_questions)

        record.status = "PUBLISHED"
        self._sync_to_mongo(record)
        return record

    def get_published_vivas(self) -> List[VivaSessionRecord]:
        if self.sessions_col is not None:
            try:
                docs = list(self.sessions_col.find({"$or": [{"status": "PUBLISHED"}, {"approved_questions.0": {"$exists": True}}]}))
                results = []
                for d in docs:
                    d.pop("_id", None)
                    results.append(VivaSessionRecord(**d))
                return results
            except Exception as e:
                logger.error(f"Error reading published vivas from MongoDB: {e}")

        return [v for v in viva_sessions_db.values() if v.status == "PUBLISHED" or len(v.approved_questions) > 0]
    def delete_viva(self, viva_id: str) -> Dict[str, Any]:
        record = self.get_viva(viva_id)
        if not record:
            raise ValueError(f"Viva session '{viva_id}' not found.")

        doc_id = record.document_id

        # 1. Remove from in-memory dictionary
        if viva_id in viva_sessions_db:
            del viva_sessions_db[viva_id]

        # 2. Remove from MongoDB
        mongo_deleted = False
        if self.sessions_col is not None:
            res = self.sessions_col.delete_one({"viva_id": viva_id})
            mongo_deleted = res.deleted_count > 0

        # 3. Clean up associated vector embeddings in ChromaDB if document_id exists
        chunks_deleted = 0
        if doc_id:
            chunks_deleted = vector_store.delete_document_chunks(doc_id)

        logger.info(f"[VIVA DELETED] Session: '{viva_id}', DocID: '{doc_id}', Chunks Cleaned: {chunks_deleted}")
        return {
            "status": "SUCCESS",
            "message": f"Successfully deleted viva session '{viva_id}'.",
            "viva_id": viva_id,
            "document_id": doc_id,
            "mongo_deleted": mongo_deleted,
            "vector_chunks_deleted": chunks_deleted
        }

viva_creation_service = VivaCreationService()
