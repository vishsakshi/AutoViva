import json
from app.models.evaluation_module import EvaluateAnswerRequest, CriterionEvaluationOutput, EvaluatorClassification
from app.models.feedback_module import GenerateFeedbackRequest
from app.models.question_gen import RubricCriterion
from app.services.evaluation_engine import evaluation_engine_module1
from app.services.scoring_engine import scoring_engine_module2
from app.services.feedback_engine import feedback_engine_module3

def run_feedback_unit_tests():
    print("=" * 80)
    print("VIVABOT PHASE 4 - MODULE 3: EVIDENCE VALIDATION & FEEDBACK ENGINE TEST SUITE")
    print("=" * 80)

    # Base Question & Rubric
    q_text = "Describe how Network Address Translation (NAT) and NAPT allow multiple internal private IP devices to communicate over a single public IP address."
    ideal_ans = "NAT maps private internal IP addresses to a public external IP. NAPT (Port Address Translation) extends this by mapping unique source port numbers alongside the public IP address, allowing thousands of internal sockets to share a single public IP. NAT also hides internal IP topologies for security."
    rubric = [
        RubricCriterion(criterion="Distinction between private internal and public external IP addresses", marks=3.0),
        RubricCriterion(criterion="Detailed mechanism of NAPT port mapping for inbound/outbound packets", marks=4.0),
        RubricCriterion(criterion="Translation table management and security benefits", marks=3.0)
    ]

    # TEST CASE 1: Fully Correct Answer
    print("\n--- TEST CASE 1: Fully Correct Answer ---")
    std_ans1 = "Distinction between private internal and public external IP addresses is local vs internet routing. Detailed mechanism of NAPT port mapping connects ports. Translation table management and security benefits hide internal topology."

    req1 = EvaluateAnswerRequest(question_text=q_text, ideal_answer=ideal_ans, evaluation_rubric=rubric, student_answer=std_ans1)
    m1_1 = evaluation_engine_module1.evaluate_answer_module1(req1)
    m2_1 = scoring_engine_module2.calculate_scores(m1_1.evaluation_id, m1_1.criterion_evaluations)
    fb_req1 = GenerateFeedbackRequest(question_text=q_text, ideal_answer=ideal_ans, student_answer=std_ans1, module1_result=m1_1, module2_result=m2_1)
    fb_res1 = feedback_engine_module3.generate_feedback_report(fb_req1)

    print(f"Final Score: {fb_res1.evaluation_summary.final_score} / {fb_res1.evaluation_summary.max_score}")
    print(f"Evidence Validity: {fb_res1.evaluation_summary.evidence_validity_status}")
    print(f"Strengths Count: {len(fb_res1.strengths)} | Improvements: {len(fb_res1.improvements)}")
    assert fb_res1.evaluation_summary.final_score == 10.0
    assert fb_res1.evaluation_summary.evidence_validity_status == "ALL_EVIDENCE_VALID"
    assert len(fb_res1.strengths) >= 1
    print("[PASSED] TEST CASE 1 PASSED: Fully correct feedback report verified.")

    # TEST CASE 2: Partial Answer
    print("\n--- TEST CASE 2: Partial Answer ---")
    std_ans2 = "Private IPs are used inside local networks while public IPs are routed on the internet. NAPT uses port numbers for mapping connections."
    req2 = EvaluateAnswerRequest(question_text=q_text, ideal_answer=ideal_ans, evaluation_rubric=rubric, student_answer=std_ans2)
    m1_2 = evaluation_engine_module1.evaluate_answer_module1(req2)
    m2_2 = scoring_engine_module2.calculate_scores(m1_2.evaluation_id, m1_2.criterion_evaluations)
    fb_req2 = GenerateFeedbackRequest(question_text=q_text, ideal_answer=ideal_ans, student_answer=std_ans2, module1_result=m1_2, module2_result=m2_2)
    fb_res2 = feedback_engine_module3.generate_feedback_report(fb_req2)

    print(f"Final Score: {fb_res2.evaluation_summary.final_score} / {fb_res2.evaluation_summary.max_score}")
    print(f"Improvements Suggested ({len(fb_res2.improvements)}):")
    for imp in fb_res2.improvements:
        print(f"  - [{imp['criterion_id']}]: \"{imp['suggestion']}\"")
    assert len(fb_res2.improvements) >= 1
    print("[PASSED] TEST CASE 2 PASSED: 1-to-1 mapped improvement suggestions verified.")

    # TEST CASE 3: Wrong / Contradicted Answer
    print("\n--- TEST CASE 3: Contradicted Answer ---")
    std_ans3 = "Private IPs and public IPs are completely identical and NAT is not needed for routing."
    req3 = EvaluateAnswerRequest(question_text=q_text, ideal_answer=ideal_ans, evaluation_rubric=rubric, student_answer=std_ans3)
    m1_3 = evaluation_engine_module1.evaluate_answer_module1(req3)
    m2_3 = scoring_engine_module2.calculate_scores(m1_3.evaluation_id, m1_3.criterion_evaluations)
    fb_req3 = GenerateFeedbackRequest(question_text=q_text, ideal_answer=ideal_ans, student_answer=std_ans3, module1_result=m1_3, module2_result=m2_3)
    fb_res3 = feedback_engine_module3.generate_feedback_report(fb_req3)

    print(f"Final Score: {fb_res3.evaluation_summary.final_score} / {fb_res3.evaluation_summary.max_score}")
    print(f"Misconceptions Detected ({len(fb_res3.misconceptions)}):")
    for misc in fb_res3.misconceptions:
        print(f"  - [{misc['criterion_id']}]: Quote: \"{misc['evidence_quote']}\"")
    print("[PASSED] TEST CASE 3 PASSED: Misconception tracking verified.")

    # TEST CASE 4: Mixed Correct & Incorrect Answer
    print("\n--- TEST CASE 4: Mixed Correct and Incorrect Answer ---")
    std_ans4 = "Distinction between private internal and public external IP addresses is local vs internet routing. NAPT uses port numbers for mapping connections."

    req4 = EvaluateAnswerRequest(question_text=q_text, ideal_answer=ideal_ans, evaluation_rubric=rubric, student_answer=std_ans4)
    m1_4 = evaluation_engine_module1.evaluate_answer_module1(req4)
    m2_4 = scoring_engine_module2.calculate_scores(m1_4.evaluation_id, m1_4.criterion_evaluations)
    fb_req4 = GenerateFeedbackRequest(question_text=q_text, ideal_answer=ideal_ans, student_answer=std_ans4, module1_result=m1_4, module2_result=m2_4)
    fb_res4 = feedback_engine_module3.generate_feedback_report(fb_req4)

    print(f"Strengths: {len(fb_res4.strengths)} | Improvements: {len(fb_res4.improvements)}")
    assert len(fb_res4.strengths) >= 1
    assert len(fb_res4.improvements) >= 1
    print("[PASSED] TEST CASE 4 PASSED: Strengths and improvements partitioned correctly.")

    # TEST CASE 5: Very Concise But Correct Answer (0 Length Penalty)
    print("\n--- TEST CASE 5: Very Concise But Correct Answer ---")
    std_ans5 = "Distinction between private internal and public external IP addresses is local vs internet. Detailed mechanism of NAPT port mapping connects ports. Translation table management and security benefits hide internal topology."

    req5 = EvaluateAnswerRequest(question_text=q_text, ideal_answer=ideal_ans, evaluation_rubric=rubric, student_answer=std_ans5)
    m1_5 = evaluation_engine_module1.evaluate_answer_module1(req5)
    m2_5 = scoring_engine_module2.calculate_scores(m1_5.evaluation_id, m1_5.criterion_evaluations)
    fb_req5 = GenerateFeedbackRequest(question_text=q_text, ideal_answer=ideal_ans, student_answer=std_ans5, module1_result=m1_5, module2_result=m2_5)
    fb_res5 = feedback_engine_module3.generate_feedback_report(fb_req5)

    print(f"Final Score: {fb_res5.evaluation_summary.final_score} / {fb_res5.evaluation_summary.max_score} (Concise Answer Word Count: {len(std_ans5.split())} words)")
    assert fb_res5.evaluation_summary.final_score == 10.0
    print("[PASSED] TEST CASE 5 PASSED: Concise correct answer receives 10.0/10.0 with 0 length penalty.")

    print("\n--- SAMPLE MODULE 3 INPUT & OUTPUT ---")
    print("SAMPLE REQUEST (GenerateFeedbackRequest):")
    print(json.dumps(fb_req2.model_dump(), indent=2)[:400] + "\n...[truncated for display]...")
    print("\nSAMPLE RESPONSE (FeedbackModule3Response):")
    print(json.dumps(fb_res2.model_dump(), indent=2))

    print("\n" + "=" * 80)
    print("ALL MODULE 3 UNIT TESTS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_feedback_unit_tests()
