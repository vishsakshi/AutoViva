import sys
import os

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_service import auth_service
from app.models.auth import UserLoginRequest

def verify_backend_integrity():
    print("=" * 80)
    print("AUTOVIVA LOCAL BACKEND INTEGRITY & LOGIN VERIFICATION SUITE")
    print("=" * 80)

    with TestClient(app) as client:
        # TEST 1: Health Endpoint
        print("\n[TEST 1]: GET /api/health")
        res_health = client.get("/api/health")
        print(f"Status Code: {res_health.status_code}")
        print(f"Response: {res_health.json()}")
        assert res_health.status_code == 200, f"Expected 200, got {res_health.status_code}"
        assert res_health.json()["status"] == "ok"
        assert res_health.json()["database"] == "connected"
        print("-> PASS: Health check passed with active database connection!")

        # TEST 2: Student Login
        print("\n[TEST 2]: POST /api/auth/login (Student)")
        student_payload = {
            "email": "student@autoviva.edu",
            "password": "student123"
        }
        res_student = client.post("/api/auth/login", json=student_payload)
        print(f"Status Code: {res_student.status_code}")
        print(f"Response User: {res_student.json().get('user')}")
        assert res_student.status_code == 200, f"Expected 200, got {res_student.status_code}: {res_student.text}"
        assert "access_token" in res_student.json()
        assert res_student.json()["user"]["role"] == "student"
        print("-> PASS: Student login authenticated successfully!")

        # TEST 3: Faculty Login
        print("\n[TEST 3]: POST /api/auth/login (Faculty)")
        faculty_payload = {
            "email": "faculty@autoviva.edu",
            "password": "faculty123"
        }
        res_faculty = client.post("/api/auth/login", json=faculty_payload)
        print(f"Status Code: {res_faculty.status_code}")
        print(f"Response User: {res_faculty.json().get('user')}")
        assert res_faculty.status_code == 200, f"Expected 200, got {res_faculty.status_code}: {res_faculty.text}"
        assert "access_token" in res_faculty.json()
        assert res_faculty.json()["user"]["role"] == "faculty"
        print("-> PASS: Faculty login authenticated successfully!")

        # TEST 4: Invalid Password Login (400 check)
        print("\n[TEST 4]: POST /api/auth/login (Invalid Password)")
        invalid_pwd_payload = {
            "email": "student@autoviva.edu",
            "password": "WrongPassword123"
        }
        res_inv = client.post("/api/auth/login", json=invalid_pwd_payload)
        print(f"Status Code: {res_inv.status_code}")
        print(f"Response Detail: {res_inv.json().get('detail')}")
        assert res_inv.status_code == 400
        print("-> PASS: Invalid password returns 400 Bad Request!")

        # TEST 5: User Registration
        print("\n[TEST 5]: POST /api/auth/register (New User)")
        import time
        unique_email = f"test.user_{int(time.time())}@university.edu"
        reg_payload = {
            "name": "Integration Test Student",
            "email": unique_email,
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "student"
        }
        res_reg = client.post("/api/auth/register", json=reg_payload)
        print(f"Status Code: {res_reg.status_code}")
        print(f"Registered User: {res_reg.json().get('user')}")
        assert res_reg.status_code in [200, 201]
        assert "access_token" in res_reg.json()
        print("-> PASS: User registration succeeded!")

        # TEST 6: Login with Newly Registered User
        print("\n[TEST 6]: POST /api/auth/login (Newly Registered User)")
        res_new_login = client.post("/api/auth/login", json={
            "email": unique_email,
            "password": "Password123!"
        })
        print(f"Status Code: {res_new_login.status_code}")
        assert res_new_login.status_code == 200
        print("-> PASS: Newly registered user logged in successfully!")

    print("\n" + "=" * 80)
    print("ALL 6 BACKEND & AUTHENTICATION INTEGRITY TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    verify_backend_integrity()
