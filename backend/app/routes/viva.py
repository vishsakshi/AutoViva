from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field

from app.services.speech_service import speech_to_text_service
from app.services.question_generator import question_generator_engine

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

@router.get("/active-questions", response_model=List[ActiveQuestionSchema])
async def get_active_viva_questions():
    """Returns active approved questions for student viva examination."""
    bank = question_generator_engine.approved_question_bank
    if not bank:
        # Provide default high-quality viva questions if bank is empty
        return [
            ActiveQuestionSchema(
                question_id="vq_cn_nat_001",
                subject="Computer Networks",
                topic="IP Addressing & NAT",
                question_text="Describe how Network Address Translation (NAT) and NAPT allow multiple internal private IP devices to communicate over a single public IP address.",
                ideal_answer="NAT maps private internal IP addresses to a public external IP. NAPT extends this by mapping unique source port numbers alongside the public IP address, allowing thousands of internal sockets to share a single public IP.",
                allocated_marks=10.0,
                time_limit_seconds=120
            ),
            ActiveQuestionSchema(
                question_id="vq_dbms_acid_002",
                subject="DBMS",
                topic="Transactions & ACID",
                question_text="Explain the ACID properties of a Relational Database Management System (DBMS) and describe how Atomicity and Isolation ensure transaction reliability.",
                ideal_answer="ACID stands for Atomicity, Consistency, Isolation, and Durability. Atomicity ensures all-or-nothing completion, while Isolation prevents concurrent transaction interference.",
                allocated_marks=10.0,
                time_limit_seconds=120
            )
        ]

    active_list = []
    for q_id, q_item in bank.items():
        active_list.append(
            ActiveQuestionSchema(
                question_id=q_id,
                subject=q_item.subject,
                topic=q_item.topic,
                question_text=q_item.question_text,
                ideal_answer=q_item.ideal_answer,
                allocated_marks=10.0,
                time_limit_seconds=120
            )
        )
    return active_list

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

        transcript = speech_to_text_service.transcribe_audio_bytes(audio_bytes, filename=file.filename or "recording.webm")

        return TranscribeResponse(
            status="success",
            filename=file.filename or "recording.webm",
            transcript=transcript,
            confidence=0.96
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech transcription failed: {str(e)}")
