import logging
from typing import List, Dict, Any, Tuple
from app.models.evaluation_module import CriterionEvaluationOutput, EvaluatorClassification
from app.models.scoring_module import CriterionScoringResult, ScoringModule2Response

logger = logging.getLogger("vivabot.services.scoring_engine")

class DeterministicScoringEngineModule2:
    """
    Module 2 Standalone Deterministic Scoring Engine.
    Strictly receives Module 1's structured criterion classifications and confidence scores.
    NEVER communicates with LLMs.
    Calculates earned marks, total score, percentage, and pending_faculty_review flag.
    """
    def __init__(self, low_confidence_threshold: float = 0.55):
        self.low_confidence_threshold = low_confidence_threshold

    def compute_multiplier(self, classification: EvaluatorClassification, confidence: float) -> Tuple[float, EvaluatorClassification]:
        """
        Confidence-Stratified Multiplier Mapping (from approved Phase 4 design):
        - SUPPORTED: 1.0 (100% of weight W_i)
        - PARTIALLY_SUPPORTED:
            - confidence >= 0.85 -> 0.90 (90% of weight W_i)
            - 0.70 <= confidence < 0.85 -> 0.75 (75% of weight W_i)
            - 0.55 <= confidence < 0.70 -> 0.60 (60% of weight W_i)
            - confidence < 0.55 -> REVIEW_REQUIRED (0.0 multiplier)
        - NOT_MENTIONED: 0.0 (0% of weight W_i)
        - CONTRADICTED: 0.0 (0% of weight W_i)
        - REVIEW_REQUIRED: 0.0 (0% of weight W_i)
        """
        if confidence < self.low_confidence_threshold or classification == EvaluatorClassification.REVIEW_REQUIRED:
            return 0.0, EvaluatorClassification.REVIEW_REQUIRED

        if classification == EvaluatorClassification.SUPPORTED:
            return 1.0, EvaluatorClassification.SUPPORTED

        elif classification == EvaluatorClassification.PARTIALLY_SUPPORTED:
            if confidence >= 0.85:
                return 0.90, EvaluatorClassification.PARTIALLY_SUPPORTED
            elif confidence >= 0.70:
                return 0.75, EvaluatorClassification.PARTIALLY_SUPPORTED
            elif confidence >= 0.55:
                return 0.60, EvaluatorClassification.PARTIALLY_SUPPORTED
            else:
                return 0.0, EvaluatorClassification.REVIEW_REQUIRED

        elif classification == EvaluatorClassification.NOT_MENTIONED:
            return 0.0, EvaluatorClassification.NOT_MENTIONED

        elif classification == EvaluatorClassification.CONTRADICTED:
            return 0.0, EvaluatorClassification.CONTRADICTED

        else:
            return 0.0, EvaluatorClassification.REVIEW_REQUIRED

    def calculate_scores(
        self,
        evaluation_id: str,
        criterion_evaluations: List[CriterionEvaluationOutput]
    ) -> ScoringModule2Response:
        scoring_results: List[CriterionScoringResult] = []
        total_earned = 0.0
        max_possible = 0.0
        pending_review = False

        for eval_item in criterion_evaluations:
            multiplier, final_class = self.compute_multiplier(
                classification=eval_item.classification,
                confidence=eval_item.confidence
            )

            if final_class == EvaluatorClassification.REVIEW_REQUIRED:
                pending_review = True

            earned = round(eval_item.allocated_marks * multiplier, 2)
            total_earned += earned
            max_possible += eval_item.allocated_marks

            scoring_results.append(
                CriterionScoringResult(
                    criterion_id=eval_item.criterion_id,
                    criterion_text=eval_item.criterion_text,
                    allocated_marks=eval_item.allocated_marks,
                    earned_marks=earned,
                    classification=final_class,
                    confidence=eval_item.confidence,
                    multiplier_applied=multiplier
                )
            )

        total_earned = round(total_earned, 2)
        max_possible = round(max_possible, 2) if max_possible > 0 else 10.0
        percentage = round((total_earned / max_possible) * 100.0, 2)

        logger.info(f"Module 2 Scoring [{evaluation_id}]: Total={total_earned}/{max_possible} ({percentage}%), Pending Review={pending_review}.")

        return ScoringModule2Response(
            status="success",
            evaluation_id=evaluation_id,
            criterion_scores=scoring_results,
            total_score=total_earned,
            max_score=max_possible,
            percentage=percentage,
            pending_faculty_review=pending_review
        )

scoring_engine_module2 = DeterministicScoringEngineModule2()
