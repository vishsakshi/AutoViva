from typing import Optional, List
from fastapi import APIRouter, HTTPException, status
from app.models.question_gen import (
    GenerateQuestionsRequest,
    ReviewActionRequest,
    VivaQuestionSchema
)
from app.services.question_generator import question_generator_engine

router = APIRouter(prefix="/questions", tags=["Questions Engine"])

@router.post("/generate")
async def generate_questions(req: GenerateQuestionsRequest):
    if not req.subject.strip() or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Subject and topic must not be empty.")

    result = question_generator_engine.generate_questions(req)
    if result["status"] == "INSUFFICIENT_CONTEXT":
        raise HTTPException(status_code=422, detail=result["message"])
    return result

@router.get("/drafts")
async def get_draft_questions():
    drafts = list(question_generator_engine.draft_questions.values())
    return {"total_drafts": len(drafts), "drafts": drafts}

@router.post("/review")
async def review_question(req: ReviewActionRequest):
    result = question_generator_engine.review_draft_question(
        question_id=req.question_id,
        action=req.action,
        edited_q=req.edited_question
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.get("/bank")
async def get_question_bank(subject: Optional[str] = None):
    bank = list(question_generator_engine.approved_question_bank.values())
    if subject:
        bank = [q for q in bank if q.subject.lower() == subject.lower()]
    return {"total_approved": len(bank), "questions": bank}

@router.get("/logs")
async def get_generation_logs():
    logs = question_generator_engine.generation_logs
    return {"total_logs": len(logs), "logs": logs}

