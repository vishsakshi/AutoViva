import logging
from typing import List, Dict, Any

logger = logging.getLogger("vivabot.services.context_builder")

class ContextBuilder:
    """
    Context Construction Service for VivaBot.
    Formats, deduplicates, and caps retrieved knowledge chunks into
    a clean, metadata-tagged context block for LLM consumption.
    """
    def __init__(self, max_chunks: int = 3, max_chars: int = 3500, min_similarity_threshold: float = 0.35):
        self.max_chunks = max_chunks
        self.max_chars = max_chars
        self.min_similarity_threshold = min_similarity_threshold

    def build_context(self, retrieved_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not retrieved_results:
            return {
                "context_text": "No relevant academic context found.",
                "used_chunks_count": 0,
                "total_chars": 0,
                "sources": []
            }

        # 1. Filter out low similarity results below threshold
        filtered = [
            r for r in retrieved_results 
            if r.get("similarity_score", 1.0) >= self.min_similarity_threshold
        ]

        # 2. Sort by similarity score descending
        sorted_results = sorted(filtered, key=lambda x: x.get("similarity_score", 0), reverse=True)

        # 3. Deduplicate based on text snippet overlap
        unique_chunks = []
        seen_texts = set()

        for item in sorted_results:
            text = item.get("text", "").strip()
            # Simple substring deduplication
            if not any(text in seen or seen in text for seen in seen_texts):
                seen_texts.add(text)
                unique_chunks.append(item)
            if len(unique_chunks) >= self.max_chunks:
                break

        # 4. Assemble context block with metadata headers and character budget enforcement
        context_blocks = []
        sources_used = []
        total_chars = 0

        for idx, chunk in enumerate(unique_chunks, 1):
            meta = chunk.get("metadata", {})
            source_file = meta.get("source_file", "unknown")
            page_num = meta.get("page_number", "N/A")
            subject = meta.get("subject", "General")
            topic = meta.get("topic", "General")
            text = chunk.get("text", "").strip()

            header = f"[SECTION {idx} | Source: {source_file} (Page {page_num}) | Subject: {subject} | Topic: {topic}]"
            block = f"{header}\n{text}"

            if total_chars + len(block) > self.max_chars and context_blocks:
                logger.info(f"Context size limit ({self.max_chars} chars) reached at chunk #{idx}. Truncating.")
                break

            context_blocks.append(block)
            total_chars += len(block)
            sources_used.append({
                "source_file": source_file,
                "page_number": page_num,
                "chunk_id": chunk.get("chunk_id"),
                "similarity_score": chunk.get("similarity_score")
            })

        final_context_text = "\n\n".join(context_blocks)

        return {
            "context_text": final_context_text,
            "used_chunks_count": len(context_blocks),
            "total_chars": len(final_context_text),
            "sources": sources_used
        }

context_builder = ContextBuilder()
