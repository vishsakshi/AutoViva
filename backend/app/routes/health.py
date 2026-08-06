from fastapi import APIRouter
from app.core.db import get_database

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    db = get_database()
    db_status = "disconnected"
    if db is not None:
        try:
            await db.command("ping")
            db_status = "connected"
        except Exception:
            db_status = "error"

    return {
        "status": "ok",
        "service": "VivaBot Backend",
        "database": db_status
    }
