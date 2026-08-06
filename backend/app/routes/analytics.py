from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("")
async def analytics_stub():
    return {"message": "Analytics route module active", "stats": {"total_vivas": 0, "avg_score": 0.0}}
