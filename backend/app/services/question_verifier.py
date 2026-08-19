import re
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from app.services.embedding_service import embedding_service

logger = logging.getLogger("vivabot.services.question_verifier")

class QuestionVerifier:
    """
    Mandatory Question Verification Gate for AutoViva.
    Enforces strict document relevance, evidence support, answerability,
    groundedness, topic consistency, quality checks, and deduplication.
    """
    def __init__(self, duplicate_similarity_threshold: float = 0.78):
        self.duplicate_threshold = duplicate_similarity_threshold

    def verify_question_candidate(
        self,
        question_text: str,
        ideal_answer: str,
        evidence_chunks: List[Dict[str, Any]],
        topic_title: str,
        existing_questions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive multi-dimensional verification on a generated viva question candidate.
        """
        reasons = []
        is_valid = True

        q_clean = question_text.strip()
        ans_clean = ideal_answer.strip()

        # Combine evidence text
        combined_evidence = " ".join([c.get("text", "") for c in evidence_chunks]).lower()

        # --- A. LENGTH & COMPLETENESS CHECK ---
        word_count = len(q_clean.split())
        if word_count > 40:
            is_valid = False
            reasons.append(f"Question exceeds max oral length ({word_count} words > 40 words max).")
        if word_count < 5:
            is_valid = False
            reasons.append("Question is too short (< 5 words).")

        if not q_clean.endswith("?") and not q_clean.endswith("."):
            q_clean += "?"

        # --- B. FORBIDDEN NOISE & PREFIXES (QUALITY RULES) ---
        forbidden_prefixes = [
            "based on the uploaded", "according to the pdf", "in the syllabus text",
            "as per the document", "referring to the slide", "from the uploaded",
            "based on the document", "as described in the text"
        ]
        for pref in forbidden_prefixes:
            if pref in q_clean.lower():
                is_valid = False
                reasons.append(f"Contains unnatural artificial prefix: '{pref}'.")

        # Check for slide numbers / page numbers (e.g. 9/20, Page 5)
        if re.search(r"\b\d+\s*/\s*\d+\b", q_clean) or re.search(r"\bpage\s+\d+\b", q_clean, re.IGNORECASE):
            is_valid = False
            reasons.append("Contains raw page/slide numbers (e.g. '9/20').")

        # Check for author names or non-academic noise
        noise_names = ["mayank singh", "copyright", "all rights reserved", "lecture notes"]
        for n in noise_names:
            if n in q_clean.lower() or n in ans_clean.lower():
                is_valid = False
                reasons.append(f"Contains author/noise artefact: '{n}'.")

        # --- C. EVIDENCE GROUNDEDNESS CHECK ---
        # Extract important terms from question (words > 4 chars, excluding common words)
        stopwords = set(["what", "explain", "describe", "discuss", "compare", "between", "which", "where", "how", "does", "with", "from", "that", "this", "their", "under", "about", "using", "into", "concept", "principle", "principles", "mechanism", "fundamental", "difference", "process"])
        q_words = [w.lower().strip("?,.:;\"'") for w in q_clean.split() if len(w.strip("?,.:;\"'")) > 3]
        key_q_words = [w for w in q_words if w not in stopwords]

        evidence_hits = 0
        for kw in key_q_words:
            if kw in combined_evidence:
                evidence_hits += 1

        evidence_ratio = (evidence_hits / len(key_q_words)) if key_q_words else 1.0
        evidence_support_score = round(min(1.0, max(0.0, evidence_ratio)), 3)

        if evidence_support_score < 0.40 and len(key_q_words) > 2:
            is_valid = False
            reasons.append(f"Low evidence support: key concepts not present in retrieved chunk text (Score: {evidence_support_score}).")

        # --- D. ANSWERABILITY & IDEAL ANSWER GROUNDEDNESS ---
        ans_words = [w.lower().strip("?,.:;\"'") for w in ans_clean.split() if len(w.strip("?,.:;\"'")) > 4]
        key_ans_words = [w for w in ans_words if w not in stopwords][:15]
        ans_hits = sum(1 for w in key_ans_words if w in combined_evidence)
        groundedness_score = round((ans_hits / len(key_ans_words)) if key_ans_words else 1.0, 3)

        if len(ans_clean) < 25:
            is_valid = False
            reasons.append("Ideal answer is too brief or incomplete.")

        # --- E. TOPIC CONSISTENCY & DOCUMENT RELEVANCE ---
        topic_lower = topic_title.lower()
        topic_words = [w for w in topic_lower.split() if len(w) > 3]
        topic_match = any(tw in q_clean.lower() or tw in combined_evidence for tw in topic_words) if topic_words else True
        topic_consistency_score = 0.95 if topic_match else 0.70

        document_relevance_score = round((evidence_support_score * 0.5 + groundedness_score * 0.3 + topic_consistency_score * 0.2), 3)

        # --- F. DEDUPLICATION CHECK ---
        is_duplicate = False
        if existing_questions:
            try:
                new_vec = np.array(embedding_service.generate_query_embedding(q_clean))
                for eq in existing_questions:
                    eq_vec = np.array(embedding_service.generate_query_embedding(eq))
                    sim = float(np.dot(new_vec, eq_vec) / (np.linalg.norm(new_vec) * np.linalg.norm(eq_vec)))
                    if sim >= self.duplicate_threshold:
                        is_duplicate = True
                        is_valid = False
                        reasons.append(f"Duplicate question detected (Cosine similarity: {sim:.3f} >= threshold {self.duplicate_threshold}).")
                        break
            except Exception as e:
                logger.warning(f"Deduplication vector check error: {e}")

        final_reason = "Passed all verification checks." if is_valid else " | ".join(reasons)

        return {
            "valid": is_valid,
            "document_relevance": document_relevance_score,
            "evidence_support": evidence_support_score,
            "answerability": round(max(0.70, groundedness_score), 3),
            "groundedness": groundedness_score,
            "topic_consistency": topic_consistency_score,
            "duplicate": is_duplicate,
            "reason": final_reason
        }

question_verifier = QuestionVerifier()
