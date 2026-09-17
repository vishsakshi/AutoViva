from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from app.models.evaluation_module import EvaluateAnswerRequest, EvaluationModule1Response
from app.models.scoring_module import ScoringModule2Response
from app.models.feedback_module import GenerateFeedbackRequest, FeedbackModule3Response
from app.models.review_module import (
    FullEvaluationRecord,
    FacultyOverrideRequest,
    FacultyAuditLogEntry
)
from app.services.evaluation_engine import evaluation_engine_module1
from app.services.scoring_engine import scoring_engine_module2
from app.services.feedback_engine import feedback_engine_module3
from app.services.evaluation_review_service import evaluation_review_service

router = APIRouter(prefix="/evaluation", tags=["Answer Evaluation Engine"])

@router.post("/evaluate-raw", response_model=EvaluationModule1Response)
async def evaluate_answer_raw(req: EvaluateAnswerRequest):
    """
    Module 1: Evaluation API
    Accepts Question, Ideal Answer, Rubric, and Student Answer.
    Returns ONLY structured JSON classification.
    """
    try:
        result = evaluation_engine_module1.evaluate_answer_module1(req)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.post("/score-module2", response_model=ScoringModule2Response)
async def score_evaluation_module2(module1_res: EvaluationModule1Response):
    """
    Module 2: Standalone Deterministic Scoring Engine
    Receives ONLY Module 1 outputs and calculates numerical marks deterministically.
    Does NOT call any LLM.
    """
    try:
        scoring_res = scoring_engine_module2.calculate_scores(
            evaluation_id=module1_res.evaluation_id,
            criterion_evaluations=module1_res.criterion_evaluations
        )
        return scoring_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")

@router.post("/feedback-module3", response_model=FeedbackModule3Response)
async def generate_feedback_module3(req: GenerateFeedbackRequest):
    """
    Module 3: Evidence Validation & Explainable Feedback Engine
    Receives Module 1 + Module 2 outputs, validates verbatim evidence,
    and constructs structured explainable feedback.
    Preserves exact marks from Module 2 without modifications.
    """
    try:
        feedback_res = feedback_engine_module3.generate_feedback_report(req)
        return feedback_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback generation failed: {str(e)}")

# ==================== MODULE 4: FACULTY REVIEW & PIPELINE INTEGRATION ENDPOINTS ====================

@router.post("/submit", response_model=FullEvaluationRecord)
async def submit_evaluation_pipeline(req: EvaluateAnswerRequest):
    """
    End-to-End Pipeline Submission:
    Executes Module 1 -> Module 2 -> Module 3 and stages as PENDING_REVIEW.
    """
    try:
        record = evaluation_review_service.submit_student_answer_pipeline(req)
        return record
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

@router.get("/pending", response_model=List[FullEvaluationRecord])
async def get_pending_evaluations():
    """GET all evaluations pending faculty review."""
    return evaluation_review_service.get_pending_evaluations()

@router.get("/all", response_model=List[FullEvaluationRecord])
async def get_all_evaluations():
    """GET all evaluations."""
    return evaluation_review_service.get_all_evaluations()

@router.get("/{eval_id}", response_model=FullEvaluationRecord)
async def get_evaluation_details(eval_id: str):
    """GET details of a specific evaluation including AI v1, Faculty v2, and Audit History."""
    record = evaluation_review_service.get_evaluation_by_id(eval_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evaluation '{eval_id}' not found.")
    return record

@router.post("/{eval_id}/approve", response_model=FullEvaluationRecord)
async def faculty_approve(eval_id: str, comment: str = ""):
    """POST Faculty Approval without score edits."""
    try:
        return evaluation_review_service.approve_evaluation(eval_id, faculty_comment=comment)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.post("/{eval_id}/reject", response_model=FullEvaluationRecord)
async def faculty_reject(eval_id: str, reason: str = "Unsatisfactory", comment: str = ""):
    """POST Faculty Rejection."""
    try:
        return evaluation_review_service.reject_evaluation(eval_id, reason_for_change=reason, faculty_comment=comment)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.post("/{eval_id}/override", response_model=FullEvaluationRecord)
async def faculty_override(eval_id: str, req: FacultyOverrideRequest):
    """
    POST Faculty Override:
    Creates Version 2 with modified scores while preserving AI Version 1 intact.
    Logs audit entry.
    """
    try:
        return evaluation_review_service.override_evaluation(eval_id, req)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.get("/{eval_id}/history", response_model=List[FacultyAuditLogEntry])
async def get_evaluation_history(eval_id: str):
    """GET evaluation audit logs and action history."""
    record = evaluation_review_service.get_evaluation_by_id(eval_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evaluation '{eval_id}' not found.")
    return record.audit_history



