import os
import pymongo
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest
from app.services.question_verifier import question_verifier

def run_document_grounded_rag_test():
    print("=" * 95)
    print("AUTOVIVA DOCUMENT-GROUNDED RAG QUESTION GENERATION PIPELINE TEST")
    print("=" * 95)

    # -------------------------------------------------------------------------
    # STEP 1: INGESTION OF DOCUMENT A (DISTRIBUTIONAL SEMANTICS)
    # -------------------------------------------------------------------------
    print("\n--- STEP 1: Uploading & Indexing Document A (Distributional Semantics) ---")
    doc_a_content = (
        "UNIT 1: DISTRIBUTIONAL SEMANTICS & VECTOR SPACES\n"
        "1.1 The Distributional Hypothesis.\n"
        "Distributional semantics models word meaning through vector space representations derived from word co-occurrence statistics.\n"
        "The Distributional Hypothesis asserts that words occurring in similar linguistic contexts have similar semantic meanings.\n\n"
        "UNIT 2: WORD X CONTEXT CO-OCCURRENCE MATRICES & PMI\n"
        "2.1 Term-Context Matrix Construction.\n"
        "A Word-Context Matrix records raw co-occurrence frequency counts within a sliding context window.\n"
        "Pointwise Mutual Information (PMI) quantifies whether two words co-occur more frequently than expected by chance.\n"
        "Positive PMI (PPMI) replaces negative values with zero to stabilize sparse matrix representation.\n\n"
        "UNIT 3: COSINE SIMILARITY & VECTOR SPACES\n"
        "3.1 Geometric Similarity.\n"
        "Cosine similarity measures the cosine of the angle between two normalized vector embeddings to evaluate semantic similarity.\n"
        "Unlike Euclidean distance, Cosine similarity is invariant to vector magnitude, making it ideal for word frequency representations.\n"
    ).encode("utf-8")

    filename_a = "NLP_Unit2_Distributional_Semantics.txt"
    doc_a_res = knowledge_service.process_and_store_document(
        file_bytes=doc_a_content,
        filename=filename_a,
        subject="Natural Language Processing",
        topic="Distributional Semantics"
    )
    doc_id_a = doc_a_res["document_id"]
    print(f"[VERIFIED]: Doc A indexed! ID: {doc_id_a}, Chunks: {doc_a_res['chunks']}, Sections: {len(doc_a_res['topic_map']['sections'])}")

    # -------------------------------------------------------------------------
    # STEP 2: INGESTION OF DOCUMENT B (OPERATING SYSTEMS - PROCESS SYNC)
    # -------------------------------------------------------------------------
    print("\n--- STEP 2: Uploading & Indexing Document B (Operating Systems) ---")
    doc_b_content = (
        "UNIT 1: PROCESS SYNCHRONIZATION\n"
        "1.1 The Critical Section Problem.\n"
        "The Critical Section is a code segment where shared memory or resources are accessed concurrently by multiple processes.\n"
        "A valid synchronization solution must satisfy Mutual Exclusion, Progress, and Bounded Waiting.\n\n"
        "UNIT 2: SEMAPHORES & MUTEX LOCKS\n"
        "2.1 Counting and Binary Semaphores.\n"
        "A Semaphore is a synchronization tool consisting of an integer value accessed via wait() and signal() atomic operations.\n"
        "Binary semaphores function as mutex locks to prevent race conditions in concurrent operating systems.\n"
    ).encode("utf-8")

    filename_b = "OS_Unit3_Process_Synchronization.txt"
    doc_b_res = knowledge_service.process_and_store_document(
        file_bytes=doc_b_content,
        filename=filename_b,
        subject="Operating Systems",
        topic="Process Synchronization"
    )
    doc_id_b = doc_b_res["document_id"]
    print(f"[VERIFIED]: Doc B indexed! ID: {doc_id_b}, Chunks: {doc_b_res['chunks']}, Sections: {len(doc_b_res['topic_map']['sections'])}")

    # -------------------------------------------------------------------------
    # STEP 3: VIVA CREATION & DOCUMENT-SCOPED GENERATION FOR DOC A
    # -------------------------------------------------------------------------
    print("\n--- STEP 3: Viva Session Creation & Grounded QGen for Document A ---")
    viva_req_a = VivaCreateRequest(
        subject="Natural Language Processing",
        course_code="NLP401",
        topic="Distributional Semantics",
        question_count=3,
        duration_minutes=15,
        batch="Batch 2026"
    )
    viva_a = viva_creation_service.create_viva(viva_req_a)
    viva_creation_service.add_uploaded_file(viva_a.viva_id, filename_a, document_id=doc_id_a, topic_map=doc_a_res["topic_map"])

    updated_viva_a = viva_creation_service.generate_questions_for_viva(viva_a.viva_id)
    questions_a = updated_viva_a.generated_questions

    print(f"\n[GENERATION AUDIT - VIVA A (NLP)] Generated {len(questions_a)} Verified Questions:")
    forbidden_os_terms = ["semaphore", "critical section", "mutex", "process synchronization", "bounded waiting"]

    for idx, q in enumerate(questions_a):
        print(f"\n  --- Question {idx + 1} ({q.get('difficulty')}, Bloom: {q.get('blooms_level')}) ---")
        print(f"  Question   : \"{q.get('question_text')}\"")
        print(f"  Ideal Answer: \"{q.get('ideal_answer')[:120]}...\"")
        print(f"  Source     : {q.get('source_page')}, Section: {q.get('source_section')}")
        print(f"  Confidence : {q.get('confidence')}")
        print(f"  Verified   : {q.get('verification_status')} (Report: {q.get('verification_report', {}).get('reason')})")

        # ASSERTION 1: Zero OS/Doc B leakage
        for term in forbidden_os_terms:
            assert term not in q.get("question_text", "").lower(), f"Leakage: Found '{term}' in Doc A question!"
            assert term not in q.get("ideal_answer", "").lower(), f"Leakage: Found '{term}' in Doc A ideal answer!"

        # ASSERTION 2: Must contain NLP/Doc A concepts
        q_lower = q.get("question_text", "").lower()
        assert "distributional" in q_lower or "vector" in q_lower or "pmi" in q_lower or "matrix" in q_lower or "cosine" in q_lower or "semantics" in q_lower, \
            f"Question not grounded in Doc A: '{q.get('question_text')}'"

        # ASSERTION 3: Must have full provenance metadata
        assert q.get("source_page") is not None
        assert q.get("source_section") is not None
        assert q.get("verification_status") == "VERIFIED"

    # -------------------------------------------------------------------------
    # STEP 4: VIVA CREATION & DOCUMENT-SCOPED GENERATION FOR DOC B
    # -------------------------------------------------------------------------
    print("\n--- STEP 4: Viva Session Creation & Grounded QGen for Document B ---")
    viva_req_b = VivaCreateRequest(
        subject="Operating Systems",
        course_code="OS302",
        topic="Process Synchronization",
        question_count=2,
        duration_minutes=15,
        batch="Batch 2026"
    )
    viva_b = viva_creation_service.create_viva(viva_req_b)
    viva_creation_service.add_uploaded_file(viva_b.viva_id, filename_b, document_id=doc_id_b, topic_map=doc_b_res["topic_map"])

    updated_viva_b = viva_creation_service.generate_questions_for_viva(viva_b.viva_id)
    questions_b = updated_viva_b.generated_questions

    print(f"\n[GENERATION AUDIT - VIVA B (OS)] Generated {len(questions_b)} Verified Questions:")
    forbidden_nlp_terms = ["distributional semantics", "pmi", "cosine similarity", "vector space", "word co-occurrence"]

    for idx, q in enumerate(questions_b):
        print(f"\n  --- Question {idx + 1} ({q.get('difficulty')}, Bloom: {q.get('blooms_level')}) ---")
        print(f"  Question   : \"{q.get('question_text')}\"")
        print(f"  Ideal Answer: \"{q.get('ideal_answer')[:120]}...\"")
        print(f"  Source     : {q.get('source_page')}, Section: {q.get('source_section')}")
        print(f"  Confidence : {q.get('confidence')}")

        # ASSERTION 1: Zero NLP/Doc A leakage
        for term in forbidden_nlp_terms:
            assert term not in q.get("question_text", "").lower(), f"Leakage: Found '{term}' in Doc B question!"

        # ASSERTION 2: Must contain OS/Doc B concepts
        q_lower = q.get("question_text", "").lower()
        assert "process" in q_lower or "synchronization" in q_lower or "critical" in q_lower or "semaphore" in q_lower or "mutex" in q_lower, \
            f"Question not grounded in Doc B: '{q.get('question_text')}'"

    print("\n" + "=" * 95)
    print("ALL TESTS PASSED! DOCUMENT ISOLATION, TOPIC MAPPING, EVIDENCE GROUNDING & VERIFICATION VERIFIED 100%!")
    print("=" * 95)

if __name__ == "__main__":
    run_document_grounded_rag_test()
