import json
from app.models.evaluation_module import EvaluateAnswerRequest
from app.models.question_gen import RubricCriterion
from app.services.evaluation_engine import evaluation_engine_module1

def main():
    print("=" * 80)
    print("VIVABOT PHASE 4 - MODULE 1: EVALUATION API TEST SUITE")
    print("=" * 80)

    # 1. Sample Evaluation Input
    sample_request = EvaluateAnswerRequest(
        question_text="Describe how Network Address Translation (NAT) and NAPT allow multiple internal private IP devices to communicate over a single public IP address.",
        ideal_answer="NAT maps private internal IP addresses to a public external IP. NAPT (Port Address Translation) extends this by mapping unique source port numbers alongside the public IP address, allowing thousands of internal sockets to share a single public IP. NAT also hides internal IP topologies for security.",
        evaluation_rubric=[
            RubricCriterion(criterion="Distinction between private internal and public external IP addresses", marks=3.0),
            RubricCriterion(criterion="Detailed mechanism of NAPT port mapping for inbound/outbound packets", marks=4.0),
            RubricCriterion(criterion="Translation table management and security benefits", marks=3.0)
        ],
        student_answer="Private IPs are used inside local networks while public IPs are routed on the internet. NAPT uses port numbers for mapping connections. It also hides internal IPs for security.",
        subject="Computer Networks",
        topic="IP Addressing & NAT"
    )

    print("\n--- INPUT PAYLOAD ---")
    print(f"Question: \"{sample_request.question_text}\"")
    print(f"Student Answer: \"{sample_request.student_answer}\"")
    print(f"Rubric Criteria Count: {len(sample_request.evaluation_rubric)}")

    # 2. Call Module 1 Evaluator Engine
    print("\n--- CALLING MODULE 1 EVALUATOR ENGINE ---")
    result = evaluation_engine_module1.evaluate_answer_module1(sample_request)

    print(f"Status: {result.status}")
    print(f"Evaluation ID: {result.evaluation_id}")
    print(f"Overall Confidence: {result.overall_confidence}")
    print(f"Processing Latency: {result.processing_latency_ms} ms")

    print("\n--- STRUCTURED CATEGORICAL CLASSIFICATION JSON OUTPUT ---")
    output_dict = result.model_dump()
    print(json.dumps(output_dict, indent=2))

    # 3. Assert Module 1 Constraints
    # Ensure NO marks calculated, NO feedback generated
    for c in result.criterion_evaluations:
        assert hasattr(c, "classification")
        assert hasattr(c, "confidence")
        assert hasattr(c, "evidence_quote")
        assert hasattr(c, "reasoning")
        assert not hasattr(c, "earned_marks")  # No mark calculation in Module 1

    assert not hasattr(result, "final_score")
    assert not hasattr(result, "suggested_improvements")

    print("\n" + "=" * 80)
    print("SUCCESS: MODULE 1 EVALUATION API COMPLETED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
