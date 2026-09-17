import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger("vivabot.services.vector_store")

class VectorStore:
    """
    ChromaDB Vector Database manager with strict document and viva isolation.
    Ensures that question generation only ever retrieves chunks from the specific uploaded document.
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
        logger.info(f"Successfully upserted {len(ids)} chunks to ChromaDB collection '{self.collection_name}'. Total vectors: {self.collection.count()}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        document_id: Optional[str] = None,
        viva_id: Optional[str] = None,
        subject_filter: Optional[str] = None,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        total_vectors = self.collection.count()
        if total_vectors == 0:
            logger.warning("[CHROMADB SEARCH] Collection is empty.")
            return []

        # Strict Document Isolation Filter
        where_clause = {}
        if document_id:
            where_clause["document_id"] = document_id
        elif viva_id:
            where_clause["viva_id"] = viva_id
        elif subject_filter and subject_filter not in ["Academic Viva Syllabus", "General"]:
            where_clause["subject"] = subject_filter

        logger.info(f"[CHROMADB SEARCH] Where Clause: {where_clause}, Top K: {top_k}, Total Vectors: {total_vectors}")

        results = None
        if where_clause:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, total_vectors),
                    where=where_clause,
                    include=["documents", "metadatas", "distances"]
                )
            except Exception as e:
                logger.warning(f"Filtered ChromaDB query error: {e}")
                results = None

        # If document_id/viva_id was supplied and returned 0 results, do NOT leak other documents!
        if (document_id or viva_id) and (not results or not results.get("ids") or not results["ids"][0]):
            logger.info(f"[CHROMADB ISOLATION] Scoped query for doc '{document_id or viva_id}' returned 0 matches.")
            return []

        # Fallback only when NO document/viva isolation was requested (e.g. general test queries)
        if not results or not results.get("ids") or not results["ids"][0]:
            if not document_id and not viva_id:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, total_vectors),
                    include=["documents", "metadatas", "distances"]
                )

        formatted_results = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]

            for i in range(len(ids)):
                similarity_score = max(0.0, 1.0 - distances[i])
                page_num = metadatas[i].get("page_number", metadatas[i].get("page", 1))
                sec_title = metadatas[i].get("section_title", "Overview")

                formatted_results.append({
                    "chunk_id": ids[i],
                    "text": documents[i],
                    "metadata": metadatas[i],
                    "page_number": page_num,
                    "section_title": sec_title,
                    "document_id": metadatas[i].get("document_id", ""),
                    "viva_id": metadatas[i].get("viva_id", ""),
                    "distance": distances[i],
                    "similarity_score": round(similarity_score, 4)
                })

        return formatted_results

    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Fetches all chunks belonging to a specific document_id directly from ChromaDB.
        """
        try:
            res = self.collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            chunks = []
            if res and res.get("ids"):
                for i in range(len(res["ids"])):
                    chunks.append({
                        "chunk_id": res["ids"][i],
                        "text": res["documents"][i],
                        "metadata": res["metadatas"][i],
                        "page_number": res["metadatas"][i].get("page_number", 1),
                        "section_title": res["metadatas"][i].get("section_title", "Overview")
                    })
            return chunks
        except Exception as e:
            logger.error(f"Error fetching document chunks for '{document_id}': {e}")
            return []

    def delete_document_chunks(self, document_id: str) -> int:
        """Deletes all chunks from ChromaDB for a given document_id."""
        if not document_id:
            return 0
        try:
            res = self.collection.get(where={"document_id": document_id})
            if res and res.get("ids"):
                ids_to_del = res["ids"]
                self.collection.delete(ids=ids_to_del)
                logger.info(f"Deleted {len(ids_to_del)} vectors for document_id '{document_id}' from ChromaDB.")
                return len(ids_to_del)
        except Exception as e:
            logger.error(f"Error deleting chunks for document '{document_id}': {e}")
        return 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_chunks": self.collection.count(),
            "collection_name": self.collection_name,
            "storage_path": self.persist_directory
        }

vector_store = VectorStore()
