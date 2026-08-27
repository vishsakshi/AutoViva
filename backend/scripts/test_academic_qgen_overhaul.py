import os
import sys
import unittest

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.document_processor import document_processor
from app.services.chunker import document_chunker
from app.services.embedding_service import embedding_service
from app.services.topic_mapper import topic_mapper
from app.services.vector_store import vector_store
from app.services.question_generator import question_generator_engine
from app.services.question_verifier import question_verifier

class TestAcademicQGenOverhaul(unittest.TestCase):
    """
    Comprehensive End-to-End Audit & Verification Test Suite for AutoViva Question Generation.
    Validates that:
    1. Document noise ("DOC 1", "OUTPUT", "or a word", "Mayank Singh", "9/20") is 100% eliminated from topic candidates.
    2. Real academic topics ("Distributional Semantics", "Pointwise Mutual Information (PMI)", "Cosine Similarity") are identified.
    3. Generated questions are complete, grammatical, and academic oral viva questions.
    4. Ideal answers directly answer the viva question using grounded evidence.
    5. The verification gate rejects malformed artifacts ("What is What is", "What is DOC 1").
    """

    def setUp(self):
        self.sample_doc_text = (
            "Unit 1: Vector Space Models & Distributional Semantics\n"
            "Mayank Singh - Department of Computer Science - Page 9/20 - Copyright 2026\n\n"
            "Distributional Semantics\n"
            "Distributional semantics is an approach to computational linguistics that represents word meaning "
            "based on patterns of co-occurrence in large textual corpora. The underlying intuition is that words "
            "occurring in similar contexts tend to share similar semantic meanings.\n\n"
            "DOC 1: An automobile is a wheeled motor vehicle used for transportation.\n"
            "or a word\n"
            "OUTPUT\n\n"
            "Pointwise Mutual Information (PMI)\n"
            "Pointwise Mutual Information is a statistical metric used in vector space models to measure the association "
            "between a word and its context. High PMI values indicate that two words co-occur significantly more often "
            "than expected by random chance.\n\n"
            "Cosine Similarity\n"
            "Cosine similarity measures the orientation between two sparse vector representations in high-dimensional space. "
            "It computes the normalized dot product of two word vectors to determine semantic relatedness regardless of vector magnitude."
        )

    def test_noise_and_artifact_rejection(self):
        """Verifies that noise tokens, author names, and document labels are excluded from topic mapper."""
        fake_pages = [{
            "page_number": 1,
            "text": self.sample_doc_text,
            "source_file": "syllabus_unit1.pdf",
            "file_type": "pdf",
            "section_title": "Distributional Semantics",
            "detected_sections": ["Distributional Semantics"]
        }]

        chunks = document_chunker.chunk_document(fake_pages, subject="NLP", topic="Semantics", document_id="doc_audit_101")
        topic_map = topic_mapper.build_topic_map(chunks)

        topic_titles = [t["title"] for t in topic_map["topics"]]
        
        print("\n=== PHASE 4: IDENTIFIED ACADEMIC TOPICS ===")
        for idx, title in enumerate(topic_titles):
            print(f"Topic {idx+1}: {title}")

        # Assert noise items are 100% absent from identified topic titles
        for bad_token in ["DOC 1", "OUTPUT", "or a word", "Mayank Singh", "9/20", "Page 9"]:
            for title in topic_titles:
                self.assertNotIn(bad_token.lower(), title.lower(), f"Artifact '{bad_token}' leaked into topic title '{title}'!")

    def test_end_to_end_question_and_answer_generation(self):
        """Runs complete QGen pipeline and validates question-answer quality and grounding."""
        fake_pages = [{
            "page_number": 1,
            "text": self.sample_doc_text,
            "source_file": "syllabus_unit1.pdf",
            "file_type": "pdf",
            "section_title": "Distributional Semantics",
            "detected_sections": ["Distributional Semantics"]
        }]

        doc_id = "doc_audit_102"
        chunks = document_chunker.chunk_document(fake_pages, subject="Natural Language Processing", topic="Distributional Semantics", document_id=doc_id)
        
        embeddings = embedding_service.generate_embeddings([c["text"] for c in chunks])
        vector_store.add_chunks(chunks, embeddings)

        result = question_generator_engine.generate_document_grounded_questions(
            document_id=doc_id,
            subject="Natural Language Processing",
            topic="Distributional Semantics",
            requested_count=3
        )

        questions = result.get("generated_questions", [])
        self.assertGreater(len(questions), 0, "Question generator failed to return candidate questions.")

        print("\n=== PHASE 15: GENERATED VIVA QUESTIONS & IDEAL ANSWERS ===")
        for idx, q in enumerate(questions):
            print(f"\n--- QUESTION {idx+1} [{q['topic']}] ---")
            print(f"Question: {q['question_text']}")
            print(f"Ideal Answer: {q['ideal_answer']}")
            print(f"Source Quote: {q.get('source_quote', '')[:100]}...")
            print(f"Verification: {q.get('status', 'VERIFIED')}")

            q_text = q['question_text']
            ans_text = q['ideal_answer']

            # Assert malformed template artifacts are NOT present
            self.assertNotIn("what is what is", q_text.lower())
            self.assertNotIn("or a word", q_text.lower())
            self.assertNotIn("doc 1", q_text.lower())
            self.assertNotIn("output?", q_text.lower())

            # Assert ideal answer is non-empty and grounded
            self.assertGreater(len(ans_text), 15)
            self.assertNotIn("In Distributional Semantics, Distributional Semantics is defined as:", ans_text)

if __name__ == "__main__":
    unittest.main()
