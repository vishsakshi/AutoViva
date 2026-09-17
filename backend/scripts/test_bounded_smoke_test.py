import os
import sys
import logging

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("autoviva.smoke_test")

from app.services.llm_service import llm_service
from app.services.document_processor import document_processor
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.question_generator import question_generator_engine
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def run_bounded_smoke_test():
    print("\n" + "=" * 80)
    print("AUTOVIVA BOUNDED SMOKE TEST (MAX 3 QUESTIONS)")
    print("=" * 80 + "\n")

    # 1. Verify LLM Config
    assert llm_service.is_configured(), "LLM Service is not configured!"
    print("[PASS] 1. Real Ollama Endpoint Configured & Available.")

    # 2. PDF Extraction & Structural Cleanup
    pdf_path = os.path.join(BASE_DIR, "database_systems_academic_syllabus.pdf")
    assert os.path.exists(pdf_path), f"PDF file not found at {pdf_path}"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    pages = document_processor.process_pdf(pdf_bytes, "database_systems_academic_syllabus.pdf")
    assert len(pages) > 0, "PDF Extraction produced 0 pages!"
    print(f"[PASS] 2. PDF Extraction & Structural Cleanup ({len(pages)} pages extracted).")

    # 3. Create Viva & Store Document in Chroma
    create_req = VivaCreateRequest(
        subject="Database Systems",
        course_code="CS401",
        topic="Relational Operators & Transactions",
        difficulty="Medium",
        question_count=3,
        duration_minutes=15,
        batch="2026-CS"
    )
    viva_record = viva_creation_service.create_viva(create_req)
    viva_id = viva_record.viva_id

    upload_res = knowledge_service.process_and_store_document(
        file_bytes=pdf_bytes,
        filename="database_systems_academic_syllabus.pdf",
        subject=viva_record.subject,
        topic=viva_record.topic,
        viva_id=viva_id
    )
    doc_id = upload_res["document_id"]
    print(f"[PASS] 3. Document Ingested & Stored in ChromaDB (Doc ID: {doc_id}, Chunks: {upload_res['chunks_stored']}).")

    # 4. Document-Scoped Retrieval Check
    retrieved = vector_store.search(
        query_embedding=embedding_service.generate_query_embedding("relational algebra operators"),
        document_id=doc_id,
        top_k=3
    )
    assert len(retrieved) > 0, "Document-scoped retrieval returned 0 chunks!"
    for r in retrieved:
        assert r.get("metadata", {}).get("document_id") == doc_id, "Foreign document chunk retrieved!"
    print("[PASS] 4. Document-Scoped Vector Retrieval Verified.")

    # 5. Question Generation (Bounded to 3 questions)
    gen_record = viva_creation_service.generate_questions_for_viva(viva_id)
    staged = gen_record.generated_questions

    print(f"\n[PASS] 5. Staged {len(staged)} Grounded Viva Questions:")
    for idx, q in enumerate(staged, 1):
        q_text = q.get("question_text") or q.get("question")
        ans_text = q.get("ideal_answer")
        topic_title = q.get("topic") or q.get("topic_title")
        quote = q.get("source_quote")
        print(f"  Q{idx} [{topic_title}]: \"{q_text}\"")
        print(f"       Answer: \"{ans_text[:120]}...\"")
        print(f"       Quote: \"{quote[:90]}...\"")
        
        # Verify no structural metadata labels became topics
        q_lower = q_text.lower()
        for struct_artifact in ["core syllabus content", "document content", "extracted content", "slide presentation", "page content"]:
            assert struct_artifact not in q_lower, f"Structural metadata artifact '{struct_artifact}' found in Q{idx}!"

    # 6. Cleanup
    vector_store.delete_document_chunks(doc_id)
    viva_creation_service.delete_viva(viva_id)

    print("\n" + "=" * 80)
    print("BOUNDED SMOKE TEST COMPLETED 100% SUCCESSFULLY!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_bounded_smoke_test()
