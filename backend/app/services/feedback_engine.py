import logging
from typing import List, Dict, Any, Tuple
from app.models.evaluation_module import EvaluatorClassification
from app.models.feedback_module import (
    GenerateFeedbackRequest,
    FeedbackModule3Response,
    EvaluationSummary,
    CriterionFeedbackItem,
    EvidenceValidationItem
)

logger = logging.getLogger("vivabot.services.feedback_engine")

class EvidenceValidationEngine:
    """
    Task 1: Evidence Validation Engine.
    Verifies that every evidence quote is an exact verbatim substring of student_answer.
    Never fabricates or paraphrases evidence.
    """
    def validate_evidence_quote(self, quote: str, student_answer: str, classification: EvaluatorClassification) -> Tuple[bool, str]:
        if classification == EvaluatorClassification.NOT_MENTIONED:
            if not quote or len(quote.strip()) == 0:
                return True, "EMPTY_NOT_MENTIONED"
            else:
                # Quote provided for not mentioned criterion
                return False, "INVALID_EVIDENCE"

        if not quote or len(quote.strip()) == 0:
            return False, "INVALID_EVIDENCE"

        # Verbatim substring check
        if quote.strip() in student_answer:
            return True, "VALID_VERBATIM"
        else:
            return False, "INVALID_EVIDENCE"

class FeedbackEngineModule3:
    """
    Module 3 Feedback Engine:
    - Verifies evidence quotes
    - Generates 1-to-1 mapped actionable feedback and improvement suggestions
    - Performs Quality Checks
    - Strictly preserves Module 2 marks & Module 1 classifications
    """
    def __init__(self):
        self.validator = EvidenceValidationEngine()

    def generate_suggestion(self, criterion_text: str, classification: EvaluatorClassification) -> str:
        """
        Task 3: Improvement Suggestions.
        Generates ONE concise improvement suggestion mapping directly to the rubric criterion.
        """
        c_text = criterion_text.strip()
        if classification == EvaluatorClassification.PARTIALLY_SUPPORTED:
            return f"Elaborate further on '{c_text}' by detailing its specific operational mechanisms and key requirements."
        elif classification == EvaluatorClassification.NOT_MENTIONED:
            return f"Include complete explanation of '{c_text}' in your response."
        elif classification == EvaluatorClassification.CONTRADICTED:
            return f"Review the correct concepts for '{c_text}' to address factual inaccuracies."
        return ""

    def generate_feedback_report(self, req: GenerateFeedbackRequest) -> FeedbackModule3Response:
        m1 = req.module1_result
        m2 = req.module2_result

        evidence_validations: List[EvidenceValidationItem] = []
        criterion_feedbacks: List[CriterionFeedbackItem] = []
        strengths: List[str] = []
        improvements: List[Dict[str, str]] = []
        misconceptions: List[Dict[str, str]] = []

        all_evidence_valid = True

        # Build Map of Module 2 scores by criterion_id
        m2_score_map = {cs.criterion_id: cs for cs in m2.criterion_scores}

        for m1_item in m1.criterion_evaluations:
            c_id = m1_item.criterion_id
            m2_item = m2_score_map.get(c_id)

            earned = m2_item.earned_marks if m2_item else 0.0
            allocated = m1_item.allocated_marks

            # 1. Validate Evidence Quote (Task 1)
            is_valid, status_code = self.validator.validate_evidence_quote(
                quote=m1_item.evidence_quote,
                student_answer=req.student_answer,
                classification=m1_item.classification
            )

            if not is_valid:
                all_evidence_valid = False

            evidence_validations.append(
                EvidenceValidationItem(
                    criterion_id=c_id,
                    evidence_quote=m1_item.evidence_quote,
                    is_verbatim=is_valid,
                    validation_status=status_code
                )
            )

            # 2. Build Criterion Feedback & Notes (Task 2)
            if m1_item.classification == EvaluatorClassification.SUPPORTED:
                note = f"Fully satisfied criterion. Earned {earned}/{allocated} marks."
                strengths.append(f"Demonstrated full understanding of '{m1_item.criterion_text}'.")
            elif m1_item.classification == EvaluatorClassification.PARTIALLY_SUPPORTED:
                note = f"Partially satisfied criterion. Earned {earned}/{allocated} marks."
                suggestion = self.generate_suggestion(m1_item.criterion_text, m1_item.classification)
                improvements.append({
                    "criterion_id": c_id,
                    "criterion_text": m1_item.criterion_text,
                    "suggestion": suggestion
                })
            elif m1_item.classification == EvaluatorClassification.NOT_MENTIONED:
                note = f"Omitted criterion. Earned 0/{allocated} marks."
                suggestion = self.generate_suggestion(m1_item.criterion_text, m1_item.classification)
                improvements.append({
                    "criterion_id": c_id,
                    "criterion_text": m1_item.criterion_text,
                    "suggestion": suggestion
                })
            elif m1_item.classification == EvaluatorClassification.CONTRADICTED:
                note = f"Contradicted criterion. Earned 0/{allocated} marks."
                suggestion = self.generate_suggestion(m1_item.criterion_text, m1_item.classification)
                misconceptions.append({
                    "criterion_id": c_id,
                    "criterion_text": m1_item.criterion_text,
                    "evidence_quote": m1_item.evidence_quote,
                    "reasoning": m1_item.reasoning,
                    "suggestion": suggestion
                })
            else:
                note = f"Evaluation flagged for faculty review."

            criterion_feedbacks.append(
                CriterionFeedbackItem(
                    criterion_id=c_id,
                    criterion_text=m1_item.criterion_text,
                    allocated_marks=allocated,
                    earned_marks=earned,
                    classification=m1_item.classification,
                    confidence=m1_item.confidence,
                    evidence_quote=m1_item.evidence_quote,
                    evidence_valid=is_valid,
                    feedback_note=note
                )
            )

        summary = EvaluationSummary(
            evaluation_id=m1.evaluation_id,
            final_score=m2.total_score,
            max_score=m2.max_score,
            percentage=m2.percentage,
            pending_faculty_review=m2.pending_faculty_review,
            evidence_validity_status="ALL_EVIDENCE_VALID" if all_evidence_valid else "CONTAINS_INVALID_EVIDENCE"
        )

        logger.info(f"Module 3 Feedback [{m1.evaluation_id}]: Strengths={len(strengths)}, Improvements={len(improvements)}, Misconceptions={len(misconceptions)}, Evidence Valid={all_evidence_valid}.")

        return FeedbackModule3Response(
            status="success",
            evaluation_summary=summary,
            criterion_feedback=criterion_feedbacks,
            strengths=strengths,
            improvements=improvements,
            misconceptions=misconceptions,
            evidence_validation=evidence_validations
        )

feedback_engine_module3 = FeedbackEngineModule3()
