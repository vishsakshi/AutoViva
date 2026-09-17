import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("vivabot.services.topic_mapper")

class DocumentTopicMapper:
    """
    Structure & Academic-Concept Aware Topic Mapping Engine for AutoViva.
    
    Responsibilities:
    - Parses document hierarchy into Units, Chapters, Sections, and Academic Concepts.
    - Classifies extracted text into:
        A. ACADEMIC_CONCEPT (Valid candidate topic for question generation)
        B. SUBCONCEPT (Valid)
        C. EXAMPLE (Valid as evidence context, REJECTED as a standalone topic title)
        D. DOCUMENT_METADATA / ARTIFACT (Strictly REJECTED: "DOC 1", "OUTPUT", "Page 9 of 20", "Mayank Singh")
        E. NOISE (Strictly REJECTED: "or a word", "and the", incomplete fragments)
    - Normalizes question-formatted headings ("What is Semantics?" -> "Semantics").
    - Prevents repeating topic titles and assigns coherent evidence packages.
    """

    def is_valid_academic_topic_line(self, line: str) -> bool:
        """Determines if a string represents a valid candidate academic topic or noise fragment."""
        l_clean = line.strip()
        if not l_clean or len(l_clean) < 3:
            return False

        l_lower = l_clean.lower()

        # Reject prepositions or conjunction fragments e.g. "or a word", "and the", "in a", "for a"
        if re.match(r"^(or|and|in|of|to|with|by|for|from|a|an|the|is|are|was|were)\s+", l_lower):
            return False

        if l_lower.endswith(" or") or l_lower.endswith(" and") or l_lower.endswith(" a") or l_lower.endswith(" in"):
            return False

        # Reject document/example labels: e.g. "DOC 1:", "DOC 2:", "EXAMPLE 1:", "FIG 2"
        if re.match(r"^\s*(doc|document|example|ex|fig|figure|table|slide|page)\s*\d+[\s:\.\-]*", l_lower):
            return False

        # Reject slide numbers or fractions: e.g. "9/20", "Slide 9"
        if re.match(r"^\s*\d+\s*/\s*\d+\s*$", l_clean) or re.match(r"^\s*(slide|page)\s+\d+", l_lower):
            return False

        # Generic structural and metadata term set
        structural_terms = {
            "content", "contents", "syllabus", "extracted", "document", "presentation", "slide", "slides",
            "section", "chapter", "unit", "module", "part", "overview", "summary", "introduction",
            "index", "table", "figure", "fig", "example", "ex", "output", "input", "data", "result",
            "references", "bibliography", "citation", "appendix", "preface", "acknowledgements",
            "copyright", "rights", "reserved", "published", "publisher", "author", "authors",
            "department", "faculty", "university", "institute", "school", "college",
            "lecture", "lectures", "note", "notes", "course", "courses", "instructor", "instructors",
            "professor", "professors", "prof", "dr", "written", "edited", "page", "pages", "cs224n"
        }

        words = set(re.findall(r"\b[a-zA-Z]{2,}\b", l_lower))
        if words and words.intersection(structural_terms):
            return False

        # Reject URLs, emails, dates, or publication metadata headers
        if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", l_clean) or re.search(r"\b(doi|isbn|issn|http|https|www)\b", l_lower):
            return False

        # Reject author names, instructor details, or lecture note header attributions
        if re.search(r"\b(prof|professor|dr|instructor|instructors|lecture\s+notes|notes\s+by|written\s+by|edited\s+by|authored\s+by|course\s+instructors)\b", l_lower):
            return False

        # Reject long conversational sentences (topics must be concise concepts)
        if len(l_clean.split()) > 7 and not re.match(r"^(unit|chapter|section|module)", l_lower):
            return False

        return True

    def clean_concept_name(self, raw_name: str) -> str:
        """Cleans leading numbers, question prefixes, and document artifacts from raw concept titles."""
        name = raw_name.strip()

        # Normalize question headings: "What is Semantics?" -> "Semantics"
        m_q = re.match(r"^(what|how|why)\s+(is|are|does|do)\s+(.+?)[\?\.\:]*$", name, re.IGNORECASE)
        if m_q:
            name = m_q.group(3).strip()

        # Remove leading noise prefixes: "OUTPUT", "INPUT", "EXAMPLE", "DOC 1", "PAGE 9"
        name = re.sub(r"^\s*(output|input|example|table|figure|doc|document|slide|page)\b[:\.\-]*\s*", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"^\s*(doc|document|example|ex|fig|figure|table|slide|page)\s*\d+[\s:\.\-]*", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"^(unit|chapter|topic|section|module|part|\d+)\s*[:\.\-]?\s*", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"^\d+[\.:\-]\s*", "", name).strip()

        # Remove leading structural/overview introductory phrases
        name = re.sub(r"^\s*(introduction\s+to|overview\s+of|basics\s+of|fundamentals\s+of|principles\s+of|notes\s+on|guide\s+to)\s+", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"\s+\b(overview|notes|guide|lecture|lectures|course|courses)\b", "", name, flags=re.IGNORECASE).strip()

        name = re.sub(r"\s+", " ", name)
        name = name.rstrip(".:,-? ")

        # Deduplicate repeated words e.g. "Distributional Semantics Distributional" -> "Distributional Semantics"
        words = name.split()
        dedup_words = []
        for w in words:
            if not dedup_words or w.lower() != dedup_words[-1].lower():
                dedup_words.append(w)

        if len(dedup_words) >= 3 and dedup_words[0].lower() == dedup_words[-1].lower():
            dedup_words.pop()

        name = " ".join(dedup_words)

        parts = name.split()
        if len(parts) >= 4:
            half = len(parts) // 2
            if [p.lower() for p in parts[:half]] == [p.lower() for p in parts[half:2*half]]:
                name = " ".join(parts[:half])

        if len(name) > 55:
            name = name[:55].strip() + "..."
        return name

    def classify_academic_topic_type(self, topic_title: str, text_context: str) -> str:
        """
        Classifies candidate topic into:
        - ACADEMIC_CONCEPT (Valid for QGen Topic Target)
        - SUBCONCEPT (Valid)
        - EXAMPLE (Valid for evidence context, excluded as standalone topic title)
        - DOCUMENT_METADATA (Reject)
        - NOISE (Reject)
        """
        t_clean = topic_title.strip()
        t_lower = t_clean.lower()

        if not self.is_valid_academic_topic_line(t_clean):
            return "NOISE"

        if re.match(r"^(doc|document|page|slide|figure|table)\s*\d+", t_lower):
            return "DOCUMENT_METADATA"

        # Check if topic title contains structural or metadata terms
        structural_terms = {"content", "contents", "syllabus", "extracted", "document", "presentation", "slide", "slides", "section", "chapter", "unit", "overview", "lecture", "notes", "course", "instructor", "instructors", "prof", "professor", "dr"}
        words = set(re.findall(r"\b[a-zA-Z]{2,}\b", t_lower))
        if words and words.intersection(structural_terms):
            return "DOCUMENT_METADATA"

        return "ACADEMIC_CONCEPT"

    def extract_candidate_concepts_from_text(self, text: str) -> List[str]:
        """
        Extracts high-value academic noun phrases and concept headings from section text.
        e.g. "Distributional Semantics", "Vector Space Models", "Pointwise Mutual Information (PMI)"
        """
        candidates = []

        # Filter out lines that contain author attributions or course headers
        clean_lines = []
        for line in text.splitlines():
            l_str = line.strip()
            l_low = l_str.lower()
            if any(k in l_low for k in ["instructor", "prof.", "dr.", "lecture notes", "written by", "edited by", "course", "cs224n", "@", "copyright"]):
                continue
            clean_lines.append(l_str)

        clean_text = "\n".join(clean_lines)

        # 1. Regex for capitalized academic terms (e.g. "Distributional Semantics", "Cosine Similarity", "ACID Properties")
        concept_matches = re.findall(r"\b([A-Z][a-zA-Z0-9\-\']+(?:\s+[A-Z][a-zA-Z0-9\-\']+){1,3})\b", clean_text)
        for cm in concept_matches:
            c_clean = self.clean_concept_name(cm)
            if self.is_valid_academic_topic_line(c_clean) and c_clean not in candidates:
                if self.classify_academic_topic_type(c_clean, clean_text) in ["ACADEMIC_CONCEPT", "SUBCONCEPT"]:
                    candidates.append(c_clean)

        # 2. Key academic definitions in text e.g. "X is defined as...", "X represents..."
        def_matches = re.findall(r"([A-Z][a-zA-Z0-9\s]{3,35})\s+(?:is defined as|refers to|represents|is the study of|allows)", clean_text)
        for dm in def_matches:
            d_clean = self.clean_concept_name(dm)
            if self.is_valid_academic_topic_line(d_clean) and d_clean not in candidates:
                if self.classify_academic_topic_type(d_clean, clean_text) in ["ACADEMIC_CONCEPT", "SUBCONCEPT"]:
                    candidates.append(d_clean)

        return candidates

    def build_topic_map(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Structure-Aware Academic Topic & Section Map Builder.
        Constructs a clean academic syllabus hierarchy:
        Document -> Sections -> Academic Topics -> Evidence Chunks.
        """
        if not chunks:
            return {"sections": {}, "topics": [], "total_topics": 0}

        sections_dict: Dict[str, List[Dict[str, Any]]] = {}
        for c in chunks:
            sec = c.get("section_title") or c.get("metadata", {}).get("section_title") or "Core Syllabus"
            if sec not in sections_dict:
                sections_dict[sec] = []
            sections_dict[sec].append(c)

        topics_list: List[Dict[str, Any]] = []
        topic_counter = 1
        seen_titles = set()

        for sec_title, sec_chunks in sections_dict.items():
            sec_pages = list(set([c.get("page_number", c.get("metadata", {}).get("page_number", 1)) for c in sec_chunks]))
            sec_chunk_ids = [c.get("chunk_id") for c in sec_chunks]
            combined_text = "\n\n".join([c.get("text", "") for c in sec_chunks])

            # Extract validated candidate concepts from section text
            extracted_concepts = self.extract_candidate_concepts_from_text(combined_text) if hasattr(self, 'extract_candidate_concepts_from_text') else []

            # Also inspect headings and paragraph openings
            paragraphs = [p.strip() for p in combined_text.split("\n\n") if len(p.strip()) > 10]
            for p in paragraphs:
                lines = [l.strip() for l in p.splitlines() if len(l.strip()) > 3]
                if lines:
                    first_line = lines[0]
                    if self.is_valid_academic_topic_line(first_line):
                        candidate = self.clean_concept_name(first_line)
                        if candidate and candidate not in extracted_concepts:
                            tp_type = self.classify_academic_topic_type(candidate, combined_text)
                            if tp_type in ["ACADEMIC_CONCEPT", "SUBCONCEPT"]:
                                extracted_concepts.append(candidate)

            # Fallback to cleaned section title if valid
            sec_clean = self.clean_concept_name(sec_title)
            if self.is_valid_academic_topic_line(sec_clean) and self.classify_academic_topic_type(sec_clean, combined_text) in ["ACADEMIC_CONCEPT", "SUBCONCEPT"]:
                if sec_clean not in extracted_concepts:
                    extracted_concepts.insert(0, sec_clean)

            # Deduplicate & Filter
            valid_final_concepts = []
            for concept in extracted_concepts:
                c_norm = concept.lower().strip()
                if c_norm not in seen_titles and self.is_valid_academic_topic_line(concept):
                    seen_titles.add(c_norm)
                    valid_final_concepts.append(concept)

            if not valid_final_concepts:
                valid_final_concepts.append("Core Syllabus & Academic Concepts")

            for sub_name in valid_final_concepts[:10]:
                topics_list.append({
                    "topic_id": f"top_{topic_counter}",
                    "title": sub_name,
                    "section": self.clean_concept_name(sec_title) or "Core Syllabus",
                    "pages": sec_pages,
                    "chunk_ids": sec_chunk_ids,
                    "text_summary": combined_text[:400]
                })
                topic_counter += 1

        logger.info(f"Built Structure-Aware Topic Map: {len(sections_dict)} sections, {len(topics_list)} valid academic topics.")
        return {
            "sections": {k: len(v) for k, v in sections_dict.items()},
            "topics": topics_list,
            "total_topics": len(topics_list)
        }

    def allocate_question_slots(self, topic_map: Dict[str, Any], requested_count: int) -> List[Dict[str, Any]]:
        """
        Allocates question slots across available valid academic topics.
        Ensures topic and chunk diversity across question slots.
        """
        topics = topic_map.get("topics", [])
        if not topics:
            topics = [{
                "topic_id": "top_1",
                "title": "Core Academic Topic",
                "section": "Core Syllabus",
                "pages": [1],
                "chunk_ids": [],
                "text_summary": ""
            }]

        # Prioritize topics with distinct primary chunk_ids
        selected_topics = []
        seen_primary_chunks = set()

        for t in topics:
            primary_chunk = t.get("chunk_ids", [None])[0] if t.get("chunk_ids") else None
            if primary_chunk and primary_chunk not in seen_primary_chunks:
                seen_primary_chunks.add(primary_chunk)
                selected_topics.append(t)

        # Fill remaining slots from unused topics if needed
        if len(selected_topics) < requested_count:
            for t in topics:
                if t not in selected_topics:
                    selected_topics.append(t)
                if len(selected_topics) >= requested_count:
                    break

        if not selected_topics:
            selected_topics = topics

        slots = []
        for i in range(requested_count):
            t = selected_topics[i % len(selected_topics)]
            diff_level = "Easy" if i % 3 == 0 else ("Medium" if i % 3 == 1 else "Hard")

            slots.append({
                "slot_index": i + 1,
                "topic_id": t["topic_id"],
                "topic_title": t["title"],
                "section": t["section"],
                "pages": t["pages"],
                "chunk_ids": t["chunk_ids"],
                "target_difficulty": diff_level
            })

        return slots

topic_mapper = DocumentTopicMapper()
