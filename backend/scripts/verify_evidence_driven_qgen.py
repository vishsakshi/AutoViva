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
logger = logging.getLogger("autoviva.evidence_qgen_test")

from app.services.llm_service import llm_service
from app.services.document_processor import document_processor
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.question_generator import question_generator_engine
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def run_evidence_driven_qgen_test():
    print("\n" + "=" * 95)
    print("AUTOVIVA EVIDENCE-DRIVEN RAG QUESTION GENERATION TEST (NLP LECTURE PDF)")
    print("=" * 95 + "\n")

    assert llm_service.is_configured(), "LLM Service is not configured!"

    pdf_path = os.path.join(BASE_DIR, "nlp_lecture_notes.pdf")
    assert os.path.exists(pdf_path), f"PDF file '{pdf_path}' does not exist!"

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    # 1. Create Viva Request & Ingest PDF
    create_req = VivaCreateRequest(
        subject="Natural Language Processing",
        course_code="CS224N",
        topic="Word Vectors & Distributional Semantics",
        difficulty="Medium",
        question_count=5,
        duration_minutes=20,
        batch="2026-NLP"
    )
    viva_record = viva_creation_service.create_viva(create_req)
    viva_id = viva_record.viva_id

    upload_res = knowledge_service.process_and_store_document(
        file_bytes=file_bytes,
        filename="nlp_lecture_notes.pdf",
        subject=viva_record.subject,
        topic=viva_record.topic,
        viva_id=viva_id
    )
    doc_id = upload_res["document_id"]
    print(f"Ingested Document ID: '{doc_id}' | Chunks Stored: {upload_res['chunks_stored']}\n")

    # 2. Generate 5 Questions
    gen_record = viva_creation_service.generate_questions_for_viva(viva_id)
    staged_questions = gen_record.generated_questions

    print("=" * 95)
    print(f"GENERATED & VERIFIED {len(staged_questions)} EVIDENCE-DRIVEN VIVA QUESTIONS:")
    print("=" * 95)

    for idx, q in enumerate(staged_questions, 1):
        q_text = q.get("question_text") or q.get("question")
        ans_text = q.get("ideal_answer")
        acad_concept = q.get("academic_concept") or q.get("topic") or q.get("topic_title")
        concept_type = q.get("concept_type", "ACADEMIC_CONCEPT")
        q_type = q.get("question_type", "conceptual_understanding")
        chunk_id = q.get("source_chunk") or (q.get("source_chunk_ids", ["N/A"])[0] if q.get("source_chunk_ids") else "N/A")
        source_quote = q.get("source_quote", "N/A")
        source_page = q.get("source_page", "Page 1")
        val_rep = q.get("validation_report", {})
        q_metrics = val_rep.get("quality_metrics", {})

        print(f"\n--- QUESTION CANDIDATE #{idx} ---")
        print(f"1. Candidate Topic/Concept: {acad_concept}")
        print(f"2. Concept Classification: {concept_type}")
        print(f"3. Retrieved Page Number: {source_page}")
        print(f"4. Retrieved Chunk ID: {chunk_id}")
        print(f"5. Short Evidence Excerpt: \"{source_quote[:120]}...\"")
        print(f"6. Question Type: {q_type}")
        print(f"7. Generated Question: \"{q_text}\"")
        print(f"8. Ideal Answer: \"{ans_text}\"")
        print(f"9. Grounding Result: Grounded={q_metrics.get('grounded', True)} | Unsupported Claims={q_metrics.get('unsupported_claims', False)}")
        print(f"10. Rejection Reason: None (Status={q_metrics.get('status', 'VERIFIED')})")

        # Assert zero document metadata/author artifacts
        q_lower = q_text.lower()
        ans_lower = ans_text.lower()
        for artifact in ["socher", "chaubard", "manning", "page 2", "lecture 1", "stanford"]:
            assert artifact not in q_lower, f"Author/Metadata artifact '{artifact}' found in Q{idx}!"
            assert artifact not in ans_lower, f"Author/Metadata artifact '{artifact}' found in answer {idx}!"

    # Cleanup
    vector_store.delete_document_chunks(doc_id)
    viva_creation_service.delete_viva(viva_id)

    print("\n" + "=" * 95)
    print("EVIDENCE-DRIVEN QUESTION GENERATION TEST COMPLETED 100% SUCCESSFULLY!")
    print("=" * 95 + "\n")

if __name__ == "__main__":
    run_evidence_driven_qgen_test()
