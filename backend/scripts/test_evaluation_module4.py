import json
from app.models.evaluation_module import EvaluateAnswerRequest
from app.models.question_gen import RubricCriterion
from app.models.review_module import FacultyAction, FacultyOverrideRequest, EvaluationStatus
from app.services.evaluation_review_service import evaluation_review_service

def run_module4_unit_tests():
    print("=" * 80)
    print("VIVABOT PHASE 4 - MODULE 4: FACULTY REVIEW & PIPELINE INTEGRATION TEST SUITE")
    print("=" * 80)

    q_text = "Describe how Network Address Translation (NAT) and NAPT allow multiple internal private IP devices to communicate over a single public IP address."
    ideal_ans = "NAT maps private internal IP addresses to a public external IP. NAPT (Port Address Translation) extends this by mapping unique source port numbers alongside the public IP address, allowing thousands of internal sockets to share a single public IP. NAT also hides internal IP topologies for security."
    rubric = [
        RubricCriterion(criterion="Distinction between private internal and public external IP addresses", marks=3.0),
        RubricCriterion(criterion="Detailed mechanism of NAPT port mapping for inbound/outbound packets", marks=4.0),
        RubricCriterion(criterion="Translation table management and security benefits", marks=3.0)
    ]
    std_ans = "Private IPs are used inside local networks while public IPs are routed on the internet. NAPT uses port numbers for mapping connections."

    req = EvaluateAnswerRequest(
        question_text=q_text,
        ideal_answer=ideal_ans,
        evaluation_rubric=rubric,
        student_answer=std_ans,
        subject="Computer Networks",
        topic="IP Addressing & NAT"
    )

    # 1. Pipeline Submission & Staging as PENDING_REVIEW
    print("\n--- STEP 1: End-to-End Pipeline Submission ---")
    rec1 = evaluation_review_service.submit_student_answer_pipeline(req, student_id="std_10293")
    eval_id = rec1.evaluation_id

    print(f"Evaluation ID: {eval_id}")
    print(f"Status: {rec1.status}")
    print(f"Current Version: v{rec1.current_version}")
    print(f"AI Score (v1): {rec1.ai_version_v1.evaluation_summary.final_score} / 10.0")

    assert rec1.status == EvaluationStatus.PENDING_REVIEW
    assert rec1.current_version == 1
    assert rec1.faculty_version_v2 is None
    print("[PASSED] STEP 1 PASSED: Pipeline submission correctly staged as PENDING_REVIEW.")

    # 2. Test 1: Faculty Approves Without Edits
    print("\n--- TEST SCENARIO 1: Faculty Approves Without Edits ---")
    rec_approved = evaluation_review_service.approve_evaluation(eval_id, faculty_comment="Excellent AI evaluation.")
    print(f"Status: {rec_approved.status}")
    print(f"Audit Logs Count: {len(rec_approved.audit_history)}")
    print(f"Latest Log Action: {rec_approved.audit_history[-1].faculty_action}")

    assert rec_approved.status == EvaluationStatus.APPROVED
    assert rec_approved.current_version == 1
    assert rec_approved.audit_history[-1].faculty_action == FacultyAction.APPROVE
    print("[PASSED] TEST SCENARIO 1 PASSED: Approved without edits.")

    # 3. Test 2 & 3: Faculty Overrides One Criterion & Total Score (Creates Version 2)
    print("\n--- TEST SCENARIO 2 & 3: Faculty Overrides Criterion Marks & Score ---")
    ai_v1_score = rec_approved.ai_version_v1.evaluation_summary.final_score

    override_req = FacultyOverrideRequest(
        action=FacultyAction.OVERRIDE,
        criterion_score_overrides={"c2": 4.0}, # Upgrade NAPT port mapping from 3.0 to 4.0
        new_score=9.25,
        faculty_comment="Upgraded NAPT criterion mark after manual review of student explanation.",
        reason_for_change="Student demonstrated sufficient understanding of port multiplexing."
    )

    rec_overridden = evaluation_review_service.override_evaluation(eval_id, override_req)

    print(f"Status: {rec_overridden.status}")
    print(f"Current Version: v{rec_overridden.current_version}")
    print(f"Original AI Score (v1): {rec_overridden.ai_version_v1.evaluation_summary.final_score}")
    print(f"New Faculty Score (v2): {rec_overridden.faculty_version_v2.evaluation_summary.final_score}")
    print(f"Audit Logs Count: {len(rec_overridden.audit_history)}")

    # IMMUTABILITY ASSERTIONS
    assert rec_overridden.status == EvaluationStatus.OVERRIDDEN
    assert rec_overridden.current_version == 2
    assert rec_overridden.ai_version_v1.evaluation_summary.final_score == ai_v1_score # AI v1 IMMUTABLE
    assert rec_overridden.faculty_version_v2.evaluation_summary.final_score == 9.25 # v2 updated
    assert rec_overridden.audit_history[-1].faculty_action == FacultyAction.OVERRIDE
    print("[PASSED] TEST SCENARIOS 2 & 3 PASSED: Version 1 preserved immutable; Version 2 created.")

    # 4. Test 4: Faculty Adds Comments & History Retrieval
    print("\n--- TEST SCENARIO 4: Faculty Audit Trail & History Inspection ---")
    history = evaluation_review_service.get_evaluation_history(eval_id)
    print(f"Total Audit History Logs for {eval_id}: {len(history)}")
    for idx, log in enumerate(history, 1):
        print(f"  Log #{idx}: Action={log.faculty_action} | PrevScore={log.previous_score} -> NewScore={log.new_score}")
        print(f"          Reason: \"{log.reason_for_change}\" | Comment: \"{log.faculty_comment}\"")

    assert len(history) == 2
    print("[PASSED] TEST SCENARIO 4 PASSED: Complete audit trail verified.")

    # 5. Test 5: Faculty Rejects Evaluation
    print("\n--- TEST SCENARIO 5: Faculty Rejects Evaluation ---")
    rec2 = evaluation_review_service.submit_student_answer_pipeline(req, student_id="std_99999")
    eval_id2 = rec2.evaluation_id

    rec_rejected = evaluation_review_service.reject_evaluation(eval_id2, reason_for_change="Spam answer submitted", faculty_comment="Student submitted non-academic text.")
    print(f"Status: {rec_rejected.status}")
    print(f"Audit Logs Count: {len(rec_rejected.audit_history)}")
    assert rec_rejected.status == EvaluationStatus.REJECTED
    assert rec_rejected.audit_history[-1].new_score == 0.0
    print("[PASSED] TEST SCENARIO 5 PASSED: Rejection recorded cleanly.")

    print("\n--- SAMPLE MODULE 4 FULL RECORD WITH VERSION HISTORY & AUDIT TRAIL ---")
    sample_json = rec_overridden.model_dump()
    print(json.dumps(sample_json, indent=2)[:600] + "\n...[truncated for display]...")

    print("\n" + "=" * 80)
    print("ALL MODULE 4 INTEGRATION TESTS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_module4_unit_tests()
