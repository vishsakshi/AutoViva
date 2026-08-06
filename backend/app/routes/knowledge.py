from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

class SearchQueryRequest(BaseModel):
    query: str
    top_k: int = 3
    subject: Optional[str] = None
    topic: Optional[str] = None

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    subject: str = Form(...),
    topic: str = Form("General")
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = knowledge_service.process_and_index_document(
            file_bytes=content,
            filename=file.filename,
            subject=subject,
            topic=topic
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/search")
async def search_knowledge(search_req: SearchQueryRequest):
    if not search_req.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    result = knowledge_service.search_knowledge_base(
        query=search_req.query,
        top_k=search_req.top_k,
        subject=search_req.subject,
        topic=search_req.topic
    )
    return result

@router.get("/stats")
async def knowledge_stats():
    return vector_store.get_stats()
