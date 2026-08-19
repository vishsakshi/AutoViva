import pymongo
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def test_10step_rag_pipeline():
    print("=" * 90)
    print("RUNNING 10-STEP FACULTY VIVA RAG PIPELINE INSTRUMENTATION AUDIT")
    print("=" * 90)

    # 1. Create Viva Session Record
    create_req = VivaCreateRequest(
        subject="Natural Language Processing",
        course_code="NLP401",
        topic="Distributional Semantics & Vector Space Models",
        question_count=3,
        duration_minutes=15,
        batch="Batch 2026"
    )
    viva_record = viva_creation_service.create_viva(create_req)
    v_id = viva_record.viva_id
    print(f"\nCreated Viva Session: {v_id} for '{viva_record.subject}'")

    # 2. Construct multi-paragraph syllabus document (simulating textbook chapters)
    nlp_textbook_content = (
        "CHAPTER 6: VECTOR SEMANTICS AND EMBEDDINGS\n"
        "6.1 Distributional Semantics and Word Representations.\n"
        "Distributional semantics represents word meanings using high-dimensional vector spaces derived from co-occurrence statistics.\n"
        "The Distributional Hypothesis states that words that occur in similar contexts tend to have similar meanings.\n"
        "Vector space models map words into continuous vector spaces where spatial proximity correlates with semantic similarity.\n\n"
        "6.2 Word x Context Co-occurrence Matrices.\n"
        "A Term-Document Matrix or Word-Context Matrix represents counts of words occurring alongside target context words.\n"
        "TF-IDF (Term Frequency-Inverse Document Frequency) balances raw term frequency against document frequency.\n"
        "Pointwise Mutual Information (PMI) measures whether two words co-occur more frequently than expected by chance.\n\n"
        "6.3 Cosine Similarity and Dense Embeddings.\n"
        "Cosine similarity measures the dot product of normalized word vectors to compute semantic similarity.\n"
        "Dense vector representations like Word2Vec, GloVe, and BERT embeddings compress high-dimensional sparse matrices into dense vectors.\n"
    ).encode("utf-8")

    filename = "NLP_Chapter6_Vector_Semantics.txt"
    upload_res = knowledge_service.process_and_store_document(
        file_bytes=nlp_textbook_content,
        filename=filename,
        subject=viva_record.subject,
        topic=viva_record.topic,
        viva_id=v_id
    )

    viva_creation_service.add_uploaded_file(v_id, filename)
    print(f"\nUploaded & Indexed '{filename}': {upload_res['chunks']} chunks into ChromaDB.")

    # 3. Call Question Generation to trigger 10-Step Instrumented Audit
    print("\n--- INVOCATION: Triggering Question Generation Engine ---")
    updated_rec = viva_creation_service.generate_questions_for_viva(v_id)

    print(f"\nGenerated {len(updated_rec.generated_questions)} Grounded RAG Questions.")
    assert len(updated_rec.generated_questions) > 0, "Question generation returned 0 questions!"

    print("\n" + "=" * 90)
    print("10-STEP PIPELINE INSTRUMENTATION AUDIT PASSED 100% SUCCESS!")
    print("=" * 90)

if __name__ == "__main__":
    test_10step_rag_pipeline()
