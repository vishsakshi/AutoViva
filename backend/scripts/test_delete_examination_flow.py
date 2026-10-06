import sys
import os

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from fastapi.testclient import TestClient
from app.main import app
from app.services.viva_creation_service import viva_creation_service, viva_sessions_db, VivaSessionRecord

def test_delete_examination_complete_flow():
    print("=" * 80)
    print("AUTOVIVA PUBLISHED EXAMINATION DELETION INTEGRITY SUITE")
    print("=" * 80)

    with TestClient(app) as client:
        # STEP 1: Login as Faculty
        print("\n[STEP 1]: Login as Faculty (`faculty@autoviva.edu`)")
        fac_res = client.post("/api/auth/login", json={
            "email": "faculty@autoviva.edu",
            "password": "faculty123"
        })
        assert fac_res.status_code == 200, f"Faculty login failed: {fac_res.text}"
        fac_token = fac_res.json()["access_token"]
        print(f"Faculty JWT Token Obtained: {fac_token[:25]}...")

        # STEP 2: Login as Student
        print("\n[STEP 2]: Login as Student (`student@autoviva.edu`)")
        std_res = client.post("/api/auth/login", json={
            "email": "student@autoviva.edu",
            "password": "student123"
        })
        assert std_res.status_code == 200, f"Student login failed: {std_res.text}"
        std_token = std_res.json()["access_token"]
        print(f"Student JWT Token Obtained: {std_token[:25]}...")

        # STEP 3: Create a Staging Published Viva Session
        print("\n[STEP 3]: Creating a Published Viva Session for Deletion Test")
        test_viva_id = "viva_test_del_9999"
        test_doc_id = "doc_test_del_9999"
        test_record = VivaSessionRecord(
            viva_id=test_viva_id,
            title="Deletion Test viva",
            subject="Software Architecture Verification",
            course_code="CS9999",
            topic="Software Architecture",
            question_count=1,
            duration_minutes=15,
            batch="Batch A",
            created_at="2026-09-27 18:50:00",
            document_id=test_doc_id,
            status="PUBLISHED",
            approved_questions=[{"id": "q1", "question": "What is unit testing?"}]
        )
        viva_sessions_db[test_viva_id] = test_record
        viva_creation_service._sync_to_mongo(test_record)
        print(f"Published Viva Created: ID='{test_viva_id}', Code='CS9999'")

        # Verify it appears in published list
        pub_list = client.get("/api/viva/published").json()
        assert any(v["viva_id"] == test_viva_id for v in pub_list), "Test viva missing from published list!"
        print("-> Confirmed test viva is present in GET /api/viva/published")

        # STEP 4: Test DELETE without Authorization Header (Should return 401)
        print("\n[STEP 4]: DELETE Request with NO Authorization Header")
        res_no_auth = client.delete(f"/api/viva/{test_viva_id}")
        print(f"Status Code: {res_no_auth.status_code}")
        print(f"Detail: {res_no_auth.json().get('detail')}")
        assert res_no_auth.status_code == 401
        assert "Missing or invalid authorization header" in res_no_auth.json()["detail"]
        print("-> PASS: Correctly rejected unauthenticated request with 401 Unauthorized!")

        # STEP 5: Test DELETE with Student Token (Should return 403)
        print("\n[STEP 5]: DELETE Request with Student Authorization Token")
        res_student_del = client.delete(
            f"/api/viva/{test_viva_id}",
            headers={"Authorization": f"Bearer {std_token}"}
        )
        print(f"Status Code: {res_student_del.status_code}")
        print(f"Detail: {res_student_del.json().get('detail')}")
        assert res_student_del.status_code == 403
        assert "Only faculty members can delete" in res_student_del.json()["detail"]
        print("-> PASS: Correctly rejected non-faculty request with 403 Forbidden!")

        # STEP 6: Test DELETE with Valid Faculty Token (Should return 200 OK)
        print("\n[STEP 6]: DELETE Request with Valid Faculty Token")
        res_fac_del = client.delete(
            f"/api/viva/{test_viva_id}",
            headers={"Authorization": f"Bearer {fac_token}"}
        )
        print(f"Status Code: {res_fac_del.status_code}")
        print(f"Response Body: {res_fac_del.json()}")
        assert res_fac_del.status_code == 200
        assert res_fac_del.json()["status"] == "SUCCESS"
        assert res_fac_del.json()["viva_id"] == test_viva_id
        print("-> PASS: Deletion request succeeded with HTTP 200 OK!")

        # STEP 7: Verify viva is removed from MongoDB and Published List
        print("\n[STEP 7]: Verifying Removal from Published List & Database")
        pub_list_after = client.get("/api/viva/published").json()
        assert not any(v["viva_id"] == test_viva_id for v in pub_list_after), "Viva still found in published list!"
        print("-> PASS: Deleted examination no longer appears in GET /api/viva/published!")

        # STEP 8: Test DELETE for Non-Existent Viva (Should return 404)
        print("\n[STEP 8]: DELETE Request for Non-Existent Viva ID")
        res_404 = client.delete(
            f"/api/viva/non_existent_id_12345",
            headers={"Authorization": f"Bearer {fac_token}"}
        )
        print(f"Status Code: {res_404.status_code}")
        assert res_404.status_code == 404
        print("-> PASS: Non-existent viva deletion returns 404 Not Found!")

    print("\n" + "=" * 80)
    print("ALL 8 PUBLISHED EXAMINATION DELETION INTEGRITY TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    test_delete_examination_complete_flow()
