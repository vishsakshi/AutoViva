import os
import sys

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.document_processor import document_processor
from app.services.chunker import document_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.topic_mapper import topic_mapper
from app.services.llm_service import llm_service
from app.services.question_generator import question_generator_engine

def trace_pdf_processing(file_bytes: bytes, filename: str, doc_id: str):
    print("=" * 90)
    print(f"AUTO VIVA END-TO-END DATA FLOW TRACE FOR: '{filename}' (ID: '{doc_id}')")
    print("=" * 90)

    # STEP 1: RAW & CLEANED EXTRACTED TEXT
    print("\n[STEP 1: DOCUMENT EXTRACTION & CLEANING]")
    pages_data = document_processor.extract_document(file_bytes, filename)
    print(f"Extracted {len(pages_data)} pages from '{filename}'.")
    for p in pages_data[:3]:
        print(f"\n--- PAGE {p['page_number']} ---")
        print(f"Section Title: {p.get('section_title')}")
        print(f"Cleaned Text Preview:\n{p['text'][:250]}...")

    # STEP 2: CHUNKING & METADATA
    print("\n[STEP 2: SEMANTIC CHUNKING]")
    chunks = document_chunker.chunk_document(pages_data, subject="Natural Language Processing", topic="Distributional Semantics", document_id=doc_id)
    print(f"Generated {len(chunks)} chunks.")
    for idx, c in enumerate(chunks[:4]):
        meta = c.get("metadata", {})
        print(f"  Chunk {idx+1} [ID: {c.get('chunk_id')} | Page {meta.get('page_number')} | Sec: '{meta.get('section_title')}']: \"{c.get('text')[:100]}...\"")

    # STEP 3: CHROMADB INDEXING & DOCUMENT ISOLATION
    print("\n[STEP 3: CHROMADB INDEXING & ISOLATION CHECK]")
    embeddings = embedding_service.generate_embeddings([c["text"] for c in chunks])
    vector_store.add_chunks(chunks, embeddings)

    # Query ChromaDB specifically for doc_id
    stored_items = vector_store.get_document_chunks(doc_id)
    print(f"ChromaDB retrieval for document_id='{doc_id}' returned {len(stored_items)} chunks.")
    for idx, sc in enumerate(stored_items[:3]):
        meta = sc.get("metadata", {})
        print(f"  Retrieved Chunk {idx+1} [DocID: '{meta.get('document_id')}']: \"{sc.get('text')[:100]}...\"")

    # STEP 4: TOPIC MAPPER & COVERAGE PLAN
    print("\n[STEP 4: TOPIC MAPPING & COVERAGE PLAN]")
    topic_map = topic_mapper.build_topic_map(chunks)
    print(f"Identified {len(topic_map['topics'])} Valid Academic Topics:")
    for idx, t in enumerate(topic_map["topics"]):
        print(f"  Topic {idx+1}: '{t['title']}' (Section: {t.get('section')}, Weight: {t.get('weight')})")

    # STEP 5: LLM CONFIG & CALL ATTEMPT
    print("\n[STEP 5: LLM GATEWAY CONFIG & INVOCATION]")
    redacted_key = f"{settings.LLM_API_KEY[:6]}...{settings.LLM_API_KEY[-4:]}" if len(settings.LLM_API_KEY) > 10 else "***"
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"LLM Model: {settings.LLM_MODEL}")
    print(f"LLM API URL: {settings.LLM_API_URL}")
    print(f"LLM Key Redacted: {redacted_key}")
    print(f"Is Configured: {llm_service.is_configured()}")

    # STEP 6: END-TO-END QUESTION GENERATION & VALIDATION
    print("\n[STEP 6: QUESTION GENERATION & VALIDATION GATE]")
    res = question_generator_engine.generate_document_grounded_questions(
        document_id=doc_id,
        subject="Natural Language Processing",
        topic="Distributional Semantics",
        requested_count=3
    )

    questions = res.get("generated_questions", [])
    print(f"Generated & Staged {len(questions)} Questions:")
    for idx, q in enumerate(questions):
        print(f"\n--- QUESTION {idx+1} [{q['topic']}] ---")
        print(f"Question: \"{q['question_text']}\"")
        print(f"Ideal Answer: \"{q['ideal_answer']}\"")
        print(f"Validation Status: {q.get('validation_status')} (Status: {q.get('status')})")
        print(f"Source Quote: \"{q.get('source_quote', '')[:100]}...\"")

if __name__ == "__main__":
    sample_text = (
        "Unit 1: Vector Space Models & Distributional Semantics\n"
        "Mayank Singh - Department of Computer Science - Page 9/20 - Copyright 2026\n\n"
        "Distributional Semantics\n"
        "Distributional semantics is an approach to computational linguistics that represents word meaning "
        "based on patterns of co-occurrence in large textual corpora. The underlying intuition is that words "
        "occurring in similar contexts tend to share similar semantic meanings.\n\n"
        "DOC 1: An automobile is a wheeled motor vehicle used for transportation.\n"
        "or a word\n"
        "OUTPUT\n\n"
        "Pointwise Mutual Information (PMI)\n"
        "Pointwise Mutual Information is a statistical metric used in vector space models to measure the association "
        "between a word and its context. High PMI values indicate that two words co-occur significantly more often "
        "than expected by random chance.\n\n"
        "Cosine Similarity\n"
        "Cosine similarity measures the orientation between two sparse vector representations in high-dimensional space. "
        "It computes the normalized dot product of two word vectors to determine semantic relatedness regardless of vector magnitude."
    )
    fake_bytes = sample_text.encode("utf-8")
    trace_pdf_processing(fake_bytes, "nlp_sample.txt", "doc_trace_test_001")
