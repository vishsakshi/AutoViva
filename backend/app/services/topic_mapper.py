import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("vivabot.services.topic_mapper")

class DocumentTopic:
    def __init__(self, topic_id: str, title: str, section: str, page_numbers: List[int], chunk_ids: List[str], text_samples: List[str]):
        self.topic_id = topic_id
        self.title = title
        self.section = section
        self.page_numbers = page_numbers
        self.chunk_ids = chunk_ids
        self.text_samples = text_samples

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "section": self.section,
            "page_numbers": self.page_numbers,
            "chunk_ids": self.chunk_ids,
            "sample_count": len(self.text_samples)
        }

class DocumentTopicMapper:
    """
    Topic & Section Map Engine for AutoViva.
    Analyzes document chunks, discovers major academic topics, sections, and units,
    and maps them to balanced question distribution slots.
    """

    def clean_concept_name(self, raw_name: str) -> str:
        name = re.sub(r"^(unit|chapter|topic|section|module|part|\d+)\s*[:\.\-]?\s*", "", raw_name, flags=re.IGNORECASE).strip()
        name = re.sub(r"^\d+[\.:\-]\s*", "", name).strip()
        name = re.sub(r"\s+", " ", name)
        name = name.rstrip(".:,- ")
        if len(name) > 60:
            name = name[:60].strip() + "..."
        return name

    def build_topic_map(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts structured topics and sections from document chunks.
        """
        if not chunks:
            return {"sections": {}, "topics": [], "total_topics": 0}

        sections_dict: Dict[str, List[Dict[str, Any]]] = {}
        for c in chunks:
            sec = c.get("section_title") or c.get("metadata", {}).get("section_title") or "General Core"
            if sec not in sections_dict:
                sections_dict[sec] = []
            sections_dict[sec].append(c)

        topics_list: List[Dict[str, Any]] = []
        topic_counter = 1

        for sec_title, sec_chunks in sections_dict.items():
            # Extract distinctive concepts within this section
            sec_pages = list(set([c.get("page_number", c.get("metadata", {}).get("page_number", 1)) for c in sec_chunks]))
            sec_chunk_ids = [c.get("chunk_id") for c in sec_chunks]
            combined_text = "\n".join([c.get("text", "") for c in sec_chunks])

            # Look for sub-topics in lines or sentences
            lines = [l.strip() for l in combined_text.splitlines() if len(l.strip()) > 15]
            found_subtopics = []

            for l in lines:
                m = re.match(r"^(\d+\.\d+|Topic\s*\d+|[A-Z\s]{4,30}:?)\s*[:\.\-]?\s*(.+)$", l)
                if m:
                    sub_title = self.clean_concept_name(l)
                    if sub_title and sub_title not in found_subtopics and len(sub_title) > 4:
                        found_subtopics.append(sub_title)

            if not found_subtopics:
                # Use first line or section title
                main_title = self.clean_concept_name(lines[0]) if lines else self.clean_concept_name(sec_title)
                found_subtopics = [main_title]

            for sub_name in found_subtopics[:3]:  # Up to 3 per section
                topics_list.append({
                    "topic_id": f"top_{topic_counter}",
                    "title": sub_name,
                    "section": sec_title,
                    "pages": sec_pages,
                    "chunk_ids": sec_chunk_ids,
                    "text_summary": combined_text[:300]
                })
                topic_counter += 1

        logger.info(f"Built Topic Map: {len(sections_dict)} sections, {len(topics_list)} distinct topics.")
        return {
            "sections": {k: len(v) for k, v in sections_dict.items()},
            "topics": topics_list,
            "total_topics": len(topics_list)
        }

    def allocate_question_slots(self, topic_map: Dict[str, Any], requested_count: int) -> List[Dict[str, Any]]:
        """
        Distributes requested questions across available document topics evenly.
        Assigns balanced cognitive difficulty levels (Easy, Medium, Hard).
        """
        topics = topic_map.get("topics", [])
        if not topics:
            topics = [{
                "topic_id": "top_1",
                "title": "Core Academic Topic",
                "section": "Overview",
                "pages": [1],
                "chunk_ids": [],
                "text_summary": ""
            }]

        slots = []
        for i in range(requested_count):
            t = topics[i % len(topics)]
            diff_level = "Easy" if i % 3 == 0 else ("Medium" if i % 3 == 1 else "Hard")
            bloom_level = "Understand" if diff_level == "Easy" else ("Analyze" if diff_level == "Medium" else "Evaluate")

            slots.append({
                "slot_index": i + 1,
                "topic_id": t["topic_id"],
                "topic_title": t["title"],
                "section": t["section"],
                "pages": t["pages"],
                "chunk_ids": t["chunk_ids"],
                "difficulty": diff_level,
                "blooms_level": bloom_level
            })

        return slots

topic_mapper = DocumentTopicMapper()
