import os
import time
import uuid
import logging
from typing import List, Dict, Any, Optional

from app.services.document_processor import document_processor
from app.services.chunker import document_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.topic_mapper import topic_mapper

logger = logging.getLogger("vivabot.services.knowledge")

class KnowledgeService:
    """
    Document-Scoped Knowledge Base Service.
    Orchestrates structure-aware document extraction, heading-aware chunking,
    BGE embeddings generation, ChromaDB vector indexing, and topic mapping.
    """

    def process_and_store_document(
        self,
        file_bytes: bytes,
        filename: str,
        subject: str = "General",
        topic: str = "General",
        viva_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        logger.info(f"[UPLOAD RECEIVED] Filename: '{filename}', Subject: '{subject}', Topic: '{topic}', Viva ID: '{viva_id}'")
        print(f"[UPLOAD RECEIVED] {filename}")

        # Extension validation
        allowed_extensions = ('.pdf', '.ppt', '.pptx', '.docx', '.txt', '.md')
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            err_msg = f"Unsupported file type '{ext}'. Allowed types: PDF, PPT, PPTX, DOCX, TXT."
            logger.error(f"[UPLOAD ERROR] {err_msg}")
            raise ValueError(err_msg)

        # 1. Assign unique Document ID
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"
        print(f"[SAVED] Document ID: {doc_id}")

        # 2. Text Extraction with Page & Section Hierarchy
        pages_data = document_processor.extract_document(file_bytes, filename)
        if not pages_data:
            err_msg = f"No text content could be extracted from '{filename}'. Please ensure the document is not an un-OCR scanned image or empty."
            logger.error(f"[TEXT EXTRACT ERROR] {err_msg}")
            raise ValueError(err_msg)

        print(f"[TEXT EXTRACTED] Extracted {len(pages_data)} pages/sections from '{filename}'")

        # 3. Structure-Aware Chunking with Metadata
        chunks = document_chunker.chunk_document(
            pages_data=pages_data,
            subject=subject,
            topic=topic,
            document_id=doc_id,
            viva_id=viva_id
        )
        if not chunks:
            err_msg = f"Failed to generate text chunks from extracted content in '{filename}'."
            logger.error(f"[CHUNK ERROR] {err_msg}")
            raise ValueError(err_msg)

        print(f"[CHUNKED] Generated {len(chunks)} heading-aware text chunks")

        # 4. Generate Topic & Section Map
        doc_topic_map = topic_mapper.build_topic_map(chunks)
        print(f"[TOPIC MAP] Identified {doc_topic_map['total_topics']} distinct topics across {len(doc_topic_map['sections'])} sections")

        # 5. Embedding Generation
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.generate_embeddings(chunk_texts)
        print(f"[EMBEDDINGS CREATED] Generated {len(embeddings)} BAAI/bge-small-en-v1.5 vector embeddings")

        # 6. ChromaDB Vector Store Storage with Strict Document Scope
        vector_store.add_chunks(chunks, embeddings)
        print(f"[CHROMADB STORED] Successfully inserted {len(chunks)} chunks into ChromaDB Knowledge Base (Doc ID: {doc_id})")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        print(f"[UPLOAD SUCCESS] Finished indexing '{filename}' in {elapsed_ms} ms")
        logger.info(f"Ingested '{filename}': {len(pages_data)} pages, {len(chunks)} chunks in {elapsed_ms} ms.")

        return {
            "success": True,
            "status": "success",
            "document_id": doc_id,
            "viva_id": viva_id or "",
            "filename": filename,
            "subject": subject,
            "topic": topic,
            "total_pages": len(pages_data),
            "chunks": len(chunks),
            "chunks_stored": len(chunks),
            "chunks_processed": len(chunks),
            "topic_map": doc_topic_map,
            "embedding_count": len(embeddings),
            "processing_latency_ms": elapsed_ms
        }

    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        viva_id: Optional[str] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        query_vec = embedding_service.generate_query_embedding(query)

        retrieved_chunks = vector_store.search(
            query_embedding=query_vec,
            top_k=top_k,
            document_id=document_id,
            viva_id=viva_id,
            subject_filter=subject,
            topic_filter=topic
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(f"Search for '{query}' (doc_id={document_id}) returned {len(retrieved_chunks)} chunks in {elapsed_ms} ms.")

        return {
            "query": query,
            "document_id": document_id,
            "viva_id": viva_id,
            "retrieved_count": len(retrieved_chunks),
            "retrieval_latency_ms": elapsed_ms,
            "results": retrieved_chunks
        }

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        return vector_store.get_document_chunks(document_id)

knowledge_service = KnowledgeService()
