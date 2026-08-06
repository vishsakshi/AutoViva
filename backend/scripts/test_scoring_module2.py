import json
from app.models.evaluation_module import CriterionEvaluationOutput, EvaluatorClassification
from app.services.scoring_engine import scoring_engine_module2

def run_unit_tests():
    print("=" * 80)
    print("VIVABOT PHASE 4 - MODULE 2: DETERMINISTIC SCORING ENGINE TEST SUITE")
    print("=" * 80)

    # TEST CASE 1: All Criteria Supported
    print("\n--- TEST CASE 1: All Criteria Supported ---")
    tc1_input = [
        CriterionEvaluationOutput(criterion_id="c1", criterion_text="Private vs Public IP", allocated_marks=3.0, classification=EvaluatorClassification.SUPPORTED, confidence=0.95, evidence_quote="q1", reasoning="r1"),
        CriterionEvaluationOutput(criterion_id="c2", criterion_text="NAPT Port Mapping", allocated_marks=4.0, classification=EvaluatorClassification.SUPPORTED, confidence=0.92, evidence_quote="q2", reasoning="r2"),
        CriterionEvaluationOutput(criterion_id="c3", criterion_text="Security Benefits", allocated_marks=3.0, classification=EvaluatorClassification.SUPPORTED, confidence=0.90, evidence_quote="q3", reasoning="r3")
    ]
    res1 = scoring_engine_module2.calculate_scores("eval_tc1", tc1_input)
    print(f"Total Score: {res1.total_score} / {res1.max_score} ({res1.percentage}%)")
    print(f"Pending Faculty Review: {res1.pending_faculty_review}")
    assert res1.total_score == 10.0
    assert res1.percentage == 100.0
    assert not res1.pending_faculty_review
    print("[PASSED] TEST CASE 1 PASSED: 10.0 / 10.0 (100.0%)")


    # TEST CASE 2: Mixed Supported / Partial (Stratified Multipliers)
    print("\n--- TEST CASE 2: Mixed Supported & Stratified Partial Credit ---")
    tc2_input = [
        CriterionEvaluationOutput(criterion_id="c1", criterion_text="Private vs Public IP", allocated_marks=3.0, classification=EvaluatorClassification.SUPPORTED, confidence=0.95, evidence_quote="q1", reasoning="r1"),
        CriterionEvaluationOutput(criterion_id="c2", criterion_text="NAPT Port Mapping", allocated_marks=4.0, classification=EvaluatorClassification.PARTIALLY_SUPPORTED, confidence=0.78, evidence_quote="q2", reasoning="r2"), # 0.75 * 4 = 3.0
        CriterionEvaluationOutput(criterion_id="c3", criterion_text="Security Benefits", allocated_marks=3.0, classification=EvaluatorClassification.PARTIALLY_SUPPORTED, confidence=0.72, evidence_quote="q3", reasoning="r3") # 0.75 * 3 = 2.25
    ]
    res2 = scoring_engine_module2.calculate_scores("eval_tc2", tc2_input)
    print(f"Total Score: {res2.total_score} / {res2.max_score} ({res2.percentage}%)")
    print(f"Pending Faculty Review: {res2.pending_faculty_review}")
    assert res2.total_score == 8.25
    assert res2.percentage == 82.5
    assert not res2.pending_faculty_review
    print("[PASSED] TEST CASE 2 PASSED: 8.25 / 10.0 (82.5%)")

    # TEST CASE 3: All Not Mentioned
    print("\n--- TEST CASE 3: All Criteria Not Mentioned ---")
    tc3_input = [
        CriterionEvaluationOutput(criterion_id="c1", criterion_text="Private vs Public IP", allocated_marks=3.0, classification=EvaluatorClassification.NOT_MENTIONED, confidence=0.90, evidence_quote="", reasoning="r1"),
        CriterionEvaluationOutput(criterion_id="c2", criterion_text="NAPT Port Mapping", allocated_marks=4.0, classification=EvaluatorClassification.NOT_MENTIONED, confidence=0.92, evidence_quote="", reasoning="r2"),
        CriterionEvaluationOutput(criterion_id="c3", criterion_text="Security Benefits", allocated_marks=3.0, classification=EvaluatorClassification.NOT_MENTIONED, confidence=0.95, evidence_quote="", reasoning="r3")
    ]
    res3 = scoring_engine_module2.calculate_scores("eval_tc3", tc3_input)
    print(f"Total Score: {res3.total_score} / {res3.max_score} ({res3.percentage}%)")
    print(f"Pending Faculty Review: {res3.pending_faculty_review}")
    assert res3.total_score == 0.0
    assert res3.percentage == 0.0
    assert not res3.pending_faculty_review
    print("[PASSED] TEST CASE 3 PASSED: 0.0 / 10.0 (0.0%)")

    # TEST CASE 4: Contradictions (Flagged Misconceptions)
    print("\n--- TEST CASE 4: Contradiction Flagged ---")
    tc4_input = [
        CriterionEvaluationOutput(criterion_id="c1", criterion_text="Private vs Public IP", allocated_marks=3.0, classification=EvaluatorClassification.CONTRADICTED, confidence=0.88, evidence_quote="q1", reasoning="r1"),
        CriterionEvaluationOutput(criterion_id="c2", criterion_text="NAPT Port Mapping", allocated_marks=4.0, classification=EvaluatorClassification.NOT_MENTIONED, confidence=0.90, evidence_quote="", reasoning="r2"),
        CriterionEvaluationOutput(criterion_id="c3", criterion_text="Security Benefits", allocated_marks=3.0, classification=EvaluatorClassification.NOT_MENTIONED, confidence=0.92, evidence_quote="", reasoning="r3")
    ]
    res4 = scoring_engine_module2.calculate_scores("eval_tc4", tc4_input)
    print(f"Total Score: {res4.total_score} / {res4.max_score} ({res4.percentage}%)")
    print(f"Pending Faculty Review: {res4.pending_faculty_review}")
    assert res4.total_score == 0.0
    assert res4.percentage == 0.0
    assert not res4.pending_faculty_review
    print("[PASSED] TEST CASE 4 PASSED: 0.0 / 10.0 (0.0%)")

    # TEST CASE 5: Review Required (Low Confidence < 0.55)
    print("\n--- TEST CASE 5: Review Required (Low Confidence < 0.55) ---")
    tc5_input = [
        CriterionEvaluationOutput(criterion_id="c1", criterion_text="Private vs Public IP", allocated_marks=3.0, classification=EvaluatorClassification.SUPPORTED, confidence=0.95, evidence_quote="q1", reasoning="r1"), # 3.0
        CriterionEvaluationOutput(criterion_id="c2", criterion_text="NAPT Port Mapping", allocated_marks=4.0, classification=EvaluatorClassification.PARTIALLY_SUPPORTED, confidence=0.45, evidence_quote="q2", reasoning="r2"), # low conf -> REVIEW_REQUIRED -> 0.0
        CriterionEvaluationOutput(criterion_id="c3", criterion_text="Security Benefits", allocated_marks=3.0, classification=EvaluatorClassification.NOT_MENTIONED, confidence=0.90, evidence_quote="", reasoning="r3")
    ]
    res5 = scoring_engine_module2.calculate_scores("eval_tc5", tc5_input)
    print(f"Total Score: {res5.total_score} / {res5.max_score} ({res5.percentage}%)")
    print(f"Pending Faculty Review: {res5.pending_faculty_review}")
    assert res5.total_score == 3.0
    assert res5.pending_faculty_review == True
    print("[PASSED] TEST CASE 5 PASSED: Flagged pending_faculty_review = True due to low confidence.")


    print("\n--- SAMPLE MODULE 2 INPUT & OUTPUT (MIXED SCENARIO) ---")
    print("SAMPLE INPUT (Module 1 Output):")
    print(json.dumps([c.model_dump() for c in tc2_input], indent=2))
    print("\nSAMPLE OUTPUT (Module 2 Response):")
    print(json.dumps(res2.model_dump(), indent=2))

    print("\n" + "=" * 80)
    print("ALL MODULE 2 UNIT TESTS PASSED WITH 100% DETERMINISTIC PRECISION!")
    print("=" * 80)

if __name__ == "__main__":
    run_unit_tests()
