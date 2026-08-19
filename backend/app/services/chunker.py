import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("vivabot.services.chunker")

class DocumentChunker:
    """
    Structure & Heading-Aware Recursive Document Chunker.
    Preserves document hierarchy (document_id, viva_id, page_number, section_title)
    and ensures complete academic definitions and technical concepts remain intact.
    """
    def __init__(self, target_chunk_size: int = 500, chunk_overlap: int = 60):
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

    def chunk_page(
        self,
        page_data: Dict[str, Any],
        subject: str,
        topic: str = "General",
        document_id: str = "doc_default",
        viva_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        text = page_data["text"]
        source_file = page_data["source_file"]
        file_type = page_data.get("file_type", "pdf")
        page_number = page_data.get("page_number", 1)
        section_title = page_data.get("section_title", topic or "Overview")
        detected_sections = page_data.get("detected_sections", [section_title])

        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            if len(current_chunk) + len(p) + 2 <= self.target_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + p
                else:
                    current_chunk = p
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_chunk = (overlap_text + "\n\n" + p).strip()
                else:
                    # Single paragraph exceeds chunk size, split by sentences
                    sentences = p.split(". ")
                    for s in sentences:
                        s_clean = s.strip()
                        if not s_clean:
                            continue
                        if not s_clean.endswith("."):
                            s_clean += "."
                        if len(current_chunk) + len(s_clean) + 1 <= self.target_chunk_size:
                            current_chunk = (current_chunk + " " + s_clean).strip()
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = s_clean

        if current_chunk:
            chunks.append(current_chunk)

        structured_chunks = []
        doc_prefix = document_id.replace("-", "_")

        for idx, chunk_text in enumerate(chunks):
            chunk_id = f"{doc_prefix}_p{page_number}_c{idx+1}_{uuid.uuid4().hex[:6]}"
            
            # Determine specific section for chunk if detected
            chunk_section = section_title
            for sec in detected_sections:
                if sec.lower() in chunk_text.lower():
                    chunk_section = sec
                    break

            structured_chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "document_id": document_id,
                "viva_id": viva_id or "",
                "page_number": page_number,
                "section_title": chunk_section,
                "metadata": {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "viva_id": viva_id or "",
                    "source_file": source_file,
                    "filename": source_file,
                    "file_type": file_type,
                    "subject": subject,
                    "topic": topic,
                    "page_number": page_number,
                    "page": page_number,
                    "section_title": chunk_section,
                    "word_count": len(chunk_text.split()),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            })

        return structured_chunks

    def chunk_document(
        self,
        pages_data: List[Dict[str, Any]],
        subject: str,
        topic: str = "General",
        document_id: str = "doc_default",
        viva_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        all_chunks = []
        for page in pages_data:
            page_chunks = self.chunk_page(
                page,
                subject=subject,
                topic=topic,
                document_id=document_id,
                viva_id=viva_id
            )
            all_chunks.extend(page_chunks)
        logger.info(f"Generated {len(all_chunks)} chunks for document '{document_id}' ({len(pages_data)} pages, subject '{subject}').")
        return all_chunks

document_chunker = DocumentChunker()
