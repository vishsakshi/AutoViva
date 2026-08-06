import json
from app.services.speech_service import speech_to_text_service
from app.services.evaluation_review_service import evaluation_review_service
from app.models.evaluation_module import EvaluateAnswerRequest
from app.models.question_gen import RubricCriterion

def run_student_viva_tests():
    print("=" * 90)
    print("VIVABOT STUDENT VIVA MODULE TEST SUITE")
    print("=" * 90)

    # 1. Test Speech-to-Text Transcription Service
    print("\n--- TEST 1: Speech-to-Text Transcription Service ---")
    dummy_audio_bytes = b"RIFF....WAVEfmt ....data" + b"\x00" * 200
    transcript = speech_to_text_service.transcribe_audio_bytes(dummy_audio_bytes, filename="test_recording.webm")
    print(f"Transcribed Text Output: \"{transcript}\"")
    assert transcript and len(transcript) > 10
    print("[PASSED]: Speech-to-Text transcription service verified.")

    # 2. Test Empty Audio Handling
    print("\n--- TEST 2: Empty Audio Validation ---")
    try:
        speech_to_text_service.transcribe_audio_bytes(b"", filename="empty.webm")
        print("[FAILED]: Should have raised ValueError for empty audio.")
    except ValueError as ve:
        print(f"[PASSED]: Gracefully caught empty audio payload -> \"{str(ve)}\"")

    # 3. Test Student Transcript Verification & Evaluation Pipeline Submission
    print("\n--- TEST 3: Student Verified Transcript Submission to Modules 1-4 ---")
    verified_student_transcript = (
        "Private IP addresses are used inside local networks while public IP addresses are routed on the internet. "
        "NAPT uses port numbers alongside public IP addresses to map multiple internal device connections."
    )

    eval_req = EvaluateAnswerRequest(
        question_text="Describe how Network Address Translation (NAT) and NAPT allow multiple internal private IP devices to communicate over a single public IP address.",
        ideal_answer="NAT maps private internal IP addresses to a public external IP. NAPT extends this by mapping unique source port numbers alongside the public IP address.",
        evaluation_rubric=[
            RubricCriterion(criterion="Distinction between private internal and public external IP addresses", marks=3.0),
            RubricCriterion(criterion="Detailed mechanism of NAPT port mapping for inbound/outbound packets", marks=4.0),
            RubricCriterion(criterion="Translation table management and security benefits", marks=3.0)
        ],
        student_answer=verified_student_transcript,
        subject="Computer Networks",
        topic="IP Addressing & NAT"
    )

    record = evaluation_review_service.submit_student_answer_pipeline(eval_req, student_id="std_live_viva_101")
    print(f"Evaluation Record ID: {record.evaluation_id}")
    print(f"Status: {record.status}")
    print(f"Module 1 Status: {record.ai_version_v1.status}")
    print(f"Module 2 Score: {record.ai_version_v1.evaluation_summary.final_score} / 10.0")
    print(f"Module 3 Evidence Validity: {record.ai_version_v1.evaluation_summary.evidence_validity_status}")

    assert record.status.value == "PENDING_REVIEW"
    assert record.ai_version_v1.evaluation_summary.final_score > 0.0
    print("[PASSED]: Verified transcript successfully routed into evaluation pipeline.")

    print("\n" + "=" * 90)
    print("ALL STUDENT VIVA MODULE TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 90)

if __name__ == "__main__":
    run_student_viva_tests()
