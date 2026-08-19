import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("vivabot.services.concept_extractor")

class ConceptExtractor:
    """
    Concept Extraction & Question Planning Engine for RAG VivaBot:
    Step 4: Extracts academic concepts, definitions, processes, and source metadata from retrieved chunks.
    Step 5: Constructs a Question Plan before LLM synthesis.
    """

    def extract_concepts_from_chunk(self, chunk_text: str, chunk_id: str, page_num: int) -> Dict[str, Any]:
        """
        Parses chunk text to extract primary concept title, definition, key terms, and candidate questions.
        """
        lines = [line.strip() for line in chunk_text.splitlines() if len(line.strip()) > 15]
        if not lines:
            lines = [chunk_text]

        # Extract concept title from heading or first line
        primary_line = lines[0]
        # Clean title of common prefixes
        concept_title = re.sub(r"^(topic|unit|chapter|section|\d+\.\d+)\s*[:\.\-]?\s*", "", primary_line, flags=re.IGNORECASE).strip()
        if len(concept_title) > 60:
            concept_title = concept_title[:60].strip() + "..."

        # Extract definition snippet
        definition_text = "\n".join(lines[:3]) if len(lines) >= 3 else chunk_text

        # Extract important terms (capitalized or highlighted phrases)
        terms = re.findall(r"\b[A-Z][a-zA-Z0-9\-\_]{2,}\b", chunk_text)
        unique_terms = list(set([t for t in terms if t.lower() not in ["the", "and", "for", "with", "this", "that", "unit", "topic", "page"]]))[:5]

        return {
            "chunk_id": chunk_id,
            "page_num": page_num,
            "concept": concept_title or "Academic Concept",
            "definition": definition_text,
            "important_terms": unique_terms,
            "source_ref": f"Page {page_num} (Chunk {chunk_id})"
        }

    def build_question_plan(self, retrieved_chunks: List[Dict[str, Any]], requested_count: int = 3) -> Dict[str, Any]:
        """
        Step 5 Question Planning:
        Constructs a structured question plan mapping concepts to Easy, Medium, and Hard viva question angles.
        """
        extracted_concepts = []
        planned_questions = []

        for idx, chunk in enumerate(retrieved_chunks):
            text = chunk.get("text", "")
            chunk_id = chunk.get("chunk_id", f"chunk_{idx+1}")
            page_num = chunk.get("page_num") or chunk.get("metadata", {}).get("page", idx + 1)
            
            c_meta = self.extract_concepts_from_chunk(text, chunk_id, page_num)
            extracted_concepts.append(c_meta)

        # Map to balanced paper plan (Easy, Medium, Hard)
        for i in range(requested_count):
            c_meta = extracted_concepts[i % len(extracted_concepts)] if extracted_concepts else {
                "concept": "Core Academic Principle",
                "definition": "Core technical principles.",
                "page_num": 1,
                "chunk_id": f"chunk_{i+1}",
                "source_ref": "Page 1"
            }

            diff_level = "Easy" if i % 3 == 0 else ("Medium" if i % 3 == 1 else "Hard")
            bloom_level = "Understand" if diff_level == "Easy" else ("Analyze" if diff_level == "Medium" else "Evaluate")

            # Formulate natural professor-level viva question angles
            concept_name = c_meta["concept"]

            if diff_level == "Easy":
                q_angle = f"What is {concept_name}? Explain the fundamental intuition and core principles behind it."
            elif diff_level == "Medium":
                q_angle = f"Describe the step-by-step process of constructing and applying {concept_name}. What key parameters or components are required?"
            else:
                q_angle = f"Critically evaluate {concept_name}. Compare its trade-offs, limitations, and practical applications against alternative approaches."

            planned_questions.append({
                "plan_id": f"plan_{i+1}",
                "concept": concept_name,
                "difficulty": diff_level,
                "blooms_level": bloom_level,
                "question_angle": q_angle,
                "chunk_id": c_meta["chunk_id"],
                "page_num": c_meta["page_num"],
                "definition": c_meta["definition"]
            })

        logger.info(f"Question Planner constructed plan for {len(planned_questions)} viva questions from {len(extracted_concepts)} extracted concepts.")
        return {
            "extracted_concepts": extracted_concepts,
            "planned_questions": planned_questions
        }

concept_extractor = ConceptExtractor()
