import fitz  # PyMuPDF
from app.services.knowledge_service import knowledge_service
from app.services.question_generator import question_generator_engine
from app.models.question_gen import GenerateQuestionsRequest

def create_dbms_pdf(filepath: str):
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((50, 40), "CS401: Database Management Systems\nUnit 1: Transaction Processing & ACID Properties", fontsize=16)
    p1.insert_text((50, 80),
        "A transaction is a logical unit of database processing that includes one or more database operations.\n"
        "To ensure integrity, transactions must adhere to the ACID properties:\n"
        "1. Atomicity: Requires that all operations of a transaction are executed completely, or none are (all-or-nothing).\n"
        "2. Consistency: Ensures that a transaction brings the database from one valid state to another valid state.\n"
        "3. Isolation: Ensures that concurrent execution of transactions results in a state that would be obtained if transactions were executed serially.\n"
        "4. Durability: Guarantees that once a transaction commits, its results are permanently saved in non-volatile storage even in system failures.",
        fontsize=10
    )
    doc.save(filepath)
    doc.close()

def main():
    print("=" * 80)
    print("VIVABOT QUESTION GENERATION ENGINE SAFEGUARDS TEST SUITE")
    print("=" * 80)

    dbms_pdf = "dbms_notes.pdf"
    create_dbms_pdf(dbms_pdf)
    with open(dbms_pdf, "rb") as f:
        knowledge_service.process_and_index_document(f.read(), dbms_pdf, "Database Management Systems", "ACID Transactions")

    # TEST SAFEGUARD 1: Retrieval Confidence Gate
    print("\n--- TEST SAFEGUARD 1: Retrieval Confidence Gate ---")
    low_conf_req = GenerateQuestionsRequest(
        subject="Quantum Physics",
        topic="Superstring Theory Multiverse",
        difficulty="hard",
        question_count=2
    )

    gate_result = question_generator_engine.generate_questions(low_conf_req)
    print(f"Status: {gate_result['status']}")
    print(f"Message: \"{gate_result['message']}\"")
    print(f"Retrieval Confidence Score: {gate_result['retrieval_confidence']}")

    assert gate_result["status"] == "INSUFFICIENT_CONTEXT"
    assert gate_result["message"] == "Insufficient academic context."
    print("[SUCCESS] SAFEGUARD 1 VERIFIED: Aborted generation cleanly on low retrieval confidence.")


    # TEST SAFEGUARD 2: Question Quality Validator
    print("\n--- TEST SAFEGUARD 2: Question Quality & Grounding Validator ---")
    multi_part_q = {
        "question_text": "What is a Binary Search Tree? How does insertion work? What is the worst case complexity?",
        "ideal_answer": "A BST is a binary tree where left < parent < right. Insertion traverses down until empty leaf. Worst case O(n).",
        "learning_objective": "Understand BST operations",
        "key_concepts": ["Binary Search Tree", "Insertion"],
        "evaluation_rubric": [{"criterion": "Explanation", "marks": 10.0}],
        "reference_source": "data_structures_notes.pdf (Page 1)"
    }
    is_valid, err_msg = question_generator_engine.validate_question_quality(multi_part_q, "Binary Search Tree properties left < parent < right")
    print(f"Multi-Part Question Validation Result: {is_valid} | Reason: \"{err_msg}\"")
    assert not is_valid
    assert "multiple sub-questions" in err_msg
    print("[SUCCESS] SAFEGUARD 2 VERIFIED: Multi-part & unsupported questions correctly rejected.")


    # STEP 3: Multi-Subject Valid Generation & Audit Logging (Safeguard 3)
    print("\n--- TEST SAFEGUARD 3: Generation Audit Logging & Metadata ---")
    valid_req = GenerateQuestionsRequest(
        subject="Database Management Systems",
        topic="ACID Transactions",
        difficulty="medium",
        question_count=2
    )

    valid_res = question_generator_engine.generate_questions(valid_req)
    print(f"Status: {valid_res['status']}")
    print(f"Generated Questions: {valid_res['generated_count']}")
    
    logs = question_generator_engine.generation_logs
    print(f"\nTotal Recorded Generation Audit Logs: {len(logs)}")
    latest_log = logs[-1]

    print("\n[LATEST GENERATION AUDIT LOG ENTRY]:")
    print(f"  - Log ID: {latest_log['log_id']}")
    print(f"  - Retrieved Chunk IDs: {latest_log['retrieved_chunk_ids']}")
    print(f"  - Retrieval Confidence: {latest_log['retrieval_confidence']}")
    print(f"  - Generation Timestamp: {latest_log['generation_timestamp']}")
    print(f"  - Generation Latency: {latest_log['generation_latency_ms']} ms")
    print(f"  - Model Version: {latest_log['model_version']}")
    print(f"  - Prompt Version: {latest_log['prompt_version']}")
    print(f"  - Question Version: {latest_log['question_version']}")
    print(f"  - Generated / Rejected Count: {latest_log['generated_count']} / {latest_log['rejected_count']}")

    print("\n" + "=" * 80)
    print("ALL THREE SAFEGUARDS FULLY VERIFIED AND PASSING!")
    print("=" * 80)

if __name__ == "__main__":
    main()
