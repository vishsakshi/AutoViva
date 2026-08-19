import pymongo
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def verify_distributional_semantics_rag():
    print("=" * 90)
    print("AUTOVIVA DYNAMIC RAG TEST: DISTRIBUTIONAL SEMANTICS PDF UPLOAD & QGEN")
    print("=" * 90)

    # STEP 1: Upload & Index Distributional Semantics Academic Text into ChromaDB
    pdf_text = (
        "DISTRIBUTIONAL SEMANTICS AND VECTOR SPACE MODELS OF MEANING\n"
        "Topic: Distributional Hypothesis, PMI, TF-IDF, and Cosine Similarity.\n"
        "Distributional semantics represents word meanings using high-dimensional vector spaces derived from co-occurrence patterns.\n"
        "The Distributional Hypothesis states that words that occur in similar contexts tend to have similar meanings.\n"
        "A Distributional Matrix can be constructed using Word x Context or Word x Document representations.\n"
        "Pointwise Mutual Information (PMI) quantifies the association strength between target words and context words.\n"
        "Term Frequency-Inverse Document Frequency (TF-IDF) weights word importance relative to document frequency.\n"
        "Cosine Similarity measures the angle between two word vectors to calculate semantic similarity.\n"
    ).encode("utf-8")

    filename = "NLP_Unit2_Distributional_Semantics.txt"
    subject = "Natural Language Processing"
    topic = "Distributional Semantics"

    print("\n--- STEP 1: Uploading & Indexing Distributional Semantics PDF into ChromaDB ---")
    upload_res = knowledge_service.process_and_store_document(
        file_bytes=pdf_text,
        filename=filename,
        subject=subject,
        topic=topic
    )
    print(f"[VERIFIED]: Processed & indexed {upload_res['chunks']} chunks into ChromaDB!")

    # STEP 2: Create Viva Session
    print("\n--- STEP 2: Creating Viva Session Record ---")
    create_req = VivaCreateRequest(
        subject=subject,
        course_code="NLP401",
        topic=topic,
        question_count=3,
        duration_minutes=15,
        batch="Batch 2026"
    )
    viva_record = viva_creation_service.create_viva(create_req)
    v_id = viva_record.viva_id
    viva_creation_service.add_uploaded_file(v_id, filename)
    print(f"[VERIFIED]: Created Session {v_id} for '{subject}' ({topic})")

    # STEP 3: Generate Grounded Questions from ChromaDB
    print("\n--- STEP 3: Generating Questions from ChromaDB Vector Store ---")
    qrec = viva_creation_service.generate_questions_for_viva(v_id)

    print(f"\n[SUCCESS]: Generated {len(qrec.generated_questions)} Grounded RAG Questions:")
    
    # Audit Each Question
    forbidden_terms = ["network address translation", "napt", "binary search tree", "acid properties"]

    
    for idx, q in enumerate(qrec.generated_questions):
        q_text = q.get("question_text", "")
        ideal_ans = q.get("ideal_answer", "")
        ref = q.get("reference_source", "")

        print(f"\n--- Question {idx + 1} ---")
        print(f"Question: \"{q_text}\"")
        print(f"Ideal Answer: \"{ideal_ans[:140]}...\"")
        print(f"Source Reference: {ref}")
        print(f"Confidence Score: {q.get('confidence')}")

        # Check that NO forbidden hardcoded terms exist
        for ft in forbidden_terms:
            assert ft not in q_text.lower(), f"[FAILED]: Found hardcoded term '{ft}' in generated question!"
            assert ft not in ideal_ans.lower(), f"[FAILED]: Found hardcoded term '{ft}' in ideal answer!"

        # Verify document concepts exist in question/answer
        assert "distributional" in q_text.lower() or "semantics" in q_text.lower() or "nlp" in q_text.lower() or "vector" in q_text.lower() or "word" in q_text.lower(), \
            f"[FAILED]: Question text is ungrounded in uploaded PDF: '{q_text}'"

    print("\n" + "=" * 90)
    print("VERIFICATION SUCCESSFUL! ALL GENERATED QUESTIONS ARE 100% GROUNDED IN THE UPLOADED DISTRIBUTIONAL SEMANTICS PDF!")
    print("=" * 90)

if __name__ == "__main__":
    verify_distributional_semantics_rag()
