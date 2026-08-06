import time
import logging
from typing import List, Dict, Any, Optional
from app.services.document_processor import document_processor
from app.services.chunker import document_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

logger = logging.getLogger("vivabot.services.knowledge")

class KnowledgeService:
    """
    Deterministic Knowledge Base Service orchestrating document extraction,
    heading-aware chunking, BGE embeddings generation, and ChromaDB vector retrieval.
    Strictly NO LLM involved.
    """

    def process_and_index_document(
        self,
        file_bytes: bytes,
        filename: str,
        subject: str,
        topic: str = "General"
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # 1. Extraction
        pages_data = document_processor.extract_document(file_bytes, filename)
        if not pages_data:
            return {"status": "error", "message": "No text content extracted from file."}

        # 2. Chunking
        chunks = document_chunker.chunk_document(pages_data, subject, topic)
        if not chunks:
            return {"status": "error", "message": "Failed to generate text chunks."}

        # 3. Embedding Generation
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.generate_embeddings(chunk_texts)

        # 4. Storage in ChromaDB
        vector_store.add_chunks(chunks, embeddings)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"Ingested '{filename}': {len(pages_data)} pages, {len(chunks)} chunks in {elapsed_ms} ms.")

        return {
            "status": "success",
            "filename": filename,
            "subject": subject,
            "topic": topic,
            "total_pages": len(pages_data),
            "total_chunks": len(chunks),
            "processing_latency_ms": elapsed_ms
        }

    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 3,
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        # Generate Query Embedding deterministically
        query_vec = embedding_service.generate_query_embedding(query)

        # Query Vector Store
        retrieved_chunks = vector_store.search(
            query_embedding=query_vec,
            top_k=top_k,
            subject_filter=subject,
            topic_filter=topic
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"Search for '{query}' returned {len(retrieved_chunks)} chunks in {elapsed_ms} ms.")

        return {
            "query": query,
            "retrieved_count": len(retrieved_chunks),
            "retrieval_latency_ms": elapsed_ms,
            "results": retrieved_chunks
        }

knowledge_service = KnowledgeService()
