from fastapi import APIRouter

router = APIRouter(prefix="/student", tags=["Student"])

@router.get("/dashboard")
async def student_dashboard_stub():
    return {
        "message": "Student route group active",
        "features": ["upcoming_vivas", "join_viva", "view_results"]
    }
