import pymongo
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def run_end_to_end_viva_qgen_pipeline():
    print("=" * 90)
    print("AUTOVIVA FULL FACULTY VIVA -> RAG QUESTION GENERATION END-TO-END SUITE")
    print("=" * 90)

    # STEP 1: Create Viva Session in MongoDB
    print("\n--- STEP 1: Creating Viva Session Metadata in MongoDB ---")
    create_req = VivaCreateRequest(
        subject="Computer Networks",
        course_code="CS301",
        topic="IP Addressing, NAT & NAPT",
        question_count=3,
        duration_minutes=15,
        batch="Batch 2026"
    )

    viva_record = viva_creation_service.create_viva(create_req)
    v_id = viva_record.viva_id
    print(f"[VERIFIED]: Viva Session Created in MongoDB!")
    print(f"Viva ID: {v_id}")
    print(f"Subject: {viva_record.subject}")
    print(f"Course Code: {viva_record.course_code}")
    print(f"Topic: {viva_record.topic}")

    # Inspect MongoDB document
    client = pymongo.MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    sessions_col = db["viva_sessions"]
    mongo_doc = sessions_col.find_one({"viva_id": v_id})
    assert mongo_doc is not None
    assert mongo_doc["subject"] == "Computer Networks"
    print(f"[VERIFIED]: Record persisted in MongoDB `db.viva_sessions` collection!")

    # STEP 2: Upload Syllabus & Index into ChromaDB
    print("\n--- STEP 2: Uploading & Indexing Syllabus Material into ChromaDB ---")
    syllabus_text = (
        "COMPUTER NETWORKS UNIT 3: NETWORK ADDRESS TRANSLATION (NAT)\n"
        "Topic 3.1: Network Address Translation and Socket Multiplexing.\n"
        "Network Address Translation (NAT) allows private internal IP networks to share a public external IP address.\n"
        "NAPT (Port Address Translation) maps private IP sockets to unique external source port numbers.\n"
        "This allows thousands of internal hosts to simultaneously communicate over a single public IP address.\n"
        "Security benefits include hiding internal network topology from external internet scanners.\n"
    ).encode("utf-8")

    filename = "Computer_Networks_Unit3_NAT.txt"
    upload_res = knowledge_service.process_and_store_document(
        file_bytes=syllabus_text,
        filename=filename,
        subject=viva_record.subject,
        topic=viva_record.topic,
        viva_id=v_id
    )

    viva_creation_service.add_uploaded_file(v_id, filename)
    print(f"[VERIFIED]: Indexed {upload_res['chunks']} chunks into ChromaDB Knowledge Base!")

    # STEP 3: Generate Grounded Questions
    print("\n--- STEP 3: RAG Grounded Question Generation from ChromaDB Context ---")
    updated_record = viva_creation_service.generate_questions_for_viva(v_id)

    print(f"[SUCCESS]: Generated {len(updated_record.generated_questions)} Grounded Questions!")
    assert len(updated_record.generated_questions) == 3

    print("\nGenerated Questions with Evidence:")
    for idx, q in enumerate(updated_record.generated_questions):
        print(f"\n--- Question {idx + 1} ({q.get('question_id')}) ---")
        print(f"Question: \"{q.get('question_text')}\"")
        print(f"Ideal Answer: \"{q.get('ideal_answer')[:120]}...\"")
        print(f"Difficulty: {q.get('difficulty')} | Bloom: {q.get('blooms_level')}")
        print(f"Marks: {q.get('total_marks', 10.0)} | Rubric Criteria: {len(q.get('evaluation_rubric', []))}")
        print(f"Evidence Source: {q.get('reference_source')}")

        # Assert mandatory evidence keys exist
        assert q.get("question_text") is not None
        assert q.get("ideal_answer") is not None
        assert q.get("evaluation_rubric") is not None

    # STEP 4: Review Queue (Approve & Publish)
    print("\n--- STEP 4: Faculty Question Review & Publishing ---")
    first_q_id = updated_record.generated_questions[0]["question_id"]
    approved_rec = viva_creation_service.review_viva_question(v_id, first_q_id, "APPROVE")
    assert len(approved_rec.approved_questions) == 1
    print(f"[VERIFIED]: Question {first_q_id} approved!")

    published_rec = viva_creation_service.publish_viva(v_id)
    assert published_rec.status == "PUBLISHED"
    print(f"[VERIFIED]: Viva Session {v_id} status set to PUBLISHED!")

    print("\n" + "=" * 90)
    print("FACULTY VIVA -> RAG QUESTION GENERATION PIPELINE PASSED 100% SUCCESS!")

    print("=" * 90)

if __name__ == "__main__":
    run_end_to_end_viva_qgen_pipeline()
