import re
import json
import uuid
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from app.models.question_gen import (
    VivaQuestionSchema,
    RubricCriterion,
    BloomTaxonomy,
    QuestionStatus,
    GenerateQuestionsRequest
)
from app.services.knowledge_service import knowledge_service
from app.services.vector_store import vector_store
from app.services.topic_mapper import topic_mapper
from app.services.question_verifier import question_verifier
from app.services.llm_service import llm_service

logger = logging.getLogger("vivabot.services.question_generator")

class QuestionGeneratorEngine:
    """
    AutoViva Redesigned Evidence-First RAG Question Generation Engine.
    Architecture:
    1. Document-scoped ChromaDB retrieval (`where={"document_id": doc_id}`).
    2. Two-Stage Structure-Aware Academic Topic Map Normalization (filters out DOC 1, 9/20, author names, fragments like "or a word").
    3. Coherent Evidence Window Retrieval before generation.
    4. Step 1: LLM Question Generation from evidence (`generate_viva_question_from_evidence`).
    5. Step 2: Separate LLM Ideal Answer Generation (`generate_ideal_answer_from_evidence`).
    6. Step 3: Validation Gate & LLM-as-a-Judge semantic grounding check.
    7. ZERO Deterministic Template Fabrication.
    8. Regeneration Loop (Max 3 retries per topic slot using alternate chunks).
    9. Rich Provenance Storage & Faculty Review Lifecycle (`FACULTY_REVIEW`).
    """
    def __init__(self, max_retries_per_slot: int = 2):
        self.max_retries_per_slot = max_retries_per_slot
        self.draft_questions: Dict[str, Any] = {}
        self.approved_question_bank: Dict[str, Any] = {}
        self.generation_logs: List[Dict[str, Any]] = []

    def _build_coherent_evidence_window(
        self,
        primary_chunk: Dict[str, Any],
        doc_chunks: List[Dict[str, Any]],
        window_size: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Builds a coherent 2-3 chunk evidence window centered around primary_chunk.
        Rules:
        - Must preserve document_id isolation (only chunks with same document_id).
        - Prefers adjacent chunks in doc_chunks sequence (same document).
        - Prefers chunks with matching section_title / topic.
        - Avoids duplicate chunks.
        """
        if not doc_chunks:
            return [primary_chunk]

        target_doc_id = primary_chunk.get("document_id") or primary_chunk.get("metadata", {}).get("document_id")
        primary_chunk_id = primary_chunk.get("chunk_id")
        primary_section = primary_chunk.get("section_title") or primary_chunk.get("metadata", {}).get("section_title")

        filtered_doc_chunks = doc_chunks
        if target_doc_id:
            same_doc = [c for c in doc_chunks if (c.get("document_id") or c.get("metadata", {}).get("document_id")) == target_doc_id]
            if same_doc:
                filtered_doc_chunks = same_doc

        primary_idx = -1
        for idx, c in enumerate(filtered_doc_chunks):
            if c.get("chunk_id") == primary_chunk_id:
                primary_idx = idx
                break

        if primary_idx == -1:
            return [primary_chunk]

        window_indices = [primary_idx]

        if primary_idx > 0:
            prev_chunk = filtered_doc_chunks[primary_idx - 1]
            prev_sec = prev_chunk.get("section_title") or prev_chunk.get("metadata", {}).get("section_title")
            if not primary_section or not prev_sec or prev_sec == primary_section:
                window_indices.insert(0, primary_idx - 1)

        if primary_idx < len(filtered_doc_chunks) - 1:
            next_chunk = filtered_doc_chunks[primary_idx + 1]
            next_sec = next_chunk.get("section_title") or next_chunk.get("metadata", {}).get("section_title")
            if not primary_section or not next_sec or next_sec == primary_section:
                window_indices.append(primary_idx + 1)

        window_chunks = [filtered_doc_chunks[i] for i in window_indices]

        seen_ids = set()
        result_chunks = []
        for c in window_chunks:
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                result_chunks.append(c)

        return result_chunks if result_chunks else [primary_chunk]

    def generate_document_grounded_questions(
        self,
        document_id: Optional[str] = None,
        viva_id: Optional[str] = None,
        subject: str = "Academic Syllabus",
        topic: str = "Core Topic",
        requested_count: int = 3
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        llm_service.reset_call_stats()

        print("\n" + "=" * 95)
        print("AUTOVIVA OPTIMIZED EVIDENCE-FIRST RAG QUESTION GENERATION PIPELINE")
        print(f"Document ID: '{document_id}' | Viva ID: '{viva_id}' | Subject: '{subject}' | Topic: '{topic}'")
        print(f"LLM Provider: {llm_service.provider} | Model: {llm_service.model}")
        print("=" * 95)

        # 1. Fetch document chunks strictly scoped to document_id
        doc_chunks = []
        if document_id:
            doc_chunks = vector_store.get_document_chunks(document_id)
        if not doc_chunks and viva_id:
            search_check = knowledge_service.search_knowledge_base(
                query=f"{subject} {topic}",
                top_k=20,
                viva_id=viva_id
            )
            doc_chunks = search_check.get("results", [])

        if not doc_chunks:
            search_check = knowledge_service.search_knowledge_base(
                query=f"{subject} {topic} core fundamentals concepts",
                top_k=20,
                subject=subject
            )
            doc_chunks = search_check.get("results", [])

        if not doc_chunks:
            err_msg = "Insufficient relevant evidence found in the uploaded document. Please ensure the syllabus document contains readable academic text."
            logger.error(f"[ZERO CHUNKS ERROR] {err_msg}")
            print(f"\n[PIPELINE ABORTED]: {err_msg}\n")
            return {
                "status": "INSUFFICIENT_RETRIEVAL_EVIDENCE",
                "error_code": "INSUFFICIENT_RETRIEVAL_EVIDENCE",
                "message": err_msg,
                "generated_questions": [],
                "verified_count": 0,
                "llm_telemetry": llm_service.get_call_stats()
            }

        # 2. Build Stage 1 + Stage 2 Topic & Section Map
        doc_topic_map = topic_mapper.build_topic_map(doc_chunks)
        print(f"[TOPIC MAP]: Found {doc_topic_map['total_topics']} valid academic topics across {len(doc_topic_map['sections'])} sections.")

        # 3. Allocate Question Slots
        question_slots = topic_mapper.allocate_question_slots(doc_topic_map, requested_count)

        verified_questions: List[Dict[str, Any]] = []
        rejected_log: List[Dict[str, Any]] = []
        accepted_question_texts: List[str] = []

        # Coverage Tracking
        used_chunk_ids: set = set()
        used_topics: set = set()
        used_sections: set = set()

        total_session_attempts = 0
        max_session_attempts = max(25, requested_count * 4)  # Bounded Budget: max(25, 4x count)

        # 4. Generate, Synthesize, and Validate per Slot
        for slot in question_slots:
            if total_session_attempts >= max_session_attempts:
                logger.warning(f"[SESSION BUDGET REACHED] Reached max candidate attempts budget ({max_session_attempts}). Halting further generation.")
                break

            slot_idx = slot["slot_index"]
            slot_topic = slot["topic_title"]
            slot_section = slot["section"]
            target_diff = slot["target_difficulty"]

            slot_success = False

            # Retrieve evidence chunks matching topic substantive terms
            stop_words = {"academic", "syllabus", "unit", "chapter", "section", "module", "part", "notes", "lecture", "overview", "introduction"}
            topic_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", slot_topic) if w.lower() not in stop_words]

            retrieval_res = knowledge_service.search_knowledge_base(
                query=f"{slot_section} {slot_topic} definition mechanism principle",
                top_k=8,
                document_id=document_id,
                viva_id=viva_id,
                subject=subject
            )
            retrieved_candidates = retrieval_res.get("results", []) or doc_chunks

            # Strictly prioritize chunks containing topic substantive words
            if topic_words:
                matched_chunks = [
                    c for c in retrieved_candidates
                    if any(tw in c.get("text", "").lower() for tw in topic_words)
                ]
                if not matched_chunks:
                    matched_chunks = [
                        c for c in doc_chunks
                        if any(tw in c.get("text", "").lower() for tw in topic_words)
                    ]
                if matched_chunks:
                    retrieved_candidates = matched_chunks

            # Sort candidates so unused chunks are evaluated first
            unused_cand_list = [c for c in retrieved_candidates if c.get("chunk_id") not in used_chunk_ids]
            ordered_candidates = unused_cand_list if unused_cand_list else retrieved_candidates

            # Attempt Loop (Max 2 retries per primary slot)
            for attempt in range(1, self.max_retries_per_slot + 1):
                if total_session_attempts >= max_session_attempts:
                    break

                total_session_attempts += 1
                chunk_candidate = ordered_candidates[(attempt - 1) % len(ordered_candidates)]
                evidence_chunks = self._build_coherent_evidence_window(chunk_candidate, doc_chunks)

                retrieval_score = chunk_candidate.get("similarity_score", 0.85)
                primary_page = chunk_candidate.get("page_number", slot.get("pages", [1])[0])
                primary_chunk_id = chunk_candidate.get("chunk_id", f"chunk_{slot_idx}_{attempt}")
                filename_source = chunk_candidate.get("filename") or chunk_candidate.get("source_file") or "Uploaded Document"

                logger.info(f"[SLOT {slot_idx} ATTEMPT {attempt} | SESSION CALL #{total_session_attempts}] Querying evidence chunk '{primary_chunk_id}' for topic '{slot_topic}'...")

                # Step 6: LLM Question + Answer Generation (Single Call)
                synth_res = llm_service.generate_viva_question_from_evidence(
                    evidence_chunks=evidence_chunks,
                    topic_title=slot_topic,
                    section_title=slot_section,
                    target_difficulty=target_diff,
                    existing_questions=accepted_question_texts,
                    attempt=attempt
                )

                if synth_res.get("status") == "ERROR":
                    if synth_res.get("error_code") == "LLM_GENERATION_FAILED":
                        err_msg = synth_res.get("message", "LLM API generation failed.")
                        logger.error(f"[LLM GENERATION FAILED] {err_msg}")
                        return {
                            "status": "LLM_GENERATION_FAILED",
                            "message": err_msg,
                            "generated_questions": [],
                            "verified_count": 0,
                            "rejected_log": rejected_log,
                            "llm_telemetry": llm_service.get_call_stats()
                        }
                    
                    rej_reason = f"LLM returned error status: {synth_res.get('error_code', 'ERROR')}"
                    logger.warning(f"  [DISCARDING CHUNK {primary_chunk_id}]: {rej_reason}")
                    rejected_log.append({
                        "slot": slot_idx,
                        "attempt": attempt,
                        "chunk_id": primary_chunk_id,
                        "reason": rej_reason
                    })
                    continue

                q_text = synth_res.get("question", "")
                ideal_ans = synth_res.get("ideal_answer", "")
                options = synth_res.get("options", {})
                correct_ans = synth_res.get("correct_answer", "A")
                source_quote = synth_res.get("source_quote", "")
                bloom = synth_res.get("bloom_level", "Understand")
                rubric = synth_res.get("rubric", [])
                keywords = synth_res.get("expected_keywords", [])
                llm_model = synth_res.get("model", llm_service.model)

                # Step 8: Multi-Stage Validation Gate
                verif_res = question_verifier.verify_question_candidate(
                    question_text=q_text,
                    ideal_answer=ideal_ans,
                    evidence_chunks=evidence_chunks,
                    topic_title=slot_topic,
                    existing_questions=accepted_question_texts,
                    source_quote=source_quote,
                    options=options if options else None,
                    correct_answer=correct_ans
                )

                if verif_res["valid"]:
                    q_id = f"vq_{uuid.uuid4().hex[:8]}"
                    q_obj = {
                        "question_id": q_id,
                        "document_id": document_id or "",
                        "viva_id": viva_id or "",
                        "filename": filename_source,
                        "subject": subject,
                        "topic": slot_topic,
                        "section": slot_section,
                        "difficulty": target_diff,
                        "blooms_level": bloom,
                        "question": q_text,
                        "question_text": q_text,
                        "options": options,
                        "correct_answer": correct_ans,
                        "source_quote": source_quote,
                        "ideal_answer": ideal_ans,
                        "evaluation_rubric": rubric,
                        "rubric": rubric,
                        "total_marks": 10.0,
                        "marks": 10.0,
                        "expected_keywords": keywords,
                        "source_page": f"Page {primary_page}",
                        "source_section": slot_section,
                        "source_chunk_ids": [primary_chunk_id],
                        "source_chunk": primary_chunk_id,
                        "source_chunks": [f"Page {primary_page} ({slot_section})"],
                        "reference_source": f"Page {primary_page} · {slot_topic}",
                        "confidence": round(retrieval_score, 4),
                        "llm_model": llm_model,
                        "validation_status": "VERIFIED",
                        "validation_report": verif_res,
                        "status": QuestionStatus.FACULTY_REVIEW.value
                    }

                    verified_questions.append(q_obj)
                    accepted_question_texts.append(q_text)
                    used_chunk_ids.add(primary_chunk_id)
                    used_topics.add(slot_topic.lower())
                    used_sections.add(slot_section.lower())
                    slot_success = True
                    print(f"  [VERIFIED SLOT {slot_idx}] '{q_text}' (Page {primary_page}, Chunk: {primary_chunk_id})")
                    break
                else:
                    rej_entry = {
                        "slot": slot_idx,
                        "attempt": attempt,
                        "chunk_id": primary_chunk_id,
                        "candidate": q_text,
                        "reason": verif_res["reason"]
                    }
                    rejected_log.append(rej_entry)
                    print(f"  [REJECTED SLOT {slot_idx} ATTEMPT {attempt}]: {verif_res['reason']}")

            # Alternate Unassigned Topic Search (Single Attempt if Primary Slot Failed)
            if not slot_success and total_session_attempts < max_session_attempts:
                unused_topics = [
                    t for t in doc_topic_map.get("topics", [])
                    if t["title"].lower() not in used_topics and t["title"].lower() != slot_topic.lower()
                ]
                
                if unused_topics:
                    alt_topic_info = unused_topics[0]
                    alt_topic = alt_topic_info["title"]
                    alt_section = alt_topic_info["section"]
                    logger.info(f"[SLOT {slot_idx} ALT TOPIC] Attempting alternate topic '{alt_topic}'...")
                    
                    retrieval_res = knowledge_service.search_knowledge_base(
                        query=f"{alt_section} {alt_topic} definition mechanism principle",
                        top_k=8,
                        document_id=document_id,
                        viva_id=viva_id,
                        subject=subject
                    )
                    alt_candidates = retrieval_res.get("results", []) or doc_chunks
                    unused_alt_cands = [c for c in alt_candidates if c.get("chunk_id") not in used_chunk_ids]
                    chunk_candidate = unused_alt_cands[0] if unused_alt_cands else alt_candidates[0]
                    evidence_chunks = self._build_coherent_evidence_window(chunk_candidate, doc_chunks)
                    
                    primary_page = chunk_candidate.get("page_number", 1)
                    primary_chunk_id = chunk_candidate.get("chunk_id", f"chunk_{slot_idx}_alt")
                    filename_source = chunk_candidate.get("filename") or chunk_candidate.get("source_file") or "Uploaded Document"
                    
                    total_session_attempts += 1
                    synth_res = llm_service.generate_viva_question_from_evidence(
                        evidence_chunks=evidence_chunks,
                        topic_title=alt_topic,
                        section_title=alt_section,
                        target_difficulty=target_diff,
                        existing_questions=accepted_question_texts,
                        attempt=1
                    )
                    
                    if synth_res.get("status") == "SUCCESS":
                        q_text = synth_res.get("question", "")
                        ideal_ans = synth_res.get("ideal_answer", "")
                        
                        verif_res = question_verifier.verify_question_candidate(
                            question_text=q_text,
                            ideal_answer=ideal_ans,
                            evidence_chunks=evidence_chunks,
                            topic_title=alt_topic,
                            existing_questions=accepted_question_texts,
                            source_quote=synth_res.get("source_quote", ""),
                            options=synth_res.get("options"),
                            correct_answer=synth_res.get("correct_answer", "A")
                        )
                        
                        if verif_res["valid"]:
                            q_id = f"vq_{uuid.uuid4().hex[:8]}"
                            q_obj = {
                                "question_id": q_id,
                                "document_id": document_id or "",
                                "viva_id": viva_id or "",
                                "filename": filename_source,
                                "subject": subject,
                                "topic": alt_topic,
                                "section": alt_section,
                                "difficulty": target_diff,
                                "blooms_level": synth_res.get("bloom_level", "Understand"),
                                "question": q_text,
                                "question_text": q_text,
                                "options": synth_res.get("options", {}),
                                "correct_answer": synth_res.get("correct_answer", "A"),
                                "source_quote": synth_res.get("source_quote", ""),
                                "ideal_answer": ideal_ans,
                                "evaluation_rubric": synth_res.get("rubric", []),
                                "rubric": synth_res.get("rubric", []),
                                "total_marks": 10.0,
                                "marks": 10.0,
                                "expected_keywords": [alt_topic],
                                "source_page": f"Page {primary_page}",
                                "source_section": alt_section,
                                "source_chunk_ids": [primary_chunk_id],
                                "source_chunk": primary_chunk_id,
                                "source_chunks": [f"Page {primary_page} ({alt_section})"],
                                "reference_source": f"Page {primary_page} · {alt_topic}",
                                "confidence": 0.95,
                                "llm_model": synth_res.get("model", llm_service.model),
                                "validation_status": "VERIFIED",
                                "validation_report": verif_res,
                                "status": QuestionStatus.FACULTY_REVIEW.value
                            }
                            verified_questions.append(q_obj)
                            accepted_question_texts.append(q_text)
                            used_chunk_ids.add(primary_chunk_id)
                            used_topics.add(alt_topic.lower())
                            used_sections.add(alt_section.lower())
                            slot_success = True
                            print(f"  [VERIFIED SLOT {slot_idx} ALT] '{q_text}' (Page {primary_page}, Chunk: {primary_chunk_id})")
                        else:
                            rejected_log.append({
                                "slot": slot_idx,
                                "attempt": 1,
                                "chunk_id": primary_chunk_id,
                                "candidate": q_text,
                                "reason": f"Alt Topic '{alt_topic}' rejected: {verif_res['reason']}"
                            })

            if not slot_success:
                logger.warning(f"[SLOT UNFULFILLED] Slot {slot_idx} ({slot_topic}) could not be fulfilled. ZERO synthetic fallback added.")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        telemetry = llm_service.get_call_stats()

        print("\n" + "=" * 95)
        print(f"QUESTION GENERATION COMPLETED: {len(verified_questions)} / {requested_count} Questions Staged in {elapsed_ms} ms ({elapsed_ms/1000:.1f} s).")
        print(f"LLM Telemetry: Total Calls={telemetry['total_calls']} | Avg Call Latency={telemetry.get('avg_latency_ms', 0)} ms | Rejections={len(rejected_log)}")
        print("=" * 95 + "\n")

        return {
            "status": "SUCCESS",
            "document_id": document_id,
            "viva_id": viva_id,
            "total_requested": requested_count,
            "verified_count": len(verified_questions),
            "generated_questions": verified_questions,
            "rejected_log": rejected_log,
            "topic_map": doc_topic_map,
            "latency_ms": elapsed_ms,
            "llm_telemetry": telemetry
        }

    def generate_questions(
        self,
        req: Optional[Any] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: str = "balanced",
        count: int = 3,
        document_id: Optional[str] = None,
        viva_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Wrapper compatibility method."""
        if req is not None and hasattr(req, "subject"):
            subject = req.subject
            topic = getattr(req, "topic", topic)
            difficulty = getattr(req, "difficulty", difficulty)
            count = getattr(req, "question_count", count)
            document_id = getattr(req, "document_id", document_id)
            viva_id = getattr(req, "viva_id", viva_id)

        return self.generate_document_grounded_questions(
            document_id=document_id,
            viva_id=viva_id,
            subject=subject or "Academic Syllabus",
            topic=topic or "Core Topic",
            requested_count=count
        )

question_generator_engine = QuestionGeneratorEngine()
