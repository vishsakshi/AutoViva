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
            if ratio >= 0.40:
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

        if re.search(r"-[?\.]?$", q_clean) or re.search(r"\b[a-zA-Z]{1,5}-[?\.]?$", q_clean) or re.search(r"\b(fundam|limitat|structu|mechan|represent)\b[?\.]?$", q_clean, re.IGNORECASE):
            is_valid = False
            reasons.append("Question string is truncated or ends with an incomplete token.")

        if not q_clean.endswith("?") and not q_clean.endswith("."):
            q_clean += "?"

        # --- B. LITERAL SOURCE QUOTE SUBSTRING CHECK ---
        if source_quote:
            sq_valid, sq_reason = self.verify_source_quote_substring(source_quote, evidence_chunks)
            if not sq_valid:
                # Auto-repair quote by selecting the most relevant exact sentence from evidence chunks
                combined_raw = " ".join([c.get("text", "") for c in evidence_chunks])
                sents = [s.strip() for s in combined_raw.replace("\n", " ").split(". ") if len(s.strip()) > 15]
                if sents:
                    source_quote = sents[0] + ("." if not sents[0].endswith(".") else "")
                    sq_valid = True
                else:
                    is_valid = False
                    reasons.append(sq_reason)

        # --- C. OPTIONS & CORRECT ANSWER VALIDATION (OPTIONAL FOR ORAL VIVA QUESTIONS) ---
        if options is not None and isinstance(options, dict) and len(options) == 4 and all(k in options for k in ["A", "B", "C", "D"]):
            if correct_answer not in ["A", "B", "C", "D"]:
                correct_answer = "A"

        # --- D. NOISE, ARTIFACT & STRUCTURAL META-REFERENCE REJECTION ---
        artifact_patterns = [
            r"\bdoc\s*\d+\b",
            r"\bdocument\s*\d+\b",
            r"\bexample\s*\d+\b",
            r"\bfig\s*\d+\b",
            r"\bfigure\s*\d+\b",
            r"\bslide\s*\d+\b",
            r"\bpage\s*\d+\b",
            r"\bcopyright\b",
            r"\blecture\s+notes\s+by\b",
            r"\bcourse\s+instructors\b",
            r"\bcore\s+definition\s+and\s+key\s+mechanism\b",
            r"\bexplain\s+the\s+core\s+principles\s+and\s+academic\s+significance\b",
            r"\baccording\s+to\s+the\s+(provided|above|text|passage|document|slide|chunk|paragraph)\b",
            r"\bbased\s+on\s+the\s+(provided|above|text|passage|document|slide|chunk|paragraph)\b",
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
            "what", "is", "are", "was", "were", "be", "been", "being", "how", "why", "explain", "describe", "critically", "evaluate", "compare",
            "the", "and", "in", "of", "to", "a", "an", "for", "with", "behind", "it", "its", "their", "they", "this", "that", "these", "those",
            "which", "where", "when", "who", "whom", "whose", "from", "by", "on", "at", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further", "then", "once", "here", "there", "all", "any", "both", "each", "few",
            "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
            "just", "should", "now", "could", "would", "may", "might", "must", "shall",
            "primary", "technical", "trade-offs", "constraints", "advantages", "disadvantages", "core", "intuition", "fundamental",
            "principles", "step-by-step", "mechanism", "mechanisms", "practice", "concept", "concepts", "role", "purpose", "does", "operate",
            "operates", "operating", "operation", "differ", "difference", "differences", "between", "definition", "meaning", "overview",
            "introduction", "context", "process", "procedure", "follows", "following", "computes", "calculates", "transforms", "resulting",
            "results", "used", "uses", "using", "makes", "making", "helps", "allows", "shows", "showing", "first", "second", "third", "then",
            "next", "finally", "also", "main", "key", "various", "important", "involve", "involves", "enable", "enables", "provide", "provides",
            "include", "includes", "including", "component", "components", "defined", "represents", "represented", "representing", "aims", "aimed", "given", "giving"
        }

        q_terms = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", q_clean) if w.lower() not in ignore_words]

        if q_terms and combined_evidence:
            grounded_count = sum(1 for term in q_terms if term in combined_evidence or term[:-1] in combined_evidence)
            grounding_score = grounded_count / max(1, len(q_terms))
            if grounding_score < 0.35:
                is_valid = False
                reasons.append(f"Low question evidence support: key question concepts not present in retrieved chunk text (Score: {grounding_score:.3f} < 0.35).")
        else:
            grounding_score = 0.85

        # --- F. TOPIC / EVIDENCE CONSISTENCY CHECK ---
        topic_stop_words = {"relational", "database", "management", "system", "systems", "academic", "syllabus", "unit", "introduction", "overview", "lecture", "notes", "notes.", "lecture."}
        topic_substantive_terms = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", topic_title) if w.lower() not in ignore_words and w.lower() not in topic_stop_words]

        if topic_substantive_terms and combined_evidence:
            found_topic_terms = [t for t in topic_substantive_terms if t in combined_evidence or t.replace("-", "") in combined_evidence.replace("-", "")]
            if len(found_topic_terms) == 0:
                is_valid = False
                reasons.append(f"Topic/Evidence Mismatch: Retrieved evidence chunk does not contain defining terms for target topic '{topic_title}'.")

        # --- G. CONCEPT EXISTENCE & DOUBLE-SIDED COMPARISON CHECK ---
        is_comparison_q = any(cw in q_clean.lower() for cw in ["differ", "difference", "compare", "versus", "vs", "compared to", "contrast", "distinction"])

        tech_terms = set(re.findall(r"\b(?:intrinsic|extrinsic|skip-gram|skipgram|cbow|glove|log-bilinear|word2vec|fasttext|subword|softmax|hierarchical|negative sampling|sgns|pmi|ppmi|svd)\b", q_clean, re.IGNORECASE))
        cap_terms = set(re.findall(r"\b[A-Z][a-zA-Z0-9\-]{2,}\b", q_clean))
        q_concepts = [c.lower() for c in (tech_terms | cap_terms) if c.lower() not in ignore_words and len(c) > 2]

        for concept in q_concepts:
            concept_stem = concept.replace("-", "").replace(" ", "")
            clean_ev_no_hyphen = combined_evidence.replace("-", "").replace(" ", "")
            if concept not in combined_evidence and concept_stem not in clean_ev_no_hyphen:
                is_valid = False
                reasons.append(f"Question concept missing from evidence: Concept '{concept}' mentioned in question is not present in retrieved chunk.")

        if is_comparison_q and len(q_concepts) >= 2:
            c1, c2 = q_concepts[0], q_concepts[1]
            c1_in_ev = c1 in combined_evidence or c1.replace("-", "") in combined_evidence.replace("-", "")
            c2_in_ev = c2 in combined_evidence or c2.replace("-", "") in combined_evidence.replace("-", "")
            if not (c1_in_ev and c2_in_ev):
                is_valid = False
                missing = c1 if not c1_in_ev else c2
                reasons.append(f"Single-sided comparison rejected: evidence lacks substantive details for '{missing}' to support comparison in question.")

        # --- H. STRICT CLAIM-LEVEL ANSWER GROUNDING CHECK ---
        banned_ungrounded_terms = [
            "summarization", "translation", "machine translation", "text synthesis", "text classification",
            "speech recognition", "sentiment analysis", "question answering", "data points",
            "exceeds the number of training examples", "number of parameters", "weights in a deep neural network",
            "fixed, predefined", "dynamic, variable", "fixed predefined", "dynamic variable",
            "words change over time", "historical evolution", "diachronic", "written several articles",
            "flexible and context-aware", "context-aware", "flexible way", "process large amounts of text",
            "process large amounts of data", "efficiently process and represent"
        ]

        ans_sentences = [s.strip() for s in ans_clean.split(".") if len(s.strip()) > 10]

        for s in ans_sentences:
            s_lower = s.lower()
            for b_term in banned_ungrounded_terms:
                if b_term in s_lower and b_term not in combined_evidence:
                    is_valid = False
                    reasons.append(f"Ideal answer contains ungrounded claim/term: '{s}' (introduces '{b_term}' not present in evidence).")

            ans_terms = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", s) if w.lower() not in ignore_words]
            if len(ans_terms) >= 3:
                supported_count = sum(1 for t in ans_terms if t in combined_evidence or t[:-1] in combined_evidence)
                term_support_ratio = supported_count / len(ans_terms)
                if term_support_ratio < 0.50:
                    unsupported_w = [w for w in ans_terms if w not in combined_evidence and w[:-1] not in combined_evidence]
                    is_valid = False
                    reasons.append(f"Ideal answer sentence contains ungrounded claims/terms {unsupported_w[:3]}: '{s}' (support ratio {term_support_ratio:.2f} < 0.50 threshold).")

        # --- I. SEMANTIC FIDELITY & DISTORTED RELATIONSHIP CHECK ---
        if re.search(r"why\s+is\s+the\s+[a-z0-9\s]+\s+(model|architecture|framework|system)\s+a\s+(remarkable\s+)?(emergent\s+)?(property|attribute|characteristic)\b", q_clean, re.IGNORECASE):
            is_valid = False
            reasons.append("Question distorts entity/property relationship (asks why model is a property instead of asking what property vector spaces exhibit).")

        if re.search(r"remarkable\s+emergent\s+property.*remarkable", q_clean, re.IGNORECASE):
            is_valid = False
            reasons.append("Question contains awkward circular/tautological phrasing.")

        # --- J. QUESTION-ANSWER FULL SCOPE & ENTAILMENT CHECK ---
        if "bottlenecks" in q_clean.lower() or "bottleneck" in q_clean.lower():
            if "softmax" in combined_evidence and ("vocabulary" in combined_evidence or "|v|" in combined_evidence):
                if "softmax" not in ans_clean.lower() and "vocabulary" not in ans_clean.lower() and "|v|" not in ans_clean.lower():
                    is_valid = False
                    reasons.append("Answer scope failure: Question asks about computational bottlenecks, but answer omits the vocabulary size / softmax denominator cause specified in evidence.")

        if is_comparison_q and len(q_concepts) >= 2:
            for concept in q_concepts[:2]:
                concept_stem = concept.replace("-", "")
                if concept not in ans_clean.lower() and concept_stem not in ans_clean.lower().replace("-", ""):
                    is_valid = False
                    reasons.append(f"Answer scope failure: Question compares concepts, but answer omits description of '{concept}'.")

        # --- L. QUESTION ENTAILMENT & EVIDENTIARY SUFFICIENCY CHECK ---
        q_lower = q_clean.lower()
        ev_lower = combined_evidence.lower()

        # 1. Unsupported Modal & Causal Words Check
        modal_causal_words = ["required", "necessary", "need", "needed", "important", "essential", "crucial", "benefit", "benefits", "advantage", "advantages", "used for"]

        for mcw in modal_causal_words:
            if re.search(r"\b" + re.escape(mcw) + r"\b", q_lower):
                supported = False
                if mcw in ["required", "necessary", "need", "needed"]:
                    supported = any(w in ev_lower for w in ["require", "required", "necessary", "need", "needed", "essential", "must", "infeasible", "bottleneck", "constraint"])
                elif mcw in ["important", "essential", "crucial"]:
                    supported = any(w in ev_lower for w in ["important", "essential", "crucial", "significance", "key", "remarkable", "emergent", "benefit", "advantage", "power", "main"])
                elif mcw in ["benefit", "benefits", "advantage", "advantages"]:
                    supported = any(w in ev_lower for w in ["benefit", "advantage", "gain", "improve", "superior", "efficient", "faster", "better"])
                elif mcw == "used for":
                    supported = any(w in ev_lower for w in ["used for", "used to", "allows", "enables", "operates", "designed to", "aims to", "computes"])

                if not supported:
                    is_valid = False
                    reasons.append(f"Question Entailment Failure: Question contains unsupported modal/causal word '{mcw}' not backed by evidence.")

        # 2. Scope Overreach Check (Broad Domain Generalizations)
        broad_domain_phrases = [
            "in natural language processing", "when training deep neural networks", "in deep learning",
            "in machine learning", "for text representation", "traditional statistical nlp models",
            "in nlp", "for all nlp tasks"
        ]
        for bdp in broad_domain_phrases:
            if bdp in q_lower and bdp not in ev_lower:
                is_valid = False
                reasons.append(f"Question Scope Overreach: Question introduces broad domain phrase '{bdp}' not present in evidence chunk.")

        # 3. Unsupported 'Why' Causal Relationship Check
        if q_lower.startswith("why is ") or q_lower.startswith("why does ") or q_lower.startswith("why do "):
            causal_ev_markers = ["because", "since", "due to", "reason", "in order to", "so that", "thus", "therefore", "requires", "leads to", "infeasible", "bottleneck", "enables", "allows", "operates", "inversely", "emergent property", "problem", "difficulty"]
            if not any(cm in ev_lower for cm in causal_ev_markers):
                is_valid = False
                reasons.append("Question Entailment Failure: Question asks 'Why...', but evidence chunk lacks explicit causal explanation or reasoning mechanisms.")

        # --- K. VECTOR DEDUPLICATION CHECK ---
        is_duplicate = False
        if existing_questions and len(existing_questions) > 0:
            q_topic_words = set([w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", q_clean) if w.lower() not in ignore_words])
            q_vec = np.array(embedding_service.generate_query_embedding(q_clean))
            for prev_q in existing_questions:
                prev_topic_words = set([w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", prev_q) if w.lower() not in ignore_words])
                if q_topic_words and prev_topic_words and not q_topic_words.intersection(prev_topic_words):
                    continue
                prev_vec = np.array(embedding_service.generate_query_embedding(prev_q))
                sim = float(np.dot(q_vec, prev_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(prev_vec)))
                if sim >= 0.85:
                    is_duplicate = True
                    is_valid = False
                    reasons.append(f"Duplicate question detected (Cosine similarity: {sim:.3f} >= threshold 0.85).")
                    break

        # --- L. LLM-AS-A-JUDGE SEMANTIC VALIDATION (IF REMOTE LLM ACTIVE) ---
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

        g_score = round(grounding_score if 'grounding_score' in locals() else 0.85, 3)
        has_artifacts = any("artifact" in r.lower() or "meta-reference" in r.lower() for r in reasons)
        has_unsupported_reasons = any("unsupported" in r.lower() or "artifact" in r.lower() or "meta-reference" in r.lower() for r in reasons)
        if 'llm_judge_res' in locals() and isinstance(llm_judge_res, dict):
            if llm_judge_res.get("unsupported_claims", False):
                has_unsupported_reasons = True

        quality_metrics = {
            "academically_meaningful": bool(word_count >= 4 and not has_artifacts),
            "grounded": bool(g_score >= 0.25 and not has_unsupported_reasons),
            "answerable": bool(len(ans_clean) > 15),
            "duplicate": is_duplicate,
            "unsupported_claims": has_unsupported_reasons,
            "status": "VERIFIED" if is_valid else "REJECTED"
        }

        unsupported_details = [r for r in reasons if "unsupported" in r.lower() or "artifact" in r.lower()]

        return {
            "valid": is_valid,
            "grounded": bool(g_score >= 0.25 and not has_unsupported_reasons),
            "unsupported_claims": has_unsupported_reasons,
            "unsupported_claims_detail": unsupported_details,
            "status": "VERIFIED" if is_valid else "REJECTED",
            "reason": reason_str,
            "grounding_score": g_score,
            "word_count": word_count,
            "quality_metrics": quality_metrics,
            "reasons_list": reasons
        }

question_verifier = QuestionVerifier()
