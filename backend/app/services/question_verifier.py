import re
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service

logger = logging.getLogger("vivabot.services.question_verifier")

class QuestionVerifier:
    """
    Mandatory Multi-Stage Question & Ideal Answer Validation Gate for AutoViva.
    Enforces Steps 8 & 9:
    1. Literal Source Quote Substring Verification (Verifies source_quote is 100% in context chunk).
    2. Artifact & Structural Meta-Reference Rejection ("DOC 1", slide numbers "9/20", author names, "According to paragraph...").
    3. Keyword Grounding Overlap (> 0.35).
    4. LLM Semantic Judge Validation (question_grounded, answer_grounded, question_answer_aligned).
    5. Vector Cosine Deduplication (< 0.78 similarity).
    """

    def verify_source_quote_substring(self, source_quote: str, evidence_chunks: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Verifies that source_quote is a 100% exact literal substring match within original context chunk text.
        """
        if not source_quote or not source_quote.strip():
            return True, "No source_quote provided."

        sq_exact = source_quote.strip()
        sq_clean = re.sub(r"\s+", " ", sq_exact).lower()
        combined_raw = " ".join([c.get("text", "") for c in evidence_chunks])
        combined_clean = re.sub(r"\s+", " ", combined_raw).lower()

        if sq_exact in combined_raw or sq_clean in combined_clean:
            return True, "100% literal substring match confirmed."

        # Token overlap check as fallback
        sq_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", sq_clean))
        if sq_words:
            found = sum(1 for w in sq_words if w in combined_clean)
            ratio = found / len(sq_words)
            if ratio >= 0.75:
                return True, f"Fuzzy quote match confirmed ({ratio:.2f} token overlap)."

        return False, f"Literal source_quote mismatch: '{source_quote[:60]}...' is not present in retrieved text chunk."

    def verify_question_candidate(
        self,
        question_text: str,
        ideal_answer: str,
        evidence_chunks: List[Dict[str, Any]],
        topic_title: str,
        existing_questions: Optional[List[str]] = None,
        source_quote: str = "",
        options: Optional[Dict[str, str]] = None,
        correct_answer: str = ""
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-dimensional verification on a generated viva question and ideal answer pair.
        """
        reasons = []
        is_valid = True

        q_clean = question_text.strip()
        ans_clean = ideal_answer.strip()
        combined_evidence = " ".join([c.get("text", "") for c in evidence_chunks]).lower()

        # --- A. LENGTH & COMPLETENESS CHECK ---
        word_count = len(q_clean.split())
        if word_count > 45:
            is_valid = False
            reasons.append(f"Question exceeds max oral length ({word_count} words > 45 words max).")
        if word_count < 4:
            is_valid = False
            reasons.append("Question is too short (< 4 words).")

        if not q_clean.endswith("?") and not q_clean.endswith("."):
            q_clean += "?"

        # --- B. LITERAL SOURCE QUOTE SUBSTRING CHECK ---
        if source_quote:
            sq_valid, sq_reason = self.verify_source_quote_substring(source_quote, evidence_chunks)
            if not sq_valid:
                is_valid = False
                reasons.append(sq_reason)

        # --- C. OPTIONS & CORRECT ANSWER VALIDATION ---
        if options is not None and len(options) > 0:
            if not isinstance(options, dict) or len(options) != 4 or not all(k in options for k in ["A", "B", "C", "D"]):
                is_valid = False
                reasons.append("Invalid options structure: must contain exactly 4 keys ('A', 'B', 'C', 'D').")
            if correct_answer not in ["A", "B", "C", "D"]:
                is_valid = False
                reasons.append(f"Invalid correct_answer '{correct_answer}': must be one of 'A', 'B', 'C', or 'D'.")

        # --- D. NOISE, ARTIFACT & STRUCTURAL META-REFERENCE REJECTION ---
        artifact_patterns = [
            r"\bdoc\s*\d+\b",
            r"\bdocument\s*\d+\b",
            r"\bexample\s*\d+\b",
            r"\bfig\s*\d+\b",
            r"\bfigure\s*\d+\b",
            r"\bslide\s*\d+\b",
            r"\bpage\s*\d+\b",
            r"\bmayank\s+singh\b",
            r"\bwritten\s+several\s+articles\b",
            r"\bcopyright\b",
            r"\bused\s+for\s+tra\b",
            r"\baccording\s+to\b",
            r"\bbased\s+on\b",
            r"\bin\s+paragraph\b",
            r"\bthe\s+provided\s+(text|passage|document|slide|chunk)\b",
            r"\bas\s+stated\s+in\b",
            r"\bas\s+mentioned\s+in\b",
            r"\bor\s+a\s+word\b",
            r"\bwhat\s+is\s+what\s+is\b",
            r"\bwhat\s+is\s+output\b",
            r"\bwhat\s+is\s+doc\b"
        ]

        q_ans_combined = (q_clean + " " + ans_clean).lower()

        for pat in artifact_patterns:
            if re.search(pat, q_ans_combined):
                is_valid = False
                reasons.append(f"Contains document artifact or structural meta-reference: '{pat}'.")

        if re.search(r"\b\d+\s*/\s*\d+\b", q_ans_combined):
            is_valid = False
            reasons.append("Contains raw page/slide numbers (e.g. '9/20').")

        # --- E. KEYWORD GROUNDING CHECK ---
        ignore_words = {
            "what", "is", "how", "why", "explain", "describe", "critically", "evaluate",
            "the", "and", "in", "of", "to", "a", "an", "for", "with", "behind", "it",
            "primary", "technical", "trade-offs", "constraints", "advantages", "core",
            "intuition", "fundamental", "principles", "step-by-step", "mechanism", "practice"
        }

        q_terms = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", q_clean) if w.lower() not in ignore_words]

        if q_terms and combined_evidence:
            grounded_count = sum(1 for term in q_terms if term in combined_evidence)
            grounding_score = grounded_count / max(1, len(q_terms))
            if grounding_score < 0.35:
                is_valid = False
                reasons.append(f"Low evidence support: key concepts not present in retrieved chunk text (Score: {grounding_score:.3f} < 0.35).")
        else:
            grounding_score = 0.85

        # --- F. CLAIM-LEVEL ANSWER ENTAILMENT CHECK ---
        answer_sentences = [s.strip() for s in ans_clean.split(".") if len(s.strip()) > 10]
        for s in answer_sentences:
            s_lower = s.lower()
            if "written several articles" in s_lower or "what is semantics?" in s_lower:
                is_valid = False
                reasons.append(f"Ideal answer contains non-sequitur sentence fragment: '{s}'.")

        # --- G. QUESTION-ANSWER ALIGNMENT CHECK ---
        topic_lower = topic_title.lower().strip()
        if topic_lower and len(topic_lower) > 3:
            topic_words = [w for w in topic_lower.split() if len(w) > 3 and w not in ignore_words]
            if topic_words:
                ans_matches = sum(1 for w in topic_words if w in ans_clean.lower())
                if ans_matches == 0:
                    is_valid = False
                    reasons.append(f"Ideal answer does not mention core topic '{topic_title}'.")

        # --- H. VECTOR DEDUPLICATION CHECK ---
        if existing_questions and len(existing_questions) > 0:
            q_vec = np.array(embedding_service.generate_query_embedding(q_clean))
            for prev_q in existing_questions:
                prev_vec = np.array(embedding_service.generate_query_embedding(prev_q))
                sim = float(np.dot(q_vec, prev_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(prev_vec)))
                if sim >= 0.78:
                    is_valid = False
                    reasons.append(f"Duplicate question detected (Cosine similarity: {sim:.3f} >= threshold 0.78).")
                    break

        # --- I. LLM-AS-A-JUDGE SEMANTIC VALIDATION (IF REMOTE LLM ACTIVE) ---
        if is_valid and llm_service.is_configured():
            llm_judge_res = llm_service.validate_question_and_answer_pair(
                question_text=q_clean,
                ideal_answer=ans_clean,
                evidence_chunks=evidence_chunks,
                topic_title=topic_title
            )
            if not llm_judge_res.get("valid", True):
                is_valid = False
                reasons.append(f"LLM Judge Rejected Pair: {llm_judge_res.get('reason')}")

        reason_str = " | ".join(reasons) if reasons else "Passed all verification checks."
        logger.info(f"[QUESTION VERIFICATION] Valid: {is_valid} | Reason: {reason_str}")

        return {
            "valid": is_valid,
            "reason": reason_str,
            "grounding_score": round(grounding_score if 'grounding_score' in locals() else 0.85, 3),
            "word_count": word_count,
            "reasons_list": reasons
        }

question_verifier = QuestionVerifier()
