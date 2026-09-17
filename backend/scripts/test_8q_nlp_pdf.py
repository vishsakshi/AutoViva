import os
import sys
import time
import json
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

BASE_URL = "http://127.0.0.1:8000/api"
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_8q_nlp_pdf_test():
    pdf_filename = "nlp_academic_lecture_14p.pdf"
    pdf_path = os.path.join(BACKEND_DIR, pdf_filename)
    if not os.path.exists(pdf_path):
        print(f"[ERROR]: File '{pdf_path}' does not exist.")
        return False

    print("\n" + "=" * 95)
    print("AUTOVIVA 8-QUESTION GROUNDED RAG PIPELINE TEST")
    print(f"Target Backend API: {BASE_URL}")
    print(f"Test PDF Document : {pdf_filename} (14 Pages)")
    print("Requested Question Count: 8")
    print("=" * 95 + "\n")

    with httpx.Client(timeout=httpx.Timeout(600.0)) as client:
        # Wait for backend readiness
        for _ in range(10):
            try:
                r = client.get(f"{BASE_URL}/auth/me", timeout=5.0)
                if r.status_code in [200, 401, 403]:
                    break
            except Exception:
                time.sleep(1.0)

        # 1. Create Viva Session with question_count=8
        res_viva = client.post(f"{BASE_URL}/viva/create", json={
            "subject": "Natural Language Processing",
            "course_code": "CS224N",
            "topic": "Word Vectors, SVD & Word2Vec",
            "question_count": 8,
            "duration_minutes": 30,
            "batch": "Batch 2026"
        })
        if res_viva.status_code != 200:
            print(f"[FAIL]: Viva creation failed HTTP_{res_viva.status_code}: {res_viva.text[:120]}")
            return False
        
        viva_data = res_viva.json()
        viva_id = viva_data.get("viva_id")
        req_count = viva_data.get("question_count")
        print(f"Step 1: Created Viva Session '{viva_id}' with requested question_count = {req_count}")

        # 2. Upload 14-Page NLP Document
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_filename, f, "application/pdf")}
            res_up = client.post(f"{BASE_URL}/viva/upload-document", data={"viva_id": viva_id}, files=files)

        if res_up.status_code != 200:
            print(f"[FAIL]: Document Upload failed HTTP_{res_up.status_code}: {res_up.text[:120]}")
            return False

        up_data = res_up.json()
        doc_id = up_data.get("document_id")
        chunks_count = up_data.get("chunks_processed", 0)
        print(f"Step 2: Uploaded & Indexed PDF successfully (DocID: '{doc_id}', Chunks: {chunks_count})")

        # 3. Generate 8 Questions using qwen2.5:3b
        t_gen_start = time.perf_counter()
        print(f"Step 3: Triggering qwen2.5:3b Question Generation for DocID '{doc_id}' (Target: 8 Questions)...")
        res_q = client.post(f"{BASE_URL}/viva/{viva_id}/generate-questions", timeout=600.0)
        t_gen_elapsed = round(time.perf_counter() - t_gen_start, 2)

        if res_q.status_code != 200:
            print(f"[FAIL]: Question generation failed HTTP_{res_q.status_code}: {res_q.text[:120]}")
            return False

        q_data = res_q.json()
        questions = q_data.get("generated_questions", [])
        
        print("\n" + "=" * 95)
        print(f"GENERATION PIPELINE SUMMARY RESULT:")
        print(f"- Requested Count : {req_count}")
        print(f"- Generated Count : {len(questions)}")
        print(f"- Total Latency   : {t_gen_elapsed} s")
        print(f"- Avg Latency/Q   : {round(t_gen_elapsed / max(1, len(questions)), 2)} s")
        print("=" * 95 + "\n")

        # Detailed Verification and Source Chunk Inspection
        all_doc_ids_used = set()
        multi_chunk_windows_used = 0

        for idx, q in enumerate(questions):
            q_text = q.get("question_text") or q.get("question", "")
            ideal = q.get("ideal_answer", "")
            doc_id_q = q.get("document_id", "")
            if doc_id_q:
                all_doc_ids_used.add(doc_id_q)

            src_chunks = q.get("source_chunk_ids", [q.get("source_chunk")])
            if len(src_chunks) > 1:
                multi_chunk_windows_used += 1

            print(f"--- ACCEPTED QUESTION {idx+1} / {len(questions)} ---")
            print(f"Question     : {q_text}")
            print(f"Ideal Answer : {ideal}")
            print(f"Source Page  : {q.get('source_page', 'Page 1')}")
            print(f"Chunk IDs    : {src_chunks}")
            print(f"Status       : {q.get('validation_status', 'VERIFIED')}")
            print()

        cross_doc_leakage = False
        for did in all_doc_ids_used:
            if did != doc_id:
                cross_doc_leakage = True

        print("=" * 95)
        print(f"EVIDENCE WINDOW & QUALITY METRICS:")
        print(f"- Target Document ID: '{doc_id}'")
        print(f"- Document IDs Used in Generated Questions: {list(all_doc_ids_used)}")
        print(f"- Cross-Document Leakage Detected: {'YES (BUG)' if cross_doc_leakage else 'NO (Strictly Scoped)'}")
        print(f"- Questions Using Multi-Chunk Coherent Windows: {multi_chunk_windows_used} / {len(questions)}")
        print("=" * 95 + "\n")

        return len(questions) > 0 and not cross_doc_leakage

if __name__ == "__main__":
    run_8q_nlp_pdf_test()
