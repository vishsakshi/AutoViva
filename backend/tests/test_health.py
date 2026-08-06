import pytest
import httpx
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "VivaBot Backend"

@pytest.mark.asyncio
async def test_route_groups():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        faculty_res = await client.get("/api/faculty/dashboard")
        assert faculty_res.status_code == 200
        
        student_res = await client.get("/api/student/dashboard")
        assert student_res.status_code == 200
