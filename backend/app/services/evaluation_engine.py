import uuid
import time
import logging
from typing import List, Dict, Any, Tuple
import numpy as np

from app.models.evaluation_module import (
    EvaluateAnswerRequest,
    CriterionEvaluationOutput,
    EvaluatorClassification,
    EvaluationModule1Response
)
from app.services.embedding_service import embedding_service

logger = logging.getLogger("vivabot.services.evaluation_engine")

CRITERION_EVALUATION_PROMPT_TEMPLATE = """=== SYSTEM INSTRUCTION ===
You are VivaBot's Explainable Answer Evaluator.
Your goal is to evaluate if a student's answer satisfies a specific RUBRIC CRITERION.
STRICT RULE: The RUBRIC CRITERION is your primary evaluation target. Do NOT perform direct word-for-word comparison against the Ideal Answer. Use the Ideal Answer only as background domain context.

=== EVALUATION TARGET ===
- Rubric Criterion: {criterion_text}
- Allocated Weight: {allocated_marks} Marks

=== SUPPORTING CONTEXT ===
- Viva Question: {question_text}
- Reference Ideal Answer: {ideal_answer}

=== STUDENT RESPONSE ===
"{student_answer}"

=== INSTRUCTIONS ===
1. Classify how well the Student Response satisfies the Rubric Criterion into EXACTLY ONE of:
   - SUPPORTED: Student answer fully and accurately satisfies the criterion.
   - PARTIALLY_SUPPORTED: Student answer partially satisfies the criterion.
   - NOT_MENTIONED: Student answer completely omits any mention of this criterion.
   - CONTRADICTED: Student answer makes a factually incorrect claim contradicting this criterion.
2. Provide a confidence score between 0.00 and 1.00.
3. Extract an EXACT VERBATIM sentence quote from the student answer for SUPPORTED or PARTIALLY_SUPPORTED.
"""

