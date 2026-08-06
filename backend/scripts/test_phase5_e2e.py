import time
import json
import tracemalloc
from typing import List, Dict, Any

from app.models.question_gen import GenerateQuestionsRequest

from app.models.evaluation_module import EvaluateAnswerRequest
from app.models.review_module import FacultyOverrideRequest, EvaluationStatus
from app.services.knowledge_service import knowledge_service
from app.services.question_generator import question_generator
from app.services.evaluation_review_service import evaluation_review_service

def run_phase5_e2e_demo():
    print("=" * 90)
    print("VIVABOT PHASE 5: COMPLETE SYSTEM INTEGRATION & END-TO-END PIPELINE VALIDATION")
    print("=" * 90)

    tracemalloc.start()
    pipeline_start_time = time.perf_counter()

    # --------------------------------------------------------------------------------
    # STEP 6: POPULATE DEMO DATA FOR 5 SUBJECTS
    # --------------------------------------------------------------------------------
    print("\n[STEP 6] POPULATING DEMO DATA FOR 5 SUBJECTS (DBMS, OS, CN, OOP, NLP)...")

    demo_subjects_data = {
        "DBMS": [
            ("Relational Database Management Systems & ACID Properties", 
             "A Relational Database Management System (RDBMS) stores data in structured tables with rows and columns. ACID properties guarantee database transactions reliably: Atomicity ensures all-or-nothing completion, Consistency maintains validity constraints, Isolation prevents concurrent transaction interference, and Durability ensures committed updates persist despite failures."),
            ("Indexing & B-Trees", 
             "B-Trees and B+ Trees are balanced search tree data structures used by database engines to speed up query retrieval. Secondary indexes allow log-time lookup of record locations.")
        ],
        "Operating Systems": [
            ("Process Management & Deadlocks", 
             "A process is an active program execution context containing PCB, program counter, and stack. Deadlocks occur when processes hold resources while waiting for others in a circular chain. Coffman conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait. Banker's Algorithm prevents deadlocks by evaluating safe states."),
            ("Virtual Memory & Paging", 
             "Virtual Memory abstracts physical RAM using fixed-size pages mapped to page frames via Page Tables. Translation Lookaside Buffers (TLB) cache recent translations to minimize memory access latency.")
        ],
        "Computer Networks": [
            ("IP Addressing, NAT & NAPT", 
             "Network Address Translation (NAT) maps private internal IPv4 addresses to public external IP addresses. NAPT (Port Address Translation) extends NAT by mapping unique transport port numbers alongside the public IP, allowing thousands of internal sockets to share a single public IP address. NAT also hides internal network topologies for security."),
            ("TCP 3-Way Handshake & Congestion Control", 
             "TCP establishes reliable connection via SYN, SYN-ACK, ACK. Congestion control algorithms like Slow Start, Congestion Avoidance, Fast Retransmit, and Fast Recovery adapt transmission windows to prevent network collapse.")
        ],
        "OOP": [
            ("Object-Oriented Design & Inheritance", 
             "Object-Oriented Programming (OOP) organizes software design around objects containing data fields and methods. Core pillars: Encapsulation hides state behind interfaces, Inheritance enables code reuse through class hierarchies, Polymorphism allows derived classes to override methods, and Abstraction exposes essential features."),
            ("Design Patterns & Interfaces", 
             "Interfaces define abstract contracts without implementation. Factory, Singleton, and Observer design patterns organize object instantiation and decoupling.")
        ],
        "NLP": [
            ("Natural Language Processing & Transformer Architecture", 
             "Transformers rely on multi-head self-attention mechanisms to compute contextual representations of tokens in parallel without recurrent connections. Positional encodings provide sequence order awareness. BERT and GPT models leverage pre-training on massive text corpora for downstream NLP tasks."),
            ("TF-IDF & Tokenization", 
             "Tokenization breaks text into subword units. Term Frequency-Inverse Document Frequency (TF-IDF) weights word importance relative to corpus document frequency.")
        ]
    }

    total_chunks = 0
    for subj, topics in demo_subjects_data.items():
        for topic_name, text in topics:
            c_id = f"chunk_{subj.lower().replace(' ', '_')}_{hash(topic_name) % 10000}"
            knowledge_service.vector_store.add_chunk(
                chunk_id=c_id,
                text=text,
                metadata={
                    "source_file": f"{subj.lower()}_syllabus.pdf",
                    "subject": subj,
                    "topic": topic_name,
                    "page_number": 1,
                    "chunk_id": c_id
                }
            )
            total_chunks += 1

    print(f"✅ Populated Knowledge Base with {total_chunks} academic chunks across 5 subjects.")

    # --------------------------------------------------------------------------------
    # STEP 1 & 3: END-TO-END DEMONSTRATION ON COMPUTER NETWORKS
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("EXECUTING END-TO-END DEMO: SUBJECT = COMPUTER NETWORKS")
    print("=" * 80)

    # 1. Knowledge Base Retrieval
    t0 = time.perf_counter()
    retrieved_chunks = knowledge_service.search_knowledge(
        query="Explain NAT, NAPT port mapping, and private vs public IP addressing",
        subject="Computer Networks",
        top_k=3
    )
    t_retrieval = round((time.perf_counter() - t0) * 1000, 2)
    print(f"\n1. Knowledge Base Retrieval Complete ({t_retrieval} ms): Retrieved {len(retrieved_chunks)} chunks.")

    # 2. Question Generation Engine
    t0 = time.perf_counter()
    gen_req = GenerateQuestionsRequest(
        subject="Computer Networks",
        topic="IP Addressing, NAT & NAPT",
        num_questions=1,
        difficulty="medium",
        bloom_level="Understand"
    )
    gen_result = question_generator.generate_questions(gen_req)
    t_gen = round((time.perf_counter() - t0) * 1000, 2)

    generated_q = gen_result["questions"][0]
    print(f"\n2. Question Generation Engine Complete ({t_gen} ms):")
    print(f"   Question ID: {generated_q['question_id']}")
    print(f"   Question Text: \"{generated_q['question_text']}\"")
    print(f"   Bloom Level: {generated_q['bloom_level']}")
    print(f"   Rubric Criteria Count: {len(generated_q['evaluation_rubric'])}")

    # 3. Faculty Approves Question
    question_generator.approve_question(generated_q["question_id"])
    print(f"\n3. Faculty Question Approval: Question '{generated_q['question_id']}' approved and moved to Question Bank.")

    # 4. Student Submits Viva Answer
    student_ans = "Private IPs are used inside local networks while public IPs are routed on the internet. NAPT uses port numbers for mapping connections. It also manages translation tables and hides internal IPs for security."
    print(f"\n4. Student Submits Viva Answer:")
    print(f"   \"{student_ans}\"")

    # 5. End-to-End Evaluation Pipeline Submission (Module 1 -> Module 2 -> Module 3 -> Staged PENDING_REVIEW)
    t0 = time.perf_counter()
    eval_req = EvaluateAnswerRequest(
        question_text=generated_q['question_text'],
        ideal_answer=generated_q['ideal_answer'],
        evaluation_rubric=generated_q['evaluation_rubric'],
        student_answer=student_ans,
        subject="Computer Networks",
        topic="IP Addressing, NAT & NAPT"
    )
    full_record = evaluation_review_service.submit_student_answer_pipeline(eval_req)
    t_eval = round((time.perf_counter() - t0) * 1000, 2)

    print(f"\n5. Evaluation Pipeline Complete ({t_eval} ms):")
    print(f"   Evaluation ID: {full_record.evaluation_id}")
    print(f"   Module 1 Status: {full_record.ai_version_v1.status}")
    print(f"   Module 2 Score: {full_record.ai_version_v1.evaluation_summary.final_score} / 10.0 ({full_record.ai_version_v1.evaluation_summary.percentage}%)")
    print(f"   Module 3 Evidence Validity: {full_record.ai_version_v1.evaluation_summary.evidence_validity_status}")
    print(f"   Current Status: {full_record.status} (Staged for Faculty Review)")

    # 6. Faculty Review & Score Override (Module 4)
    t0 = time.perf_counter()
    override_req = FacultyOverrideRequest(
        action="OVERRIDE",
        new_score=10.0,
        criterion_score_overrides={"c1": 3.0, "c2": 4.0, "c3": 3.0},
        faculty_comment="Excellent explanation. Full marks awarded after manual verification of NAPT table management.",
        reason_for_change="Upgraded score to 10.0 after faculty inspection of student answer topology."
    )
    final_record = evaluation_review_service.override_evaluation(full_record.evaluation_id, override_req)
    t_review = round((time.perf_counter() - t0) * 1000, 2)

    print(f"\n6. Faculty Review & Final Publication Complete ({t_review} ms):")
    print(f"   Final Status: {final_record.status}")
    print(f"   Current Version: v{final_record.current_version}")
    print(f"   AI Version 1 Score: {final_record.ai_version_v1.evaluation_summary.final_score} / 10.0")
    print(f"   Faculty Version 2 Published Score: {final_record.faculty_version_v2.evaluation_summary.final_score} / 10.0 (100.0%)")
    print(f"   Audit Log Entries Count: {len(final_record.audit_history)}")

    pipeline_total_ms = round((time.perf_counter() - pipeline_start_time) * 1000, 2)
    current_mem_mb, peak_mem_mb = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --------------------------------------------------------------------------------
    # STEP 5: PERFORMANCE MEASUREMENTS SUMMARY
    # --------------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5: VIVABOT SYSTEM PERFORMANCE BENCHMARKS")
    print("=" * 80)
    print(f"Retrieval Latency:           {t_retrieval} ms")
    print(f"Question Generation Latency: {t_gen} ms")
    print(f"Evaluation Pipeline Latency: {t_eval} ms")
    print(f"Faculty Review Latency:      {t_review} ms")
    print(f"Total End-to-End Latency:    {pipeline_total_ms} ms")
    print(f"Current Memory Usage:        {current_mem_mb / 1024 / 1024:.2f} MB")
    print(f"Peak Memory Allocation:      {peak_mem_mb / 1024 / 1024:.2f} MB")
    print("=" * 80)

if __name__ == "__main__":
    run_phase5_e2e_demo()
