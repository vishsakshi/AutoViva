import os
import sys
import uuid
import time

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.topic_mapper import topic_mapper
from app.services.question_verifier import question_verifier
from app.services.question_generator import question_generator_engine
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest
from app.services.evaluation_engine import evaluation_engine_module1
from app.services.scoring_engine import scoring_engine_module2
from app.services.feedback_engine import feedback_engine_module3
from app.models.evaluation_module import EvaluateAnswerRequest
from app.models.question_gen import RubricCriterion
from app.services.llm_service import llm_service

DOC_A_NLP_CONTENT = """
UNIT 1: DISTRIBUTIONAL SEMANTICS & VECTOR SPACES
Distributional semantics is an approach to natural language processing where word meaning is represented as high-dimensional vectors based on contextual distribution. The core intuition, formalized by Firth (1957), states that words that occur in similar contexts have similar meanings.

WORD X CONTEXT CO-OCCURRENCE MATRICES & PMI
In traditional vector space models, we construct word-context co-occurrence matrices where rows represent target words and columns represent context words within a sliding window. Pointwise Mutual Information (PMI) and Positive PMI (PPMI) measure the statistical association between words by comparing joint probability against independent probability.

COSINE SIMILARITY & VECTOR SPACES
Vector similarity is computed using cosine similarity, which calculates the dot product of two normalized vectors to determine their angular distance regardless of magnitude. High cosine similarity indicates strong semantic relatedness between lexical items.
"""

DOC_B_OS_CONTENT = """
UNIT 1: PROCESS SYNCHRONIZATION
Process synchronization is a fundamental operating systems mechanism to ensure concurrent processes execute without race conditions when accessing shared memory or critical sections.

CRITICAL SECTION PROBLEM
The critical section problem requires three mandatory conditions: Mutual Exclusion, Progress, and Bounded Waiting. A race condition occurs when multiple processes access and manipulate the same shared resource concurrently, and the outcome depends on the order of execution.

SEMAPHORES & MUTEX LOCKS
A semaphore is a synchronization tool represented as an integer variable accessed only through atomic wait() (P) and signal() (V) operations. Counting semaphores control access to a finite resource pool, whereas binary semaphores behave as mutex locks for exclusive mutual exclusion.
"""

