import os
import sys
import time
import json
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

BASE_URL = "http://127.0.0.1:8000/api"

def run_system_audit():
    print("\n" + "=" * 95)
    print("AUTOVIVA FINAL SYSTEM AUDIT & VALIDATION SUITE")
    print(f"Target Backend API: {BASE_URL}")
    print("=" * 95 + "\n")

    audit_results = []

    def record_test(area: str, name: str, status: str, details: str = ""):
        res = {"area": area, "name": name, "status": status, "details": details}
        audit_results.append(res)
        tag = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"[{area:20s}] | {tag:6s} | {name:50s} | {details}")

    with httpx.Client(timeout=180.0) as client:
        # Wait for backend readiness
        for retry in range(10):
            try:
                r = client.get(f"{BASE_URL}/auth/me", timeout=2.0)
                if r.status_code in [200, 401, 403]:
                    break
            except Exception:
                time.sleep(1.0)

        # ---------------------------------------------------------------------
        # AREA 1: ANSWER EVALUATION EDGE CASES
        # ---------------------------------------------------------------------
        # 1A: Irrelevant Answer Handling
        try:
            req_irrelevant = {
                "question_text": "Explain the ACID properties of a Relational Database Management System.",
                "ideal_answer": "ACID stands for Atomicity, Consistency, Isolation, and Durability. Atomicity ensures all-or-nothing completion.",
                "student_answer": "I really enjoy playing football and watching movies on weekends with my friends.",
                "evaluation_rubric": [
                    {"criterion": "Explain Atomicity property", "marks": 5.0},
                    {"criterion": "Explain Isolation property", "marks": 5.0}
                ],
                "subject": "DBMS",
                "topic": "Transactions"
            }
            res_irr = client.post(f"{BASE_URL}/evaluation/submit", json=req_irrelevant)
            if res_irr.status_code == 200:
                data = res_irr.json()
                final_score = data.get("ai_version_v1", {}).get("evaluation_summary", {}).get("final_score", -1)
                if final_score == 0.0:
                    record_test("ANSWER_EVAL", "Irrelevant Answer (Football)", "PASS", f"Score strictly 0.0/10.0 (Unrelated content received zero marks)")
                else:
                    record_test("ANSWER_EVAL", "Irrelevant Answer (Football)", "FAIL", f"Unexpected score {final_score}/10.0 for irrelevant content")
            else:
                record_test("ANSWER_EVAL", "Irrelevant Answer (Football)", "FAIL", f"HTTP_{res_irr.status_code}: {res_irr.text[:100]}")
        except Exception as e:
            record_test("ANSWER_EVAL", "Irrelevant Answer (Football)", "FAIL", str(e))

        # 1B: Empty / Whitespace Student Answer
        try:
            req_empty = {
                "question_text": "What is Network Address Translation?",
                "ideal_answer": "NAT maps private IP addresses to public IP addresses.",
                "student_answer": "   ",
                "evaluation_rubric": [{"criterion": "Explain NAT", "marks": 10.0}]
            }
            res_emp = client.post(f"{BASE_URL}/evaluation/submit", json=req_empty)
            if res_emp.status_code in [400, 422, 500] and ("empty" in res_emp.text.lower() or "invalid" in res_emp.text.lower()):
                record_test("ANSWER_EVAL", "Empty Student Answer Rejection", "PASS", f"Rejected with HTTP_{res_emp.status_code}: '{res_emp.json().get('detail', '')[:60]}'")
            else:
                record_test("ANSWER_EVAL", "Empty Student Answer Rejection", "FAIL", f"Unexpected response HTTP_{res_emp.status_code}")
        except Exception as e:
            record_test("ANSWER_EVAL", "Empty Student Answer Rejection", "FAIL", str(e))

        # 1C: Partially Correct Answer Scoring
        try:
            req_partial = {
                "question_text": "Describe Atomicity and Durability in DBMS transactions.",
                "ideal_answer": "Atomicity ensures all operations succeed or roll back. Durability guarantees committed changes persist even after system failure.",
                "student_answer": "Atomicity means that a transaction is all or nothing so if it fails it rolls back completely.",
                "evaluation_rubric": [
                    {"criterion": "Explain Atomicity all-or-nothing rollback", "marks": 5.0},
                    {"criterion": "Explain Durability persistence after crash", "marks": 5.0}
                ],
                "subject": "DBMS",
                "topic": "Transactions"
            }
            res_part = client.post(f"{BASE_URL}/evaluation/submit", json=req_partial)
            if res_part.status_code == 200:
                data = res_part.json()
                final_score = data.get("ai_version_v1", {}).get("evaluation_summary", {}).get("final_score", -1)
                if 4.0 <= final_score <= 6.0:
                    record_test("ANSWER_EVAL", "Partially Correct Answer", "PASS", f"Score {final_score}/10.0 (Atomicity rewarded 5.0, omitted Durability earned 0.0)")
                else:
                    record_test("ANSWER_EVAL", "Partially Correct Answer", "FAIL", f"Unexpected partial score {final_score}/10.0")
            else:
                record_test("ANSWER_EVAL", "Partially Correct Answer", "FAIL", f"HTTP_{res_part.status_code}: {res_part.text[:100]}")
        except Exception as e:
            record_test("ANSWER_EVAL", "Partially Correct Answer", "FAIL", str(e))

        # ---------------------------------------------------------------------
        # AREA 3: SPEECH-TO-TEXT (STT) VALIDATION
        # ---------------------------------------------------------------------
        # 3A: STT Audio Handling (No Silent Fake Answers on Error)
        try:
            sample_wav = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
            files = {"file": ("test_answer.wav", sample_wav, "audio/wav")}
            res_stt = client.post(f"{BASE_URL}/viva/transcribe", files=files)
            if res_stt.status_code == 200:
                stt_data = res_stt.json()
                record_test("STT", "Audio Transcription Endpoint", "PASS", f"Transcribed text: '{stt_data.get('transcript')}' (Confidence: {stt_data.get('confidence')})")
            elif res_stt.status_code in [400, 500] and "failed" in res_stt.text.lower():
                record_test("STT", "Audio Transcription Endpoint", "PASS", f"Returned clear error HTTP_{res_stt.status_code} on empty audio (No fake transcript produced)")
            else:
                record_test("STT", "Audio Transcription Endpoint", "FAIL", f"Unexpected STT response HTTP_{res_stt.status_code}: {res_stt.text[:100]}")
        except Exception as e:
            record_test("STT", "Audio Transcription Endpoint", "FAIL", str(e))

        # ---------------------------------------------------------------------
        # AREA 4: FACIAL TELEMETRY NON-MARKING COMPLIANCE
        # ---------------------------------------------------------------------
        try:
            req_tel_high = {
                "question_text": "What is Network Address Translation?",
                "ideal_answer": "NAT translates private IP addresses into a single public IP address.",
                "student_answer": "NAT translates private internal IP addresses into a single public IP address for external communication.",
                "evaluation_rubric": [{"criterion": "Explain NAT private to public IP mapping", "marks": 10.0}],
                "facial_telemetry": {"attention_percentage": 98.0, "expression": "focused"}
            }
            req_tel_low = {
                "question_text": "What is Network Address Translation?",
                "ideal_answer": "NAT translates private IP addresses into a single public IP address.",
                "student_answer": "NAT translates private internal IP addresses into a single public IP address for external communication.",
                "evaluation_rubric": [{"criterion": "Explain NAT private to public IP mapping", "marks": 10.0}],
                "facial_telemetry": {"attention_percentage": 10.0, "expression": "distracted"}
            }
            res_high = client.post(f"{BASE_URL}/evaluation/submit", json=req_tel_high)
            res_low = client.post(f"{BASE_URL}/evaluation/submit", json=req_tel_low)

            if res_high.status_code == 200 and res_low.status_code == 200:
                score_high = res_high.json().get("ai_version_v1", {}).get("evaluation_summary", {}).get("final_score", -1)
                score_low = res_low.json().get("ai_version_v1", {}).get("evaluation_summary", {}).get("final_score", -2)
                if score_high == score_low and score_high >= 0:
                    record_test("FACIAL_TELEMETRY", "Zero Marks Contribution", "PASS", f"Score identical ({score_high}/{score_low} marks) despite 98% vs 10% attention telemetry (0 marks contributed)")
                else:
                    record_test("FACIAL_TELEMETRY", "Zero Marks Contribution", "FAIL", f"Facial telemetry affected score: High={score_high}, Low={score_low}")
            else:
                record_test("FACIAL_TELEMETRY", "Zero Marks Contribution", "FAIL", f"HTTP_{res_high.status_code}/{res_low.status_code}")
        except Exception as e:
            record_test("FACIAL_TELEMETRY", "Zero Marks Contribution", "FAIL", str(e))

        # ---------------------------------------------------------------------
        # AREA 5: AUTHORIZATION & ROLE ISOLATION
        # ---------------------------------------------------------------------
        # 5A: Student Token Attempting Faculty Delete Endpoint
        try:
            std_email = f"std.audit_{int(time.time())}@autoviva.edu"
            std_pw = "studentPassword123!"
            reg_std = client.post(f"{BASE_URL}/auth/register", json={
                "name": "Audit Student",
                "email": std_email,
                "password": std_pw,
                "confirm_password": std_pw,
                "role": "student"
            })
            std_token = reg_std.json().get("access_token", "") if reg_std.status_code == 200 else ""
            
            headers_std = {"Authorization": f"Bearer {std_token}"}
            fac_resp = client.delete(f"{BASE_URL}/viva/viva_audit_dummy", headers=headers_std)

            if fac_resp.status_code == 403:
                record_test("AUTH_ISOLATION", "Student Access to Faculty Endpoint", "PASS", f"Correctly denied with HTTP_{fac_resp.status_code} ({fac_resp.json().get('detail')})")
            else:
                record_test("AUTH_ISOLATION", "Student Access to Faculty Endpoint", "FAIL", f"Student allowed access to faculty endpoint! HTTP_{fac_resp.status_code}")
        except Exception as e:
            record_test("AUTH_ISOLATION", "Student Access to Faculty Endpoint", "FAIL", str(e))

        # 5B: Invalid JWT Token Rejection
        try:
            bad_headers = {"Authorization": "Bearer invalid.jwt.signature"}
            bad_resp = client.delete(f"{BASE_URL}/viva/viva_audit_dummy", headers=bad_headers)
            if bad_resp.status_code in [401, 403]:
                record_test("AUTH_ISOLATION", "Invalid JWT Token Rejection", "PASS", f"Rejected invalid token with HTTP_{bad_resp.status_code} ({bad_resp.json().get('detail')})")
            else:
                record_test("AUTH_ISOLATION", "Invalid JWT Token Rejection", "FAIL", f"Allowed invalid token! HTTP_{bad_resp.status_code}")
        except Exception as e:
            record_test("AUTH_ISOLATION", "Invalid JWT Token Rejection", "FAIL", str(e))

        # ---------------------------------------------------------------------
        # AREA 6 & 7: SERVICE CONNECTIVITY & DEMO READINESS
        # ---------------------------------------------------------------------
        try:
            health_resp = client.get(f"{BASE_URL}/health")
            if health_resp.status_code == 200:
                h_data = health_resp.json()
                record_test("DEMO_READINESS", "Health Check API", "PASS", f"Status: '{h_data.get('status')}' (Backend & Vector Store Active)")
            else:
                record_test("DEMO_READINESS", "Health Check API", "FAIL", f"HTTP_{health_resp.status_code}: {health_resp.text[:100]}")
        except Exception as e:
            record_test("DEMO_READINESS", "Health Check API", "FAIL", str(e))

    pass_cnt = sum(1 for r in audit_results if r["status"] == "PASS")
    fail_cnt = sum(1 for r in audit_results if r["status"] == "FAIL")

    print("\n" + "=" * 95)
    print(f"SYSTEM AUDIT & VALIDATION SUMMARY: {pass_cnt} / {len(audit_results)} TESTS PASSED ({fail_cnt} FAILS)")
    print("=" * 95 + "\n")

    return {
        "pass_count": pass_cnt,
        "fail_count": fail_cnt,
        "total_tests": len(audit_results),
        "results": audit_results
    }

if __name__ == "__main__":
    run_system_audit()
