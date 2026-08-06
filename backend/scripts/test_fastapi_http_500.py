import json
from fastapi.testclient import TestClient
from app.main import app

def test_fastapi_register_endpoint():
    client = TestClient(app)

    print("Testing HTTP POST /api/auth/register via FastAPI TestClient...")

    payload = {
        "name": "Sakshi",
        "email": "sakshi_test_http@gmail.com",
        "password": "12345678",
        "confirm_password": "12345678",
        "role": "student"
    }

    res = client.post("/api/auth/register", json=payload)
    print(f"HTTP Status Code: {res.status_code}")
    print(f"Response Body: {res.text}")

    assert res.status_code in [200, 201], f"Expected 200/201 but got {res.status_code}: {res.text}"

if __name__ == "__main__":
    test_fastapi_register_endpoint()