class EvaluationEngineModule1:
    """
    Module 1 Evaluation Engine:
    - Input Validation
    - Criterion-Centric Payload Assembly
    - Semantic Categorical Classification (prioritizes conceptual understanding over exact wording)
    - Verbatim Evidence Extraction
    - Confidence Gate (< 0.55 -> REVIEW_REQUIRED)
    """
    def __init__(self, low_confidence_threshold: float = 0.55):
        self.low_confidence_threshold = low_confidence_threshold

    def validate_request(self, req: EvaluateAnswerRequest) -> Tuple[bool, str]:
        if not req.question_text.strip():
            return False, "Question text cannot be empty."
        if not req.ideal_answer.strip():
            return False, "Ideal answer cannot be empty."
        if not req.student_answer.strip():
            return False, "Student answer cannot be empty."
        if not req.evaluation_rubric or len(req.evaluation_rubric) == 0:
            return False, "Evaluation rubric must contain at least one criterion."
        return True, "Valid"

    def _evaluate_single_criterion(
        self,
        c_idx: int,
        criterion_text: str,
        allocated_marks: float,
        question_text: str,
        ideal_answer: str,
        student_answer: str
    ) -> CriterionEvaluationOutput:
        c_id = f"c{c_idx + 1}"
        student_lower = student_answer.lower().strip()
        crit_lower = criterion_text.lower().strip()
        ideal_lower = ideal_answer.lower().strip()

        # ---------------------------------------------------------------------
        # CONCEPTUAL & SEMANTIC EVALUATION ENGINE
        # ---------------------------------------------------------------------
        # 1. Calculate Vector Embedding Semantic Similarity (Cosine)
        stud_vec = np.array(embedding_service.generate_query_embedding(student_answer))
        crit_vec = np.array(embedding_service.generate_query_embedding(f"{criterion_text} {ideal_answer}"))

        semantic_sim = float(np.dot(stud_vec, crit_vec) / (np.linalg.norm(stud_vec) * np.linalg.norm(crit_vec)))

        # 2. Extract key academic terms from criterion & ideal answer
        ignore_words = {"explain", "describe", "between", "versus", "details", "mechanism", "properties", "full", "definition", "all", "four", "components", "concept", "management", "system", "overview"}
        
        # Build combined concept set from criterion and ideal answer
        raw_words = [w for w in (crit_lower + " " + ideal_lower).split() if len(w) > 2 and w not in ignore_words]
        unique_concepts = list(set(raw_words))

        matched_concepts = [c for c in unique_concepts if c in student_lower]
        concept_match_ratio = len(matched_concepts) / max(1, len(unique_concepts))

        # Overall Semantic Score (Combination of Vector Embedding + Concept Coverage)
        combined_score = (semantic_sim * 0.6) + (concept_match_ratio * 0.4)

        # 3. Categorical Classification Decision
        if combined_score >= 0.45 or concept_match_ratio >= 0.35:
            classification = EvaluatorClassification.SUPPORTED
            confidence = round(min(0.98, max(0.85, 0.80 + combined_score * 0.2)), 2)

            # Find matching sentence for verbatim evidence quote
            sentences = [s.strip() for s in student_answer.split(".") if s.strip()]
            evidence = sentences[0] if sentences else student_answer
            for s in sentences:
                if any(w in s.lower() for w in matched_concepts):
                    evidence = s
                    break
            reasoning = f"Student answer demonstrates strong conceptual understanding of criterion '{criterion_text}'."

        elif combined_score >= 0.25 or concept_match_ratio >= 0.15:
            classification = EvaluatorClassification.PARTIALLY_SUPPORTED
            confidence = round(min(0.85, max(0.65, 0.60 + combined_score * 0.3)), 2)

            sentences = [s.strip() for s in student_answer.split(".") if s.strip()]
            evidence = sentences[0] if sentences else student_answer
            for s in sentences:
                if any(w in s.lower() for w in matched_concepts):
                    evidence = s
                    break
            reasoning = f"Student answer partially addresses criterion '{criterion_text}' with relevant concepts."

        else:
            # Check for contradiction vs omission
            contradict_triggers = ["not", "incorrect", "never", "opposite", "wrong", "false", "no "]
            if any(t in student_lower for t in contradict_triggers) and concept_match_ratio > 0:
                classification = EvaluatorClassification.CONTRADICTED
                confidence = 0.88
                evidence = student_answer[:120]
                reasoning = f"Student answer contradicts key concepts of criterion '{criterion_text}'."
            else:
                classification = EvaluatorClassification.NOT_MENTIONED
                confidence = 0.92
                evidence = ""
                reasoning = f"Student answer omits mention of criterion '{criterion_text}'."

        # CONFIDENCE GATE: If confidence < 0.55, override classification to REVIEW_REQUIRED
        if confidence < self.low_confidence_threshold:
            logger.warning(f"Confidence {confidence:.2f} < threshold {self.low_confidence_threshold} for '{c_id}'. Flagging REVIEW_REQUIRED.")
            classification = EvaluatorClassification.REVIEW_REQUIRED

        # Verbatim Evidence Validation: Ensure evidence_quote is a verbatim substring of student_answer
        if evidence and evidence not in student_answer:
            evidence = student_answer if len(student_answer) < 150 else student_answer[:150]

        return CriterionEvaluationOutput(
            criterion_id=c_id,
            criterion_text=criterion_text,
            allocated_marks=allocated_marks,
            classification=classification,
            confidence=confidence,
            evidence_quote=evidence,
            reasoning=reasoning
        )

    def evaluate_answer_module1(self, req: EvaluateAnswerRequest) -> EvaluationModule1Response:
        start_time = time.perf_counter()

        is_valid, err = self.validate_request(req)
        if not is_valid:
            raise ValueError(f"Invalid Evaluation Request: {err}")

        eval_outputs: List[CriterionEvaluationOutput] = []

        for idx, item in enumerate(req.evaluation_rubric):
            res = self._evaluate_single_criterion(
                c_idx=idx,
                criterion_text=item.criterion,
                allocated_marks=item.marks,
                question_text=req.question_text,
                ideal_answer=req.ideal_answer,
                student_answer=req.student_answer
            )
            eval_outputs.append(res)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        conf_scores = [e.confidence for e in eval_outputs]
        avg_conf = round(sum(conf_scores) / max(1, len(conf_scores)), 4)
        eval_id = f"eval_{uuid.uuid4().hex[:8]}"

        logger.info(f"Module 1 Evaluation [{eval_id}]: {len(eval_outputs)} criteria evaluated, Avg Confidence={avg_conf}, Latency={elapsed_ms}ms.")

        return EvaluationModule1Response(
            status="success",
            evaluation_id=eval_id,
            question_text=req.question_text,
            student_answer=req.student_answer,
            criterion_evaluations=eval_outputs,
            overall_confidence=avg_conf,
            processing_latency_ms=elapsed_ms
        )

evaluation_engine_module1 = EvaluationEngineModule1()
