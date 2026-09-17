import os
import sys
import logging
import json
import time
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("autoviva.e2e_test")

from app.core.config import settings
from app.services.llm_service import llm_service
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.question_generator import question_generator_engine
from app.services.question_verifier import question_verifier
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def run_e2e_real_app_flow():
    print("\n" + "=" * 95)
    print("AUTOVIVA END-TO-END REAL APPLICATION FLOW TEST")
    print("=" * 95 + "\n")

    # 1. Verify LLM Configuration
    print("--- [STAGE 1] LLM Service Configuration & Availability ---")
    print(f"Provider: {llm_service.provider}")
    print(f"Model: {llm_service.model}")
    print(f"API URL: {llm_service.api_url}")
    print(f"Is Configured: {llm_service.is_configured()}")
    assert llm_service.is_configured(), "LLM Service is not configured!"
    print("[PASS] STAGE 1: Real Ollama LLM endpoint available.\n")

    # 2. Real Faculty PDF Upload Workflow
    pdf_file_path = os.path.join(BASE_DIR, "database_systems_academic_syllabus.pdf")
    assert os.path.exists(pdf_file_path), f"Actual PDF file '{pdf_file_path}' does not exist!"

    print("--- [STAGE 2] Faculty Step 1: Viva Session Creation ---")
    create_req = VivaCreateRequest(
        subject="Database Management Systems",
        course_code="CS401",
        topic="Transactions, Concurrency, Indexing & Query Optimization",
        difficulty="Medium",
        question_count=10,
        duration_minutes=30,
        batch="2026-CS"
    )
    viva_record = viva_creation_service.create_viva(create_req)
    viva_id = viva_record.viva_id
    print(f"Created Viva ID: '{viva_id}' | Subject: '{viva_record.subject}' | Target Questions: {viva_record.question_count}\n")

    print("--- [STAGE 3] Faculty Step 2: Uploading Actual Academic PDF ---")
    with open(pdf_file_path, "rb") as f:
        file_bytes = f.read()

    upload_res = knowledge_service.process_and_store_document(
        file_bytes=file_bytes,
        filename="database_systems_academic_syllabus.pdf",
        subject=viva_record.subject,
        topic=viva_record.topic,
        viva_id=viva_id
    )

    doc_id = upload_res["document_id"]
    print(f"Ingested Document ID: '{doc_id}'")
    print(f"Extracted Chunks Count: {upload_res['chunks_stored']}")
    
    # Store uploaded file metadata in viva record
    viva_creation_service.add_uploaded_file(
        viva_id=viva_id,
        filename="database_systems_academic_syllabus.pdf",
        document_id=doc_id,
        topic_map=upload_res.get("topic_map")
    )

    chunks = vector_store.get_document_chunks(doc_id)
    print(f"Stored Chunks in Vector Store: {len(chunks)}")
    for idx, c in enumerate(chunks, 1):
        print(f"  Chunk {idx}: ID={c['chunk_id']} | Page={c['metadata'].get('page')} | Section='{c['metadata'].get('section_title')}' | Snippet='{c['text'][:90]}...'")
    print("[PASS] STAGE 3: Document extracted, chunked, embedded, and stored in ChromaDB.\n")

    # 3. Real Ollama Question Generation & Review Queue Staging
    print("--- [STAGE 4] Real Ollama Question & Ideal Answer Generation (Target: 8-10 Questions) ---")
    gen_record = viva_creation_service.generate_questions_for_viva(viva_id)
    
    staged_questions = gen_record.generated_questions
    print(f"\nSuccessfully Generated & Verified {len(staged_questions)} Viva Questions for Faculty Review Queue!")
    assert len(staged_questions) >= 8, f"Expected at least 8 generated questions, got {len(staged_questions)}!"

    print("\n" + "=" * 95)
    print("DETAILED 10-QUESTION PROVENANCE & GROUNDING AUDIT REPORT")
    print("=" * 95)

    covered_sections = set()
    for idx, q in enumerate(staged_questions, 1):
        q_text = q.get("question_text") or q.get("question")
        ans_text = q.get("ideal_answer")
        sec_title = q.get("section") or q.get("source_section") or "General"
        covered_sections.add(sec_title)
        
        chunk_id = q.get("source_chunk") or (q.get("source_chunk_ids", ["N/A"])[0] if q.get("source_chunk_ids") else "N/A")
        quote = q.get("source_quote", "N/A")
        concept = q.get("topic") or q.get("topic_title", "Core Concept")
        quality = q.get("validation_report", {}).get("quality_metrics", {})

        print(f"\n--- Question #{idx} ---")
        print(f"Concept/Topic: {concept}")
        print(f"Question: \"{q_text}\"")
        print(f"Retrieved Source Section/Chunk: {sec_title} (Chunk ID: {chunk_id})")
        print(f"Evidence Used: \"{quote}\"")
        print(f"Ideal Answer: \"{ans_text}\"")
        print(f"Grounding Result: Grounded={quality.get('grounded')} | Unsupported Claims={quality.get('unsupported_claims')}")
        print(f"Verification Result: Status={quality.get('status')} | Meaningful={quality.get('academically_meaningful')}")

        # Assert criteria per question
        q_lower = q_text.lower()
        ans_lower = ans_text.lower()

        # Check A: No DOC/OUTPUT/header artifacts
        for artifact in ["doc 1", "output", "page 1", "page 2", "slide", "written several"]:
            assert artifact not in q_lower, f"Artifact '{artifact}' found in question {idx}!"
            assert artifact not in ans_lower, f"Artifact '{artifact}' found in ideal answer {idx}!"

        # Check B & C: No template strings or questions based only on topic names
        for template in ["explain the core principles and academic significance of", "what is what is"]:
            assert template not in q_lower, f"Template string '{template}' found in question {idx}!"

        # Check E & F: No unsupported claims
        assert "change over time" not in ans_lower, f"Unsupported 'change over time' claim found in answer {idx}!"
        assert quality.get("grounded") is True, f"Question {idx} failed grounding check!"
        assert quality.get("unsupported_claims") is False, f"Question {idx} flagged for unsupported claims!"

    # Check G: Multiple concepts/sections covered
    print(f"\nSections Covered ({len(covered_sections)} unique sections): {list(covered_sections)}")
    assert len(covered_sections) >= 2, "Questions failed to cover multiple document units/sections!"
    print("[PASS] Check G: Multiple units/sections covered across questions.")

    # Check H: No duplicate questions
    print("\n--- [STAGE 5] Checking Cosine Similarity & Deduplication ---")
    for i in range(len(staged_questions)):
        for j in range(i + 1, len(staged_questions)):
            q1 = staged_questions[i]["question_text"]
            q2 = staged_questions[j]["question_text"]
            v1 = np.array(embedding_service.generate_query_embedding(q1))
            v2 = np.array(embedding_service.generate_query_embedding(q2))
            sim = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
            assert sim < 0.85, f"Near-duplicate question pair detected ({sim:.3f} similarity) between Q{i+1} and Q{j+1}!"
    print("[PASS] Check H: All generated questions are distinct (Cosine similarity < 0.85).")

    # Check I: Document isolation check
    print("\n--- [STAGE 6] Document-Scoped Retrieval Verification ---")
    foreign_check = vector_store.search(
        query_embedding=embedding_service.generate_query_embedding("relational calculus"),
        document_id=doc_id,
        top_k=5
    )
    for res in foreign_check:
        assert res.get("metadata", {}).get("document_id") == doc_id, "Foreign document chunk retrieved!"
    print("[PASS] Check I: Retrieval remains strictly document-scoped.")

    # Check J: API Failure Test
    print("\n--- [STAGE 7] API Failure Behavior Test (Zero Fallback Questions) ---")
    orig_key = llm_service.api_key
    try:
        llm_service.api_key = ""
        fail_res = question_generator_engine.generate_document_grounded_questions(
            document_id=doc_id,
            requested_count=5
        )
        assert fail_res.get("status") == "LLM_GENERATION_FAILED", "Expected LLM_GENERATION_FAILED on API failure!"
        assert fail_res.get("verified_count") == 0, "Expected 0 questions on API failure!"
        print("[PASS] Check J: LLM API error cleanly produces 0 questions (NO silent fallbacks).")
    finally:
        llm_service.api_key = orig_key

    # Check K: Backend to Frontend Data Consistency Verification
    print("\n--- [STAGE 8] Backend vs Faculty Review Queue Consistency ---")
    fetched_record = viva_creation_service.get_viva(viva_id)
    assert fetched_record is not None, "Viva record not found in backend!"
    assert len(fetched_record.generated_questions) == len(staged_questions), "Question count mismatch!"
    for backend_q, staged_q in zip(fetched_record.generated_questions, staged_questions):
        assert backend_q["question_text"] == staged_q["question_text"], "Question text mismatch between backend and staged queue!"
        assert backend_q["ideal_answer"] == staged_q["ideal_answer"], "Ideal answer mismatch between backend and staged queue!"
    print("[PASS] Check K: Backend stored questions match faculty review queue payload 100%.")

    # Cleanup temp viva & vector store entries
    vector_store.delete_document_chunks(doc_id)
    viva_creation_service.delete_viva(viva_id)

    print("\n" + "=" * 95)
    print("ALL 11 END-TO-END APPLICATION FLOW CHECKS PASSED 100% SUCCESSFULLY!")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    run_e2e_real_app_flow()
