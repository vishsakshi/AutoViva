import os
import pymongo
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from app.services.viva_creation_service import viva_creation_service, VivaCreateRequest

def test_complete_upload_pipeline():
    print("=" * 90)
    print("AUTOVIVA SYLLABUS UPLOAD & CHROMADB INDEXING END-TO-END SUITE")
    print("=" * 90)

    # 1. Create a sample syllabus document file
    sample_filename = "NLP_Unit3_Transformers_Syllabus.txt"
    sample_content = (
        "UNIT 3: SEQUENCE TO SEQUENCE MODELS & TRANSFORMERS\n"
        "Topic 3.1: Encoder-Decoder Architecture and Attention Mechanisms.\n"
        "Sequence to sequence models utilize recurrent networks or Transformer blocks to convert input sequences into output sequences.\n"
        "Bahdanau additive attention and Luong multiplicative attention dynamically compute context vectors over input hidden states.\n\n"
        "Topic 3.2: Transformer Self-Attention and Multi-Head Attention.\n"
        "The Transformer architecture replaces recurrence entirely with Scaled Dot-Product Self-Attention.\n"
        "Query (Q), Key (K), and Value (V) matrices map tokens to high-dimensional representation spaces.\n"
        "Multi-Head Attention allows the model to jointly attend to information from different representation subspaces at different positions.\n"
    ).encode("utf-8")

    # 2. Execute process_and_store_document
    print("\n--- STEP 1: Executing process_and_store_document ---")
    res = knowledge_service.process_and_store_document(
        file_bytes=sample_content,
        filename=sample_filename,
        subject="Natural Language Processing",
        topic="Transformers & Attention",
        viva_id="viva_test_nlp_001"
    )

    print("\nUpload Response JSON:")
    print(res)

    assert res["success"] is True
    assert res["chunks"] > 0
    assert res["embedding_count"] == res["chunks"]
    print(f"\n[VERIFIED]: Processed {res['chunks']} chunks with {res['embedding_count']} BGE embeddings into ChromaDB!")

    # 3. Query ChromaDB Vector Store to verify retrieval
    print("\n--- STEP 2: Querying ChromaDB Vector Store for Retrieved Chunks ---")
    query_str = "Scaled Dot-Product Self Attention Query Key Value"
    search_res = knowledge_service.search_knowledge_base(
        query=query_str,
        top_k=2,
        subject="Natural Language Processing"
    )

    print(f"Query: '{query_str}'")
    print(f"Retrieved {search_res['retrieved_count']} chunks from ChromaDB:")
    for idx, item in enumerate(search_res["results"]):
        print(f"  Chunk {idx + 1} (Score: {item['similarity_score']:.4f}): {item['text'][:120]}...")

    assert search_res["retrieved_count"] > 0, "No chunks retrieved from ChromaDB!"
    print("\n" + "=" * 90)
    print("SYLLABUS UPLOAD & CHROMADB INDEXING VERIFIED 100% WORKING!")
    print("=" * 90)

if __name__ == "__main__":
    test_complete_upload_pipeline()
