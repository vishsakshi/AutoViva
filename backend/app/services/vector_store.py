import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger("vivabot.services.vector_store")

class VectorStore:
    """
    ChromaDB Vector Database manager with local disk persistence.
    Provides HNSW indexing, document upsertion, and metadata filtering.
    """
    def __init__(self, persist_directory: str = "data/vector_store", collection_name: str = "vivabot_knowledge"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        os.makedirs(self.persist_directory, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB PersistentClient at '{self.persist_directory}'...")
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaDB collection '{self.collection_name}' ready with {self.collection.count()} vectors.")

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        if not chunks:
            return

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Successfully upserted {len(ids)} chunks to vector store.")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 3,
        subject_filter: Optional[str] = None,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        where_clause = {}
        if subject_filter:
            where_clause["subject"] = subject_filter
        if topic_filter:
            where_clause["topic"] = topic_filter

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            for i in range(len(ids)):
                # Convert cosine distance to similarity score
                similarity_score = max(0.0, 1.0 - distances[i])
                formatted_results.append({
                    "chunk_id": ids[i],
                    "text": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i],
                    "similarity_score": round(similarity_score, 4)
                })

        return formatted_results

    def get_stats() -> Dict[str, Any]:
        return {
            "total_chunks": self.collection.count(),
            "collection_name": self.collection_name,
            "storage_path": self.persist_directory
        }

vector_store = VectorStore()
