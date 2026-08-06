from fastapi import APIRouter

router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("/dashboard")
async def faculty_dashboard_stub():
    return {
        "message": "Faculty route group active",
        "features": ["create_viva", "manage_questions", "view_evaluations", "analytics"]
    }
