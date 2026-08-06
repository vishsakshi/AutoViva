import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

logger = logging.getLogger("vivabot.services.reranker")

class RerankerService:
    """
    Reranker Service using Cross-Encoder models (BAAI/bge-reranker-small or ms-marco-MiniLM-L-6-v2).
    Evaluates joint (Query, Chunk) similarity to re-score and re-rank initial vector retrieval candidates.
    """
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            logger.info(f"Loading Cross-Encoder Reranker model '{self.model_name}'...")
            self._model = CrossEncoder(self.model_name)
            logger.info(f"Cross-Encoder model '{self.model_name}' ready.")
        return self._model

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not candidate_chunks:
            return []

        # Prepare (query, chunk_text) pairs for cross-encoder scoring
        pairs = [(query, chunk["text"]) for chunk in candidate_chunks]
        scores = self.model.predict(pairs)

        # Attach rerank score to chunks
        scored_chunks = []
        for idx, chunk in enumerate(candidate_chunks):
            # Normalize cross-encoder logit score into [0, 1] range using sigmoid if needed
            raw_score = float(scores[idx])
            chunk_copy = dict(chunk)
            chunk_copy["rerank_score"] = round(raw_score, 4)
            scored_chunks.append(chunk_copy)

        # Sort descending by rerank score
        reranked = sorted(scored_chunks, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]

reranker_service = RerankerService()
