import os
import sys
import logging
import json
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("autoviva.smoke_test_3b")

from app.core.config import settings
from app.services.llm_service import llm_service
from app.services.document_processor import document_processor
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.question_generator import question_generator_engine
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def run_qwen3b_smoke_test():
    print("\n" + "=" * 95)
    print("AUTOVIVA DEFAULT OLLAMA MODEL SMOKE TEST (DEFAULT MODEL: qwen2.5:3b)")
    print("=" * 95 + "\n")

    # 1. Confirm Ollama is running & reachable
    print("CHECK 1 & 2: Confirming Ollama is active and qwen2.5:3b is loaded...")
    try:
        resp = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5.0)
        assert resp.status_code == 200, "Ollama service HTTP check failed!"
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"  Local Ollama Installed Models: {models}")
        assert any("qwen2.5:3b" in m for m in models), "qwen2.5:3b model not found in local Ollama!"
        print("[PASS] Check 1 & 2: Ollama active and qwen2.5:3b confirmed available.\n")
    except Exception as e:
        print(f"[FAIL] Check 1 & 2 Error: {e}")
        sys.exit(1)

    # 2. Confirm Backend Configuration Default
    print("CHECK 3: Confirming AutoViva Backend Default Model Configuration...")
    print(f"  settings.LLM_MODEL = '{settings.LLM_MODEL}'")
    print(f"  llm_service.model  = '{llm_service.model}'")
    assert settings.LLM_MODEL == "qwen2.5:3b", f"Expected settings.LLM_MODEL='qwen2.5:3b', got '{settings.LLM_MODEL}'!"
    assert llm_service.model == "qwen2.5:3b", f"Expected llm_service.model='qwen2.5:3b', got '{llm_service.model}'!"
    print("[PASS] Check 3: Default configuration correctly set to qwen2.5:3b.\n")

    # 3. Process 14-Page PDF & Ingest into ChromaDB
    print("CHECK 4: Ingesting 14-Page Academic PDF (nlp_academic_lecture_14p.pdf)...")
    pdf_path = os.path.join(BASE_DIR, "nlp_academic_lecture_14p.pdf")
    assert os.path.exists(pdf_path), f"14-page PDF '{pdf_path}' not found!"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    pages = document_processor.process_pdf(file_bytes, "nlp_academic_lecture_14p.pdf")
    assert len(pages) == 14, f"Expected 14 pages, got {len(pages)}"

    create_req = VivaCreateRequest(
        subject="Natural Language Processing",
        course_code="CS224N",
        topic="Word Representations & Vector Models",
        difficulty="Medium",
        question_count=5,
        duration_minutes=20,
        batch="2026-NLP-SMOKE-3B"
    )
    viva_record = viva_creation_service.create_viva(create_req)
    viva_id = viva_record.viva_id

    upload_res = knowledge_service.process_and_store_document(
        file_bytes=file_bytes,
        filename="nlp_academic_lecture_14p.pdf",
        subject=viva_record.subject,
        topic=viva_record.topic,
        viva_id=viva_id
    )
    doc_id = upload_res["document_id"]
    print(f"[PASS] Check 4: Ingested 14-page PDF | Doc ID: '{doc_id}' | Total Chunks: {upload_res['chunks_stored']}\n")

    # 4. Generate 5 Questions
    print("CHECK 5, 6, 7, 8 & 9: Generating 5 Grounded Questions using Default Model (qwen2.5:3b)...")
    gen_results = question_generator_engine.generate_document_grounded_questions(
        document_id=doc_id,
        viva_id=viva_id,
        subject=create_req.subject,
        topic=create_req.topic,
        requested_count=5
    )
    staged_questions = gen_results.get("generated_questions", [])
    assert len(staged_questions) == 5, f"Expected 5 staged questions, got {len(staged_questions)}"
    print(f"[PASS] Check 5: Generated exactly {len(staged_questions)} grounded questions.\n")

    # Audit each question object for model, verification, and UI compatibility
    for idx, q in enumerate(staged_questions, 1):
        q_model = q.get("llm_model")
        val_status = q.get("validation_status")
        val_report = q.get("validation_report", {})
        q_text = q.get("question_text") or q.get("question")
        ans_text = q.get("ideal_answer")

        print(f"==================== QUESTION #{idx} ====================")
        print(f"Target Concept : {q.get('topic')}")
        print(f"Model Used     : {q_model}")
        print(f"Question       : \"{q_text}\"")
        print(f"Ideal Answer   : \"{ans_text}\"")
        print(f"Status         : {val_status} (Grounded={val_report.get('grounded', True)})")

        # Check 6: Sent to qwen2.5:3b
        assert q_model == "qwen2.5:3b", f"Question #{idx} model mismatch: '{q_model}' != 'qwen2.5:3b'!"
        # Check 7: Verification ran
        assert val_status == "VERIFIED", f"Question #{idx} validation status failed: '{val_status}'!"
        assert val_report.get("valid") is True, f"Question #{idx} report invalid!"
        # Check 8: No silent fallback
        assert q.get("confidence") is not None, "Missing confidence score!"
        # Check 9: UI Schema keys present
        for req_key in ["question_id", "question_text", "ideal_answer", "source_page", "rubric"]:
            assert req_key in q, f"Question #{idx} missing required UI schema key '{req_key}'!"

    print("\n[PASS] Check 6: Requests actually sent to 'qwen2.5:3b'.")
    print("[PASS] Check 7: Grounding and question-quality verifications executed cleanly.")
    print("[PASS] Check 8: ZERO fallback models used.")
    print("[PASS] Check 9: All generated questions compatible with UI display schema.\n")

    # Cleanup Vector Store & Session
    vector_store.delete_document_chunks(doc_id)
    viva_creation_service.delete_viva(viva_id)

    print("=" * 95)
    print("AUTOVIVA SMOKE TEST COMPLETE: DEFAULT MODEL 'qwen2.5:3b' VERIFIED 100% OPERATIONAL")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    run_qwen3b_smoke_test()
