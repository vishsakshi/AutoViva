import logging
from typing import List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("vivabot.services.embedding")

class EmbeddingService:
    """
    Local Embedding Service utilizing BAAI/bge-small-en-v1.5.
    Provides 384-dimensional dense vector embeddings with top MTEB retrieval performance.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(f"Loading local embedding model '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model '{self.model_name}' loaded successfully into RAM.")
        return self._model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # BGE models perform best with clean sentence/paragraph inputs
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def generate_query_embedding(self, query: str) -> List[float]:
        # BGE recommendation: query prefix can be added for retrieval tasks
        query_text = f"Represent this sentence for searching relevant passages: {query}"
        embedding = self.model.encode(query_text, normalize_embeddings=True, show_progress_bar=False)
        return embedding.tolist()

embedding_service = EmbeddingService()
