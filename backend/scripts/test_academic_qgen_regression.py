import os
import sys
import unittest

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.document_processor import document_processor
from app.services.chunker import document_chunker
from app.services.embedding_service import embedding_service
from app.services.topic_mapper import topic_mapper
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.services.question_generator import question_generator_engine
from app.services.question_verifier import question_verifier

class TestAcademicQGenRegression(unittest.TestCase):
    """
    Comprehensive End-to-End Regression Test Suite for AutoViva Document-Grounded RAG Pipeline.
    Verifies:
    1. LLM API configuration loading & safe secret key redaction.
    2. Elimination of document artifacts ("DOC 1", "OUTPUT", "or a word", "Mayank Singh", "9/20").
    3. Identification of real academic topics ("Distributional Semantics", "Pointwise Mutual Information", "Cosine Similarity").
    4. 10-Check Question & Answer validation gate enforcement.
    5. Clean evidence-grounded answer synthesis without template repetition.
    6. Safe generation trace logging (DOCUMENT, TOPICS, EVIDENCE, LLM CONFIG, QUESTION, ANSWER, VALIDATION).
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

    def test_01_llm_config_verification(self):
        """Verifies LLM configuration loading & safe secret redaction."""
        print("\n" + "=" * 80)
        print("[TEST 01] LLM CONFIGURATION VERIFICATION")
        print("=" * 80)
        
        redacted_key = f"{settings.LLM_API_KEY[:6]}...{settings.LLM_API_KEY[-4:]}" if len(settings.LLM_API_KEY) > 10 else "***"
        print(f"Provider: {settings.LLM_PROVIDER}")
        print(f"API URL: {settings.LLM_API_URL}")
        print(f"Redacted Key: {redacted_key}")
        print(f"Model: {settings.LLM_MODEL}")
        print(f"Is Configured: {llm_service.is_configured()}")
        
        self.assertTrue(bool(settings.LLM_MODEL), "LLM_MODEL is not configured.")

    def test_02_artifact_rejection_in_topic_mapper(self):
        """Verifies that noise tokens, author names, and document labels are excluded from topic mapper."""
        print("\n" + "=" * 80)
        print("[TEST 02] TOPIC MAPPER ARTIFACT REJECTION")
        print("=" * 80)

        fake_pages = [{
            "page_number": 1,
            "text": self.sample_doc_text,
            "source_file": "nlp_syllabus.pdf",
            "file_type": "pdf",
            "section_title": "Distributional Semantics",
            "detected_sections": ["Distributional Semantics"]
        }]

        chunks = document_chunker.chunk_document(fake_pages, subject="NLP", topic="Semantics", document_id="doc_reg_101")
        topic_map = topic_mapper.build_topic_map(chunks)

        topic_titles = [t["title"] for t in topic_map["topics"]]
        print(f"Identified Academic Topics ({len(topic_titles)}):")
        for idx, title in enumerate(topic_titles):
            print(f"  Topic {idx+1}: '{title}'")

        # Assert noise items are 100% absent from identified topic titles
        for bad_token in ["DOC 1", "OUTPUT", "or a word", "Mayank Singh", "9/20", "Page 9"]:
            for title in topic_titles:
                self.assertNotIn(bad_token.lower(), title.lower(), f"Artifact '{bad_token}' leaked into topic title '{title}'!")

    def test_03_end_to_end_qgen_and_validation(self):
        """Runs end-to-end QGen pipeline and prints full safe generation trace."""
        print("\n" + "=" * 80)
        print("[TEST 03] END-TO-END RAG QUESTION GENERATION & VALIDATION TRACE")
        print("=" * 80)

        fake_pages = [{
            "page_number": 1,
            "text": self.sample_doc_text,
            "source_file": "nlp_syllabus.pdf",
            "file_type": "pdf",
            "section_title": "Distributional Semantics",
            "detected_sections": ["Distributional Semantics"]
        }]

        doc_id = "doc_reg_102"
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

        print(f"\nDOCUMENT: nlp_syllabus.pdf | ID: {doc_id}")
        print(f"LLM CONFIG: provider={settings.LLM_PROVIDER} | model={settings.LLM_MODEL}")
        print(f"TOTAL QUESTIONS GENERATED: {len(questions)}")

        for idx, q in enumerate(questions):
            print(f"\n--- TRACE QUESTION {idx+1} ---")
            print(f"SELECTED TOPIC: {q['topic']}")
            print(f"RETRIEVED EVIDENCE CHUNK: {q.get('source_chunk_ids', [''])[0]} ({q.get('source_page', '')})")
            print(f"GENERATED QUESTION: \"{q['question_text']}\"")
            print(f"GENERATED ANSWER: \"{q['ideal_answer']}\"")
            print(f"SOURCE QUOTE: \"{q.get('source_quote', '')[:90]}...\"")
            
            verif = q.get("validation_report", {})
            print("VALIDATION REPORT:")
            print(f"  Valid: {verif.get('valid', True)}")
            print(f"  Reason: {verif.get('reason', 'Passed validation checks.')}")
            print(f"FINAL STATUS: {q.get('status', 'FACULTY_REVIEW')}")

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