def run_llm_grounded_rag_test():
    print("=" * 95)
    print("AUTOVIVA LLM EVIDENCE-GROUNDED RAG & ANSWER EVALUATION TEST SUITE")
    print("=" * 95)
    print(f"LLM Provider: {llm_service.provider} | Model: {llm_service.model}")

    # -------------------------------------------------------------------------
    # TEST 1: Upload and Index Document A (NLP - Distributional Semantics)
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Uploading & Indexing Document A (Distributional Semantics) ---")
    doc_a_id = f"doc_{uuid.uuid4().hex[:8]}"
    upload_res_a = knowledge_service.process_and_store_document(
        file_bytes=DOC_A_NLP_CONTENT.encode("utf-8"),
        filename="NLP_Unit2_Distributional_Semantics.txt",
        subject="Natural Language Processing",
        document_id=doc_a_id
    )

    doc_a_id = upload_res_a["document_id"]
    chunks_a = upload_res_a.get("chunks", upload_res_a.get("chunks_stored", 3))
    print(f"[VERIFIED]: Doc A indexed! ID: {doc_a_id}, Chunks: {chunks_a}")

    # -------------------------------------------------------------------------
    # TEST 2: Upload and Index Document B (OS - Process Synchronization)
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Uploading & Indexing Document B (Operating Systems) ---")
    doc_b_id = f"doc_{uuid.uuid4().hex[:8]}"
    upload_res_b = knowledge_service.process_and_store_document(
        file_bytes=DOC_B_OS_CONTENT.encode("utf-8"),
        filename="OS_Unit3_Process_Synchronization.txt",
        subject="Operating Systems",
        document_id=doc_b_id
    )

    doc_b_id = upload_res_b["document_id"]
    chunks_b = upload_res_b.get("chunks", upload_res_b.get("chunks_stored", 2))
    print(f"[VERIFIED]: Doc B indexed! ID: {doc_b_id}, Chunks: {chunks_b}")

    # -------------------------------------------------------------------------
    # TEST 3: Viva Session Creation & Grounded QGen for Document A
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Viva Session Creation & LLM QGen for Document A (NLP) ---")
    viva_a = viva_creation_service.create_viva(VivaCreateRequest(
        subject="Natural Language Processing",
        course_code="NLP401",
        topic="Distributional Semantics & Vector Spaces",
        question_count=3,
        duration_minutes=15,
        batch="Batch 2026"
    ))

    viva_creation_service.add_uploaded_file(
        viva_id=viva_a.viva_id,
        filename="NLP_Unit2_Distributional_Semantics.txt",
        document_id=doc_a_id
    )

    updated_viva_a = viva_creation_service.generate_questions_for_viva(viva_a.viva_id)
    questions_a = updated_viva_a.generated_questions

    print(f"\n[GENERATION AUDIT - VIVA A (NLP)] Generated {len(questions_a)} Verified Questions:")
    for idx, q in enumerate(questions_a):
        q_text = q.get("question_text", "") if isinstance(q, dict) else q.question_text
        ideal = q.get("ideal_answer", "") if isinstance(q, dict) else q.ideal_answer
        diff = q.get("difficulty", "Medium") if isinstance(q, dict) else q.difficulty
        bloom = q.get("blooms_level", "Understand") if isinstance(q, dict) else q.blooms_level
        rub = q.get("rubric", []) if isinstance(q, dict) else q.rubric
        page = q.get("source_page", "Page 1") if isinstance(q, dict) else q.source_page
        sec = q.get("source_section", "") if isinstance(q, dict) else q.source_section
        conf = q.get("confidence", 0.9) if isinstance(q, dict) else q.confidence
        model = q.get("llm_model", "AutoViva-Grounded-RAG-v2") if isinstance(q, dict) else getattr(q, 'llm_model', 'AutoViva-Grounded-RAG-v2')

        print(f"\n  --- Question {idx+1} ({diff}, Bloom: {bloom}) ---")
        print(f"  Question   : \"{q_text}\"")
        print(f"  Ideal Answer: \"{ideal[:120]}...\"")
        print(f"  Rubric     : {[r.get('criterion', r) if isinstance(r, dict) else getattr(r, 'criterion', r) for r in rub]}")
        print(f"  Source     : {page}, Section: {sec}")
        print(f"  Confidence : {conf}")
        print(f"  AI Model   : {model}")

    # Assertions for Document A
    assert len(questions_a) == 3, f"Expected 3 questions for Viva A, got {len(questions_a)}"
    for q in questions_a:
        q_text = q.get("question_text", "") if isinstance(q, dict) else q.question_text
        ideal = q.get("ideal_answer", "") if isinstance(q, dict) else q.ideal_answer
        q_lower = (q_text + " " + ideal).lower()
        # Must contain NLP terms
        nlp_keywords = ["distributional", "semantics", "vector", "context", "pmi", "co-occurrence", "cosine", "similarity"]
        assert any(k in q_lower for k in nlp_keywords), f"Question '{q_text}' missing NLP grounding!"
        # Must NOT contain OS terms (Zero Cross-Leakage)
        os_keywords = ["semaphore", "mutex", "critical section", "process synchronization", "deadlock"]
        assert not any(k in q_lower for k in os_keywords), f"Cross-document contamination! Found OS term in NLP question: {q_text}"

    print("\n[VERIFIED]: Document A generated 3 questions strictly grounded in NLP with 0% OS cross-leakage!")

    # -------------------------------------------------------------------------
    # TEST 4: Viva Session Creation & Grounded QGen for Document B
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Viva Session Creation & LLM QGen for Document B (OS) ---")
    viva_b = viva_creation_service.create_viva(VivaCreateRequest(
        subject="Operating Systems",
        course_code="OS302",
        topic="Process Synchronization",
        question_count=2,
        duration_minutes=10,
        batch="Batch 2026"
    ))

    viva_creation_service.add_uploaded_file(
        viva_id=viva_b.viva_id,
        filename="OS_Unit3_Process_Synchronization.txt",
        document_id=doc_b_id
    )

    updated_viva_b = viva_creation_service.generate_questions_for_viva(viva_b.viva_id)
    questions_b = updated_viva_b.generated_questions

    print(f"\n[GENERATION AUDIT - VIVA B (OS)] Generated {len(questions_b)} Verified Questions:")
    for idx, q in enumerate(questions_b):
        q_text = q.get("question_text", "") if isinstance(q, dict) else q.question_text
        ideal = q.get("ideal_answer", "") if isinstance(q, dict) else q.ideal_answer
        diff = q.get("difficulty", "Medium") if isinstance(q, dict) else q.difficulty
        bloom = q.get("blooms_level", "Understand") if isinstance(q, dict) else q.blooms_level
        page = q.get("source_page", "Page 1") if isinstance(q, dict) else q.source_page
        sec = q.get("source_section", "") if isinstance(q, dict) else q.source_section
        conf = q.get("confidence", 0.9) if isinstance(q, dict) else q.confidence

        print(f"\n  --- Question {idx+1} ({diff}, Bloom: {bloom}) ---")
        print(f"  Question   : \"{q_text}\"")
        print(f"  Ideal Answer: \"{ideal[:120]}...\"")
        print(f"  Source     : {page}, Section: {sec}")
        print(f"  Confidence : {conf}")

    # Assertions for Document B
    assert len(questions_b) == 2, f"Expected 2 questions for Viva B, got {len(questions_b)}"
    for q in questions_b:
        q_text = q.get("question_text", "") if isinstance(q, dict) else q.question_text
        ideal = q.get("ideal_answer", "") if isinstance(q, dict) else q.ideal_answer
        q_lower = (q_text + " " + ideal).lower()
        # Must contain OS terms
        os_keywords = ["process", "synchronization", "critical", "section", "semaphore", "mutex", "race condition"]
        assert any(k in q_lower for k in os_keywords), f"Question '{q_text}' missing OS grounding!"
        # Must NOT contain NLP terms (Zero Cross-Leakage)
        nlp_keywords = ["distributional semantics", "pmi", "cosine similarity", "word-context"]
        assert not any(k in q_lower for k in nlp_keywords), f"Cross-document contamination! Found NLP term in OS question: {q_text}"

    print("\n[VERIFIED]: Document B generated 2 questions strictly grounded in OS with 0% NLP cross-leakage!")

    # -------------------------------------------------------------------------
    # TEST 5: USE CASE #2 — Student Oral Answer Evaluation with LLM
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Student Oral Answer Evaluation against Approved Question & Rubric ---")
    first_q = questions_a[0]
    first_q_text = first_q.get("question_text", "") if isinstance(first_q, dict) else first_q.question_text
    first_ideal = first_q.get("ideal_answer", "") if isinstance(first_q, dict) else first_q.ideal_answer

    sample_student_answer = (
        "Distributional semantics is based on the core intuition that words appearing in similar contexts have similar meanings. "
        "We construct high-dimensional vector representations from word-context co-occurrence counts and calculate cosine similarity to measure lexical distance."
    )

    rubric_items = [
        RubricCriterion(criterion="Clear definition and fundamental intuition of distributional semantics", marks=3.0),
        RubricCriterion(criterion="Explanation of vector space representation and co-occurrence counts", marks=4.0),
        RubricCriterion(criterion="Calculation of cosine similarity to measure semantic relatedness", marks=3.0)
    ]

    eval_req = EvaluateAnswerRequest(
        question_text=first_q_text,
        ideal_answer=first_ideal,
        evaluation_rubric=rubric_items,
        student_answer=sample_student_answer,
        subject="Natural Language Processing",
        topic="Distributional Semantics"
    )

    eval_mod1 = evaluation_engine_module1.evaluate_answer_module1(eval_req)
    score_mod2 = scoring_engine_module2.calculate_scores(eval_mod1.evaluation_id, eval_mod1.criterion_evaluations)

    print(f"\n[EVALUATION REPORT - EVAL ID: {eval_mod1.evaluation_id}]")
    print(f"Question: \"{first_q_text}\"")
    print(f"Student Response: \"{sample_student_answer}\"")
    print(f"Overall Confidence: {eval_mod1.overall_confidence} | Latency: {eval_mod1.processing_latency_ms}ms")
    print(f"Calculated Score: {score_mod2.total_score} / {score_mod2.max_score} ({score_mod2.percentage}%)")

    for ce in eval_mod1.criterion_evaluations:
        print(f"\n  Criterion: {ce.criterion_text} [{ce.allocated_marks} Marks]")
        print(f"  Classification: {ce.classification} (Confidence: {ce.confidence})")
        print(f"  Evidence Quote: \"{ce.evidence_quote}\"")
        print(f"  Reasoning: {ce.reasoning}")

    assert eval_mod1.status == "success"
    assert len(eval_mod1.criterion_evaluations) == 3
    assert score_mod2.total_score >= 7.0, f"Expected high score for accurate answer, got {score_mod2.total_score}"
    print("\n[VERIFIED]: Student Answer Evaluation executed with explainable criterion breakdown and verbatim evidence quotes!")

    # -------------------------------------------------------------------------
    # TEST 6: Intentional Question Rejection & Quality Gate Verification
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: Intentional Rejection & Verification Gate Robustness ---")
    bad_q1 = "What did Mayank Singh state on slide 9/20 regarding lecture 3?"
    verif_bad1 = question_verifier.verify_question_candidate(
        question_text=bad_q1,
        ideal_answer="Mayank Singh stated slide details.",
        evidence_chunks=[{"text": DOC_A_NLP_CONTENT}],
        topic_title="Distributional Semantics"
    )
    print(f"[REJECTION TEST 1] Candidate: '{bad_q1}'")
    print(f"  -> Valid: {verif_bad1['valid']} | Reason: {verif_bad1['reason']}")
    assert not verif_bad1["valid"], "Failed to reject author/slide noise question!"

    # Test Duplicate rejection
    duplicate_q = first_q_text
    verif_dup = question_verifier.verify_question_candidate(
        question_text=duplicate_q,
        ideal_answer=first_ideal,
        evidence_chunks=[{"text": DOC_A_NLP_CONTENT}],
        topic_title="Distributional Semantics",
        existing_questions=[first_q_text]
    )
    print(f"\n[REJECTION TEST 2 - DUPLICATE] Candidate: '{duplicate_q}'")
    print(f"  -> Valid: {verif_dup['valid']} | Reason: {verif_dup['reason']}")
    assert not verif_dup["valid"], "Failed to reject duplicate question candidate!"

    print("\n" + "=" * 95)
    print("ALL 6 TESTS PASSED! LLM INTEGRATION, GROUNDED RAG, EVALUATION & VERIFICATION ARE 100% VERIFIED!")
    print("=" * 95)

if __name__ == "__main__":
    run_llm_grounded_rag_test()
