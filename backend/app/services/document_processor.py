import io
import logging
from typing import List, Dict, Any
import fitz  # PyMuPDF
from pptx import Presentation

logger = logging.getLogger("vivabot.services.document_processor")

class DocumentProcessor:
    """
    Deterministic Document Processor for PDF, PPTX, and TXT files.
    Extracts text per page/slide with metadata.
    """

    def process_pdf(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Extracting text from PDF '{filename}' using PyMuPDF...")
        pages_data = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page_idx, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                # Basic text cleaning: normalize spaces
                cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
                cleaned_text = "\n".join(cleaned_lines)
                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": cleaned_text,
                    "source_file": filename,
                    "file_type": "pdf"
                })

        doc.close()
        logger.info(f"Extracted {len(pages_data)} pages from '{filename}'.")
        return pages_data

    def process_pptx(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Extracting text from PPTX '{filename}' using python-pptx...")
        slides_data = []
        prs = Presentation(io.BytesIO(file_bytes))

        for slide_idx, slide in enumerate(prs.slides):
            slide_texts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if p_text:
                            slide_texts.append(p_text)
            
            cleaned_text = "\n".join(slide_texts)
            if cleaned_text:
                slides_data.append({
                    "page_number": slide_idx + 1,
                    "text": cleaned_text,
                    "source_file": filename,
                    "file_type": "pptx"
                })

        logger.info(f"Extracted {len(slides_data)} slides from '{filename}'.")
        return slides_data

    def process_txt(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Extracting text from TXT '{filename}'...")
        text_content = file_bytes.decode("utf-8", errors="ignore").strip()
        if not text_content:
            return []
        
        # Split into logical sections or treat as single page
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)
        return [{
            "page_number": 1,
            "text": cleaned_text,
            "source_file": filename,
            "file_type": "txt"
        }]

    def extract_document(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext == "pdf":
            return self.process_pdf(file_bytes, filename)
        elif ext in ["pptx", "ppt"]:
            return self.process_pptx(file_bytes, filename)
        elif ext in ["txt", "md"]:
            return self.process_txt(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file extension '.{ext}'. Supported: .pdf, .pptx, .txt, .md")

document_processor = DocumentProcessor()
