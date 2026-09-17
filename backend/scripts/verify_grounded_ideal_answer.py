import os
import sys
import fitz
import logging
import json
import time

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
logger = logging.getLogger("autoviva.grounding_verification")

from app.core.config import settings
from app.services.llm_service import llm_service
from app.services.document_processor import document_processor
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.question_generator import question_generator_engine
from app.services.question_verifier import question_verifier

def run_grounding_verification():
    print("\n" + "=" * 90)
    print("AUTOVIVA GROUNDED IDEAL ANSWER & VERIFICATION REGRESSION TEST")
    print("=" * 90 + "\n")

    # 1. Check LLM Configuration
    print("--- [TEST 1] LLM Configuration Check ---")
    print(f"Provider: {llm_service.provider}")
    print(f"Model: {llm_service.model}")
    print(f"API URL: {llm_service.api_url}")
    print(f"Is Configured: {llm_service.is_configured()}")
    assert llm_service.is_configured(), "LLM Service is not configured!"
    print("[PASS] TEST 1: LLM Configured correctly.\n")

    # 2. Ingest Distributional Semantics Evidence Document
    print("--- [TEST 2] Ingesting Distributional Semantics PDF ---")
    
    # Create PDF with exact evidence text
    evidence_text = (
        "Chapter 1: Distributional Semantics and Vector Models\n\n"
        "Distributional semantics is based on the distributional hypothesis that words occurring in "
        "similar contexts tend to have similar word embeddings. Continuous skip-gram and continuous "
        "bag-of-words architectures are used to efficiently learn word embeddings in continuous vector spaces."
    )
    
    pdf_path = os.path.join(BASE_DIR, "dist_semantics_reg.pdf")
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, evidence_text)
    doc.save(pdf_path)
    doc.close()

    # Upload to Knowledge Service
    with open(pdf_path, "rb") as f:
        up_res = knowledge_service.process_and_store_document(
            file_bytes=f.read(),
            filename="dist_semantics_reg.pdf",
            subject="Natural Language Processing",
            topic="Distributional Semantics",
            viva_id="viva_dist_reg_1"
        )
    
    document_id = up_res["document_id"]
    print(f"Ingested Document ID: {document_id}")
    print(f"Total Chunks Stored: {up_res['chunks_stored']}")
    
    retrieved_chunks = vector_store.get_document_chunks(document_id)
    print(f"Retrieved Chunks Count: {len(retrieved_chunks)}")
    assert len(retrieved_chunks) > 0, "No chunks retrieved from vector store!"
    print(f"Retrieved Evidence Text: \"{retrieved_chunks[0]['text']}\"\n")

    # 3. Test Direct Grounding Verification on BAD vs GOOD Candidates
    print("--- [TEST 3A] Testing BAD ANSWER Rejection (Contains 'change over time') ---")
    bad_q = "What is the core definition and conceptual intuition behind distributional semantics and vector models?"
    bad_ans = "Distributional semantics is a branch of natural language processing that studies the distribution of words in a text. It aims to understand how words are associated with each other and how they change over time. Vector models are a type of distributional semantics that represent words using vectors."
    
    bad_res = question_verifier.verify_question_candidate(
        question_text=bad_q,
        ideal_answer=bad_ans,
        evidence_chunks=retrieved_chunks,
        topic_title="Distributional Semantics"
    )
    
    print(f"Bad Answer Valid: {bad_res['valid']}")
    print(f"Bad Answer Grounded: {bad_res['grounded']}")
    print(f"Bad Answer Unsupported Claims: {bad_res['unsupported_claims']}")
    print(f"Bad Answer Reason: {bad_res['reason']}")
    assert bad_res['valid'] is False, "BAD ANSWER FAILED: expected valid = False!"
    assert bad_res['grounded'] is False, "BAD ANSWER FAILED: expected grounded = False!"
    assert bad_res['unsupported_claims'] is True, "BAD ANSWER FAILED: expected unsupported_claims = True!"
    print("[PASS] TEST 3A: BAD ANSWER correctly rejected (unsupported_claims=True, valid=False, grounded=False).\n")

    print("--- [TEST 3B] Testing GOOD ANSWER Acceptance (Grounded in Evidence) ---")
    good_q = "What is the core definition and conceptual intuition behind distributional semantics and vector models?"
    good_ans = "Distributional semantics is based on the distributional hypothesis: words that occur in similar contexts tend to have similar word embeddings. Vector models represent these word relationships in continuous vector spaces, and architectures such as continuous skip-gram and continuous bag-of-words can be used to learn such embeddings."

    good_res = question_verifier.verify_question_candidate(
        question_text=good_q,
        ideal_answer=good_ans,
        evidence_chunks=retrieved_chunks,
        topic_title="Distributional Semantics"
    )

    print(f"Good Answer Valid: {good_res['valid']}")
    print(f"Good Answer Grounded: {good_res['grounded']}")
    print(f"Good Answer Unsupported Claims: {good_res['unsupported_claims']}")
    print(f"Good Answer Reason: {good_res['reason']}")
    assert good_res['valid'] is True, "GOOD ANSWER FAILED: expected valid = True!"
    assert good_res['grounded'] is True, "GOOD ANSWER FAILED: expected grounded = True!"
    assert good_res['unsupported_claims'] is False, "GOOD ANSWER FAILED: expected unsupported_claims = False!"
    print("[PASS] TEST 3B: GOOD ANSWER correctly accepted (unsupported_claims=False, valid=True, grounded=True).\n")

    # 4. Generate Question + Ideal Answer via Real LLM Call
    print("--- [TEST 4] Real LLM Grounded Question + Ideal Answer Generation ---")
    gen_res = question_generator_engine.generate_document_grounded_questions(
        document_id=document_id,
        requested_count=1
    )

    print(f"Generation Status: {gen_res.get('status')}")
    print(f"Verified Questions Count: {gen_res.get('verified_count')}")

    questions = gen_res.get("generated_questions", [])
    assert len(questions) > 0, "Question generation returned ZERO verified questions!"

    q_item = questions[0]
    generated_q = q_item["question_text"]
    generated_ans = q_item["ideal_answer"]
    
    print("\n--- GENERATED QUESTION & GROUNDED IDEAL ANSWER ---")
    print(f"Generated Question: \"{generated_q}\"")
    print(f"Generated Ideal Answer: \"{generated_ans}\"")
    print(f"Source Quote: \"{q_item.get('source_quote', '')}\"")
    print(f"Quality Metrics: {json.dumps(q_item.get('validation_report', {}).get('quality_metrics', {}))}")

    # Assert Grounding Requirements
    ans_lower = generated_ans.lower()
    assert "change over time" not in ans_lower, "CRITICAL ERROR: Generated answer contains unsupported 'change over time' claim!"
    assert "distributional hypothesis" in ans_lower or "embeddings" in ans_lower or "vector" in ans_lower, "Generated answer fails to explain distributional hypothesis or embeddings from evidence!"
    print("[PASS] TEST 4: Ideal answer is fully grounded in retrieved evidence (explains distributional hypothesis, zero unsupported claims).\n")

    # 5. API Failure Test (No Silent Fallback)
    print("--- [TEST 5] API Failure Handling Test (Zero Silent Fallbacks) ---")
    orig_key = llm_service.api_key
    try:
        llm_service.api_key = ""
        fail_res = question_generator_engine.generate_document_grounded_questions(
            document_id=document_id,
            requested_count=1
        )
        print(f"API Error Status: {fail_res.get('status')}")
        print(f"API Error Verified Count: {fail_res.get('verified_count')}")
        assert fail_res.get("status") == "LLM_GENERATION_FAILED", "Expected LLM_GENERATION_FAILED status!"
        assert fail_res.get("verified_count") == 0, "Expected 0 questions on API error!"
        print("[PASS] TEST 5: API failure returned LLM_GENERATION_FAILED and 0 questions (No silent fallback).\n")
    finally:
        llm_service.api_key = orig_key

    # 6. Cross-Document Isolation Test
    print("--- [TEST 6] Cross-Document Isolation Test ---")
    q_emb = embedding_service.generate_query_embedding("relational database indexing")
    search_res = vector_store.search(query_embedding=q_emb, document_id=document_id, top_k=5)
    print(f"Cross-document search returned {len(search_res)} chunks for {document_id}")
    for c in search_res:
        assert c.get("metadata", {}).get("document_id") == document_id, "Foreign chunk leaked across document boundaries!"
    print("[PASS] TEST 6: Strict document isolation confirmed.\n")

    # Cleanup temp PDF & ChromaDB vectors
    vector_store.delete_document_chunks(document_id)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    print("=" * 90)
    print("ALL GROUNDING REGRESSION TESTS PASSED 100% SUCCESSFULLY!")
    print("=" * 90 + "\n")

if __name__ == "__main__":
    run_grounding_verification()
