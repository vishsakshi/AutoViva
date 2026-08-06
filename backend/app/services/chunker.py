import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger("vivabot.services.chunker")

class DocumentChunker:
    """
    Heading-Aware Recursive Paragraph Chunker.
    Splits text along double newlines, newlines, and sentence boundaries
    to preserve complete academic definitions and question context.
    """
    def __init__(self, target_chunk_size: int = 500, chunk_overlap: int = 50):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_into_paragraphs(self, text: str) -> List[str]:
        # Split by double newline (paragraphs) first
        raw_paragraphs = text.split("\n\n")
        paragraphs = []
        for p in raw_paragraphs:
            cleaned = p.strip()
            if cleaned:
                paragraphs.append(cleaned)
        return paragraphs

    def chunk_page(self, page_data: Dict[str, Any], subject: str, topic: str = "General") -> List[Dict[str, Any]]:
        text = page_data["text"]
        source_file = page_data["source_file"]
        file_type = page_data.get("file_type", "pdf")
        page_number = page_data["page_number"]

        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = ""
        current_start = 0

        for p in paragraphs:
            if len(current_chunk) + len(p) + 2 <= self.target_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + p
                else:
                    current_chunk = p
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Keep overlap from end of current_chunk
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_chunk = (overlap_text + "\n\n" + p).strip()
                else:
                    # Single paragraph exceeds chunk size, split by sentences or lines
                    lines = p.split("\n")
                    for line in lines:
                        if len(current_chunk) + len(line) + 1 <= self.target_chunk_size:
                            current_chunk = (current_chunk + "\n" + line).strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = line.strip()

        if current_chunk:
            chunks.append(current_chunk)

        structured_chunks = []
        doc_id_prefix = source_file.replace(".", "_").replace(" ", "_").lower()

        for idx, chunk_text in enumerate(chunks):
            start_pos = text.find(chunk_text[:30]) if len(chunk_text) >= 30 else 0
            end_pos = start_pos + len(chunk_text)
            chunk_id = f"{doc_id_prefix}_p{page_number}_c{idx+1}_{uuid.uuid4().hex[:6]}"

            structured_chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "metadata": {
                    "chunk_id": chunk_id,
                    "source_file": source_file,
                    "file_type": file_type,
                    "subject": subject,
                    "topic": topic,
                    "page_number": page_number,
                    "start_char": max(0, start_pos),
                    "end_char": end_pos,
                    "word_count": len(chunk_text.split()),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            })

        return structured_chunks

    def chunk_document(self, pages_data: List[Dict[str, Any]], subject: str, topic: str = "General") -> List[Dict[str, Any]]:
        all_chunks = []
        for page in pages_data:
            page_chunks = self.chunk_page(page, subject, topic)
            all_chunks.extend(page_chunks)
        logger.info(f"Generated {len(all_chunks)} chunks across {len(pages_data)} pages for subject '{subject}'.")
        return all_chunks

document_chunker = DocumentChunker()
