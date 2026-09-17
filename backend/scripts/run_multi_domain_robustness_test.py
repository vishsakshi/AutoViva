import os
import sys
import logging
import time
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("autoviva.multi_domain_robustness")

from app.core.config import settings
from app.services.llm_service import llm_service
from app.services.document_processor import document_processor
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.question_generator import question_generator_engine
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def run_multi_domain_test():
    print("\n" + "=" * 95)
    print("AUTOVIVA GENERIC MULTI-DOMAIN RAG QUESTION GENERATION ROBUSTNESS AUDIT")
    print(f"Default Local Ollama Model: '{settings.LLM_MODEL}' (llm_service: '{llm_service.model}')")
    print("=" * 95 + "\n")

    test_docs = [
        {
            "domain": "Natural Language Processing (NLP)",
            "filename": "nlp_academic_lecture_14p.pdf",
            "subject": "Natural Language Processing",
            "topic": "Word Representations & Vector Models"
        },
        {
            "domain": "Database Management Systems (DBMS)",
            "filename": "database_systems_academic_syllabus.pdf",
            "subject": "Database Management Systems",
            "topic": "Relational Model & Normalization"
        },
        {
            "domain": "Operating Systems (OS)",
            "filename": "operating_systems_lecture.txt",
            "subject": "Operating Systems",
            "topic": "Process Synchronization & Memory Management"
        }
    ]

    domain_audit_report = []

    for doc_item in test_docs:
        domain = doc_item["domain"]
        filename = doc_item["filename"]
        subject = doc_item["subject"]
        topic = doc_item["topic"]

        print("\n" + "#" * 95)
        print(f"TESTING DOMAIN: {domain}")
        print(f"Document File : {filename} | Subject: '{subject}' | Topic: '{topic}'")
        print("#" * 95 + "\n")

        file_path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(file_path):
            print(f"[ERROR] File '{file_path}' not found! Skipping.")
            continue

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        start_time = time.perf_counter()

        # 1. Document Extraction Quality & Scanned Detection
        pages_data = document_processor.extract_document(file_bytes, filename)
        ext_len = sum(len(p.get("text", "")) for p in pages_data)
        print(f"[STEP 1 EXTRACTION QUALITY]: Extracted {len(pages_data)} pages/sections ({ext_len} total characters).")
        assert ext_len >= 100, f"Extraction quality check failed for {filename}!"

        # 2. Ingest Document into ChromaDB
        create_req = VivaCreateRequest(
            subject=subject,
            course_code=domain[:6].upper(),
            topic=topic,
            difficulty="Medium",
            question_count=5,
            duration_minutes=20,
            batch=f"2026-ROBUST-{domain[:3]}"
        )
        viva_record = viva_creation_service.create_viva(create_req)
        viva_id = viva_record.viva_id

        upload_res = knowledge_service.process_and_store_document(
            file_bytes=file_bytes,
            filename=filename,
            subject=subject,
            topic=topic,
            viva_id=viva_id
        )
        doc_id = upload_res["document_id"]
        chunks_count = upload_res["chunks_stored"]
        print(f"[STEP 2 CHUNKING & INDEXING]: Ingested into ChromaDB | Doc ID: '{doc_id}' | Total Chunks: {chunks_count}")

        # 3. Document-Scoped Question Generation & Verification Gate
        gen_results = question_generator_engine.generate_document_grounded_questions(
            document_id=doc_id,
            viva_id=viva_id,
            subject=subject,
            topic=topic,
            requested_count=5
        )
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        staged_questions = gen_results.get("generated_questions", [])
        rejected_log = gen_results.get("rejected_log", [])
        telemetry = gen_results.get("llm_telemetry", {})

        total_llm_calls = telemetry.get("total_calls", 0)
        avg_call_ms = telemetry.get("avg_latency_ms", 0.0)
        avg_q_sec = round((elapsed_ms / 1000) / max(1, len(staged_questions)), 2)

        # Audit domain results
        doc_audit = {
            "domain": domain,
            "filename": filename,
            "doc_id": doc_id,
            "extraction_pages": len(pages_data),
            "extraction_characters": ext_len,
            "chunks_count": chunks_count,
            "staged_count": len(staged_questions),
            "rejected_count": len(rejected_log),
            "llm_calls": total_llm_calls,
            "avg_call_ms": avg_call_ms,
            "avg_q_sec": avg_q_sec,
            "latency_ms": elapsed_ms,
            "latency_sec": round(elapsed_ms / 1000, 1),
            "staged_questions": staged_questions,
            "rejected_log": rejected_log
        }
        domain_audit_report.append(doc_audit)

        # Display Staged Questions for Domain
        print(f"\n" + "=" * 95)
        print(f"STAGED GROUNDED VIVA QUESTIONS FOR {domain} ({len(staged_questions)} / 5 Questions):")
        print("=" * 95)
        for idx, q in enumerate(staged_questions, 1):
            q_text = q.get("question_text") or q.get("question")
            ans_text = q.get("ideal_answer")
            q_topic = q.get("topic")
            source_page = q.get("source_page")
            source_quote = q.get("source_quote", "N/A")
            val_rep = q.get("validation_report", {})
            q_metrics = val_rep.get("quality_metrics", {})

            print(f"\n==================== QUESTION #{idx} [{domain}] ====================")
            print(f"Target Concept     : {q_topic}")
            print(f"Page / Source      : {source_page}")
            print(f"Retrieved Evidence : \"{source_quote}\"")
            print(f"Generated Question : \"{q_text}\"")
            print(f"Generated Ideal Ans: \"{ans_text}\"")
            print(f"Grounding Result   : Grounded={q_metrics.get('grounded', True)} | Unsupported Claims={q_metrics.get('unsupported_claims', False)}")
            print(f"Status             : {q_metrics.get('status', 'VERIFIED')}")

        print(f"\n--- REJECTED CANDIDATES LOG FOR {domain} ({len(rejected_log)} Rejections) ---")
        for r_idx, r in enumerate(rejected_log, 1):
            print(f"Rejected #{r_idx} | Slot {r.get('slot')} Attempt {r.get('attempt')} | Chunk {r.get('chunk_id')}")
            if r.get('candidate'):
                print(f"  Candidate Question: \"{r.get('candidate')}\"")
            print(f"  Rejection Reason  : {r.get('reason')}")
            print("-" * 80)

        # Cleanup ChromaDB vectors & viva records
        vector_store.delete_document_chunks(doc_id)
        viva_creation_service.delete_viva(viva_id)

    # Multi-Domain Final Summary
    print("\n\n" + "=" * 95)
    print("AUTOVIVA MULTI-DOMAIN PERFORMANCE AUDIT SUMMARY (BEFORE vs AFTER OPTIMIZATION)")
    print("=" * 95)
    print(f"{'Domain':38s} | {'Staged':7s} | {'Rejections':10s} | {'LLM Calls':9s} | {'Total Time':10s} | {'Avg/Question':12s}")
    print("-" * 95)
    for r in domain_audit_report:
        print(f"{r['domain']:38s} | {r['staged_count']:2d}/5    | {r['rejected_count']:10d} | {r['llm_calls']:9d} | {r['latency_sec']:6.1f} s   | {r['avg_q_sec']:6.1f} s/q")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    run_multi_domain_test()

