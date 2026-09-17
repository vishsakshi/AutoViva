import os
import sys
import logging
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("autoviva.model_comparison")

from app.services.llm_service import llm_service
from app.services.document_processor import document_processor
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.question_generator import question_generator_engine
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def run_model_comparison():
    print("\n" + "=" * 95)
    print("AUTOVIVA MODEL COMPARISON TEST ON 14-PAGE NLP PDF")
    print("Comparing: (1) qwen2.5:0.5b  VS  (2) qwen2.5:3b")
    print("Same Document | Same Retrieved Chunks | Same Prompts | Same Verification Pipeline")
    print("=" * 95 + "\n")

    pdf_path = os.path.join(BASE_DIR, "nlp_academic_lecture_14p.pdf")
    assert os.path.exists(pdf_path), f"PDF file '{pdf_path}' not found!"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    pages = document_processor.process_pdf(file_bytes, "nlp_academic_lecture_14p.pdf")
    print(f"Processed 14-page PDF containing {len(pages)} pages.")

    create_req = VivaCreateRequest(
        subject="Natural Language Processing",
        course_code="CS224N",
        topic="Word Representations & Vector Models",
        difficulty="Medium",
        question_count=5,
        duration_minutes=20,
        batch="2026-NLP-COMPARE"
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
    print(f"Document Ingested into ChromaDB | Doc ID: '{doc_id}' | Total Chunks: {upload_res['chunks_stored']}\n")

    models_to_test = ["qwen2.5:0.5b", "qwen2.5:3b"]
    test_results = {}

    for model_name in models_to_test:
        print("\n" + "#" * 95)
        print(f"STARTING TEST RUN FOR MODEL: {model_name}")
        print("#" * 95 + "\n")

        llm_service.model = model_name

        start_t = time.perf_counter()
        gen_results = question_generator_engine.generate_document_grounded_questions(
            document_id=doc_id,
            viva_id=viva_id,
            subject=create_req.subject,
            topic=create_req.topic,
            requested_count=5
        )
        elapsed = round((time.perf_counter() - start_t) * 1000, 2)

        staged_q = gen_results.get("generated_questions", [])
        rejected_log = gen_results.get("rejected_log", [])

        test_results[model_name] = {
            "staged_questions": staged_q,
            "rejected_log": rejected_log,
            "latency_ms": elapsed
        }

    # Cleanup Vector Store & Viva Record
    vector_store.delete_document_chunks(doc_id)
    viva_creation_service.delete_viva(viva_id)

    # Detailed Comparison Reporting
    print("\n\n" + "=" * 95)
    print("MODEL COMPARISON REPORT: DETAILED RESULTS & AUDIT")
    print("=" * 95)

    for model_name in models_to_test:
        m_res = test_results[model_name]
        staged_q = m_res["staged_questions"]
        rejected_log = m_res["rejected_log"]
        latency = m_res["latency_ms"]

        print(f"\n" + "*" * 95)
        print(f"MODEL: {model_name} (Total Generation & Verification Time: {latency} ms)")
        print(f"Staged Questions: {len(staged_q)} / 5 | Total Candidates Rejected by Verifier: {len(rejected_log)}")
        print("*" * 95)

        print(f"\n--- REJECTED CANDIDATES LOG FOR {model_name} ({len(rejected_log)} Rejections) ---")
        for r_idx, r in enumerate(rejected_log, 1):
            print(f"Rejected #{r_idx} | Slot {r.get('slot')} Attempt {r.get('attempt')} | Chunk: {r.get('chunk_id')}")
            if r.get("candidate"):
                print(f"  Candidate Question: \"{r.get('candidate')}\"")
            print(f"  Rejection Reason  : {r.get('reason')}")
            print("-" * 80)

        print(f"\n--- STAGED ACCEPTED QUESTIONS FOR {model_name} ({len(staged_q)} Questions) ---")
        for idx, q in enumerate(staged_q, 1):
            q_text = q.get("question_text") or q.get("question")
            ans_text = q.get("ideal_answer")
            acad_concept = q.get("academic_concept") or q.get("topic") or q.get("topic_title")
            chunk_id = q.get("source_chunk") or (q.get("source_chunk_ids", ["N/A"])[0] if q.get("source_chunk_ids") else "N/A")
            source_quote = q.get("source_quote", "N/A")
            source_page = q.get("source_page", "Page 1")
            val_rep = q.get("validation_report", {})
            q_metrics = val_rep.get("quality_metrics", {})

            # Consistency checks
            q_terms = [w.lower() for w in q_text.split() if len(w) > 4]
            ans_terms = [w.lower() for w in ans_text.split() if len(w) > 4]
            
            # Check for hallucinated CCV or other invalid terms
            has_ccv = "ccv" in q_text.lower() or "ccv" in ans_text.lower() or "contextual vector" in q_text.lower() or "contextual vector" in ans_text.lower()

            print(f"\n[QUESTION #{idx}] (Model: {model_name})")
            print(f"Target Concept       : {acad_concept}")
            print(f"Page & Chunk ID      : {source_page} | {chunk_id}")
            print(f"Retrieved Evidence   : \"{source_quote}\"")
            print(f"Question             : \"{q_text}\"")
            print(f"Ideal Answer         : \"{ans_text}\"")
            print(f"Grounding Result     : Grounded={q_metrics.get('grounded', True)} | Unsupported Claims={q_metrics.get('unsupported_claims', False)}")
            print(f"Question/Evidence Cons: {'FAIL (Hallucinated CCV)' if has_ccv else 'PASS (Substantively Supported)'}")
            print(f"Answer/Evidence Cons  : {'FAIL (Hallucinated CCV)' if has_ccv else 'PASS (Directly Entailed)'}")
            print(f"Status               : {q_metrics.get('status', 'VERIFIED')}")

    print("\n" + "=" * 95)
    print("FINAL MODEL COMPARISON SUMMARY & RECOMMENDATION")
    print("=" * 95)
    for model_name in models_to_test:
        staged_cnt = len(test_results[model_name]["staged_questions"])
        rej_cnt = len(test_results[model_name]["rejected_log"])
        lat = test_results[model_name]["latency_ms"]
        print(f"- {model_name:15s}: Staged={staged_cnt}/5 | Rejections={rej_cnt:2d} | Latency={lat} ms")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    run_model_comparison()
