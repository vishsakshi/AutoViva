import io
import re
import logging
from typing import List, Dict, Any
import fitz  # PyMuPDF
from pptx import Presentation

logger = logging.getLogger("vivabot.services.document_processor")

class DocumentProcessor:
    """
    Academic Document Processor for PDF, PPTX, DOCX, and TXT files.
    Extracts clean text while preserving page numbers, section headers, and academic structure.
    Strips noise (page numbers like 9/20, author names, headers, footers, copyright, slide counts).
    """

    def clean_academic_line(self, line: str) -> bool:
        """
        Filters out non-academic noise lines. Returns False if line should be discarded.
        """
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 2:
            return False

        # Page / Slide number patterns: e.g. "9/20", "Page 9", "Slide 12", "9 of 20", "Page 1 of 15"
        if re.match(r"^\s*\d+\s*/\s*\d+\s*$", line_clean):
            return False
        if re.match(r"^\s*\d+\s*of\s*\d+\s*$", line_clean, re.IGNORECASE):
            return False
        if re.match(r"^\s*(page|slide)\s+\d+(\s*(of|/)\s*\d+)?\s*$", line_clean, re.IGNORECASE):
            return False
        if re.match(r"^\s*-\s*\d+\s*-\s*$", line_clean):
            return False

        # Document labels / example artifacts / single noise words: e.g. "DOC 1:", "OUTPUT", "or a word"
        if re.match(r"^\s*(doc|document|example|fig|figure|table|slide|page)\s*\d+[\s:\.\-]*", line_clean, re.IGNORECASE):
            return False
        if line_clean.lower() in ["output", "input", "example", "table", "figure", "result", "code", "data", "test", "index"]:
            return False
        if re.match(r"^(or|and|in|of|to|with|by|for|from)\s+[a-z]{1,4}\s+[a-z]{1,8}$", line_clean, re.IGNORECASE):
            return False

        # Common author / copyright / institute noise patterns
        noise_patterns = [
            r"(?i)mayank\s+singh",
            r"(?i)copyright\s+.*",
            r"(?i)all\s+rights\s+reserved",
            r"(?i)department\s+of\s+computer\s+science",
            r"(?i)university\s+of\s+.*",
            r"(?i)lecture\s+\d+",
            r"(?i)slide\s+\d+"
        ]
        for pat in noise_patterns:
            if re.search(pat, line_clean):
                return False

        return True

    def detect_section_header(self, line: str) -> str:
        """
        Detects if a line is a real section or unit heading.
        e.g., 'Unit 1: Vector Space Models', 'Chapter 3: NAPT', '3.1 Cosine Similarity'
        Excludes noise, single words ('OUTPUT'), author names, and document labels ('DOC 1').
        """
        line_clean = line.strip()
        l_lower = line_clean.lower()

        # Generic metadata, citation, email, and document artifact detection across domains
        if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line_clean) or re.search(r"\b(doi|isbn|issn|http|https|www)\b", l_lower):
            return ""
        if re.search(r"^\s*(doc|document|example|fig|figure|table|slide|page)\s*\d+[\s:\.\-]", l_lower):
            return ""
        if re.search(r"^\s*\d+\s*(of|/)\s*\d+\s*$", line_clean) or re.search(r"^\s*(copyright|all rights reserved|published by|printed in)\b", l_lower):
            return ""

        # Generic structural words: skip if line is purely structural metadata
        structural_terms = {"output", "input", "example", "table", "figure", "overview", "introduction", "content", "contents", "syllabus", "extracted", "presentation"}
        line_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", l_lower))
        if line_words and line_words.issubset(structural_terms):
            return ""

        # Check for explicit heading keywords or numbering
        heading_patterns = [
            r"^(unit|chapter|module|section|part)\s*(\d+|[IVXLCDM]+)[\s:\.\-]+(.+)$",
            r"^(\d+\.\d+(\.\d+)?)\s+([A-Z].+)$"
        ]
        for pat in heading_patterns:
            m = re.match(pat, line_clean, re.IGNORECASE)
            if m:
                return line_clean

        # All-caps short header check
        if re.match(r"^([A-Z\s]{5,40})$", line_clean) and len(line_clean.split()) >= 2:
            return line_clean

        return ""

    def process_pdf(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Extracting clean academic text from PDF '{filename}' using PyMuPDF...")
        pages_data = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        current_section = "Academic Content"

        for page_idx, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                raw_lines = text.splitlines()
                cleaned_lines = []
                page_sections = []

                for line in raw_lines:
                    line_str = line.strip()
                    if self.clean_academic_line(line_str):
                        header = self.detect_section_header(line_str)
                        if header:
                            current_section = header
                            page_sections.append(header)
                            if not cleaned_lines or cleaned_lines[-1].lower() != line_str.lower():
                                cleaned_lines.append(line_str)
                        else:
                            # Skip line if it duplicates current section title or preceding line
                            if cleaned_lines and (line_str.lower() == cleaned_lines[-1].lower() or line_str.lower() == current_section.lower()):
                                continue
                            cleaned_lines.append(line_str)

                cleaned_text = "\n".join(cleaned_lines)
                if cleaned_text:
                    pages_data.append({
                        "page_number": page_idx + 1,
                        "text": cleaned_text,
                        "source_file": filename,
                        "file_type": "pdf",
                        "section_title": current_section,
                        "detected_sections": page_sections or [current_section]
                    })

        doc.close()
        logger.info(f"Extracted {len(pages_data)} clean pages from '{filename}'.")
        return pages_data

    def process_pptx(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Extracting clean text from PPTX '{filename}'...")
        slides_data = []
        prs = Presentation(io.BytesIO(file_bytes))
        current_section = "Academic Presentation"

        for slide_idx, slide in enumerate(prs.slides):
            slide_texts = []
            slide_title = ""

            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if p_text and self.clean_academic_line(p_text):
                            header = self.detect_section_header(p_text)
                            if header and not slide_title:
                                slide_title = header
                                current_section = header
                            slide_texts.append(p_text)
            
            cleaned_text = "\n".join(slide_texts)
            if cleaned_text:
                slides_data.append({
                    "page_number": slide_idx + 1,
                    "text": cleaned_text,
                    "source_file": filename,
                    "file_type": "pptx",
                    "section_title": slide_title or current_section,
                    "detected_sections": [slide_title or current_section]
                })

        logger.info(f"Extracted {len(slides_data)} clean slides from '{filename}'.")
        return slides_data

    def process_txt(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Extracting clean text from TXT '{filename}'...")
        text_content = file_bytes.decode("utf-8", errors="ignore").strip()
        if not text_content:
            return []
        
        lines = text_content.splitlines()
        cleaned_lines = []
        sections_found = []
        current_sec = "Overview"

        for line in lines:
            if self.clean_academic_line(line):
                header = self.detect_section_header(line)
                if header:
                    current_sec = header
                    sections_found.append(header)
                cleaned_lines.append(line.strip())

        cleaned_text = "\n".join(cleaned_lines)
        return [{
            "page_number": 1,
            "text": cleaned_text,
            "source_file": filename,
            "file_type": "txt",
            "section_title": current_sec,
            "detected_sections": sections_found or [current_sec]
        }]

    def process_docx(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Extracting clean text from DOCX '{filename}'...")
        lines = []
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                xml_content = z.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                text_elems = tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                lines = [t.text.strip() for t in text_elems if t.text and t.text.strip()]
        except Exception as e:
            text_content = file_bytes.decode("utf-8", errors="ignore").strip()
            lines = [l.strip() for l in text_content.splitlines() if l.strip()]

        cleaned_lines = [l for l in lines if self.clean_academic_line(l)]
        cleaned_text = "\n".join(cleaned_lines)
        return [{
            "page_number": 1,
            "text": cleaned_text,
            "source_file": filename,
            "file_type": "docx",
            "section_title": "Academic Document",
            "detected_sections": ["Academic Document"]
        }]

    def extract_document(self, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext == "pdf":
            pages_data = self.process_pdf(file_bytes, filename)
        elif ext in ["pptx", "ppt"]:
            pages_data = self.process_pptx(file_bytes, filename)
        elif ext == "docx":
            pages_data = self.process_docx(file_bytes, filename)
        elif ext in ["txt", "md"]:
            pages_data = self.process_txt(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file extension '.{ext}'. Supported: .pdf, .pptx, .txt, .md, .docx")

        total_extracted_len = sum(len(p.get("text", "").strip()) for p in pages_data)
        if not pages_data or total_extracted_len < 100:
            raise ValueError(
                f"INSUFFICIENT_DOCUMENT_TEXT: Insufficient readable academic text extracted from '{filename}' ({total_extracted_len} characters found). "
                "The file may be a scanned image-only PDF, empty, or unreadable binary."
            )

        return pages_data

document_processor = DocumentProcessor()
