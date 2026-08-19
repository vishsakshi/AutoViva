import time
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List

from app.services.viva_creation_service import (
    viva_creation_service,
    VivaCreateRequest,
    VivaSessionRecord
)
from app.services.knowledge_service import knowledge_service

router = APIRouter(prefix="/viva", tags=["Faculty Viva Pipeline"])

@router.post("/create", response_model=VivaSessionRecord)
def create_viva(req: VivaCreateRequest):
    try:
        return viva_creation_service.create_viva(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create viva session: {str(e)}")

@router.post("/upload-document")
def upload_viva_document(viva_id: str = Form(...), file: UploadFile = File(...)):
    try:
        record = viva_creation_service.get_viva(viva_id)
        subject_name = record.subject if record else "Academic Viva Syllabus"
        topic_name = record.topic if record else "General"

        content = file.file.read()
        file_size_bytes = len(content)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        if file_size_mb == 0:
            file_size_mb = round(file_size_bytes / 1024, 1)
            size_str = f"{file_size_mb} KB"
        else:
            size_str = f"{file_size_mb} MB"

        res = knowledge_service.process_and_store_document(
            file_bytes=content,
            filename=file.filename,
            subject=subject_name,
            topic=topic_name,
            viva_id=viva_id
        )
        
        doc_id = res.get("document_id")
        topic_map = res.get("topic_map")
        updated_record = viva_creation_service.add_uploaded_file(
            viva_id=viva_id,
            filename=file.filename,
            document_id=doc_id,
            topic_map=topic_map
        )
        upload_time = time.strftime("%I:%M %p, %b %d")

        return {
            "status": "success",
            "viva_id": viva_id,
            "document_id": doc_id,
            "filename": file.filename,
            "file_size": size_str,
            "upload_time": upload_time,
            "chunks_processed": res.get("chunks_processed", 0),
            "topic_map": topic_map,
            "viva_record": updated_record
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/{viva_id}/generate-questions", response_model=VivaSessionRecord)
def generate_viva_questions(viva_id: str):
    try:
        return viva_creation_service.generate_questions_for_viva(viva_id)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@router.post("/{viva_id}/review-question", response_model=VivaSessionRecord)
def review_viva_question(viva_id: str, question_id: str = Form(...), action: str = Form(...), edited_text: Optional[str] = Form(None)):
    try:
        return viva_creation_service.review_viva_question(viva_id, question_id, action, edited_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{viva_id}/publish", response_model=VivaSessionRecord)
def publish_viva(viva_id: str):
    try:
        return viva_creation_service.publish_viva(viva_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/published", response_model=List[VivaSessionRecord])
def get_published_vivas():
    return viva_creation_service.get_published_vivas()

@router.get("/all", response_model=List[VivaSessionRecord])
def get_all_vivas():
    return list(viva_creation_service.viva_sessions_db.values())
