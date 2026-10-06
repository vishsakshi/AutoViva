from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field

from app.services.speech_service import speech_to_text_service

router = APIRouter(prefix="/viva", tags=["Student Viva Module"])


class TranscribeResponse(BaseModel):
    status: str = "success"
    filename: str
    transcript: str
    confidence: float = 0.96


class ActiveQuestionSchema(BaseModel):
    question_id: str
    subject: str
    topic: str
    question_text: str
    ideal_answer: str
    allocated_marks: float = 10.0
    time_limit_seconds: int = 120
    # Rubric passed through so the frontend uses the real faculty-set criteria
    evaluation_rubric: List[Dict[str, Any]] = []


@router.get("/session/{viva_id}")
async def get_viva_session_detail(viva_id: str):
    """Returns full published viva session details by ID."""
    from app.services.viva_creation_service import viva_creation_service
    record = viva_creation_service.get_viva(viva_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Viva session '{viva_id}' not found.")
    return record


@router.get("/active-questions", response_model=List[ActiveQuestionSchema])
async def get_active_viva_questions(viva_id: Optional[str] = None):
    """
    Returns ONLY the faculty-approved questions for a specific published viva session.
    - When viva_id is supplied: returns approved_questions for that viva ONLY.
      Rejected and unapproved questions are never included.
      Raises 404 if the viva does not exist, 422 if it has no approved questions yet.
    - When viva_id is omitted: returns approved questions from the most recently
      published viva (latest-first), so the student dashboard generic link still works.
    """
    from app.services.viva_creation_service import viva_creation_service

    def _extract_rubric(q: dict) -> List[Dict[str, Any]]:
        """Extract rubric from question dict, normalising key names."""
        raw = q.get("evaluation_rubric") or q.get("rubric") or []
        result = []
        for r in raw:
            if isinstance(r, dict):
                criterion = r.get("criterion") or r.get("criterion_text") or ""
                marks = float(r.get("marks") or r.get("allocated_marks") or 3.0)
                if criterion:
                    result.append({"criterion": criterion, "marks": marks})
        return result

    def _build_schema(q: dict, viva) -> ActiveQuestionSchema:
        return ActiveQuestionSchema(
            question_id=q.get("question_id", ""),
            subject=viva.subject,
            topic=viva.topic,
            question_text=q.get("question_text") or q.get("question", ""),
            ideal_answer=q.get("ideal_answer", ""),
            allocated_marks=float(q.get("allocated_marks") or q.get("marks") or q.get("total_marks") or 10.0),
            time_limit_seconds=120,
            evaluation_rubric=_extract_rubric(q),
        )

    # --- Path A: caller supplied a specific viva_id ---
    if viva_id:
        viva = viva_creation_service.get_viva(viva_id)
        if not viva:
            raise HTTPException(
                status_code=404,
                detail=f"Viva session '{viva_id}' not found."
            )
        if not viva.approved_questions:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Viva '{viva_id}' has no faculty-approved questions yet. "
                    "Please complete the faculty review and publish the viva before students can attempt it."
                )
            )
        return [_build_schema(q, viva) for q in viva.approved_questions]

    # --- Path B: no viva_id — use the most recently published viva ---
    published_vivas = viva_creation_service.get_published_vivas()
    if published_vivas:
        viva = published_vivas[-1]
        if viva.approved_questions:
            return [_build_schema(q, viva) for q in viva.approved_questions]

    return []


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_file(file: UploadFile = File(...)):
    """
    OpenAI Whisper Speech-to-Text Endpoint.
    Transcribes student recorded microphone audio into text.
    Returns high-accuracy transcript for student verification.
    """
    try:
        audio_bytes = await file.read()
        if not audio_bytes or len(audio_bytes) < 50:
            raise HTTPException(status_code=400, detail="Audio file payload is empty or invalid.")

        transcript = speech_to_text_service.transcribe_audio_bytes(
            audio_bytes, filename=file.filename or "recording.webm"
        )

        return TranscribeResponse(
            status="success",
            filename=file.filename or "recording.webm",
            transcript=transcript,
            confidence=0.96,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech transcription failed: {str(e)}")
