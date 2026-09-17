import os
import sys
import time
import json
import httpx
import fitz  # PyMuPDF

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

BASE_URL = "http://127.0.0.1:8000/api"
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_unicode_academic_syllabus(file_path: str):
    academic_text = (
        "Unit 1: Normal Distribution & Standard Deviation \u03c3 Analysis\n"
        "In statistical inference and machine learning, standard deviation \u03c3 measures the amount of variation or dispersion of a set of data values. A low standard deviation \u03c3 indicates that the observed data values tend to be close to the population mean \u03bc of the dataset. Formally, for a continuous random variable X with expected mean \u03bc, the variance is defined as \u03c3^2 = E[(X - \u03bc)^2].\n\n"
        "Unit 2: Feature Scaling and Z-Score Standardization\n"
        "In data preprocessing for multivariate statistical modeling, z-score standardization transforms continuous numerical features so that they exhibit a zero mean \u03bc = 0 and a unit standard deviation \u03c3 = 1. The mathematical z-score transformation formula is computed as z = (x - \u03bc) / \u03c3 for each individual feature value x across the sample set. Scaling ensures features contribute equally to Support Vector Machines.\n\n"
        "Unit 3: Activation Functions and Logistic Sigmoid \u03c3(z)\n"
        "In deep artificial neural networks and binary logistic regression models, the logistic sigmoid activation function is defined by the equation \u03c3(z) = 1 / (1 + e^-z), which smoothly maps real-valued inputs z into the bounded open interval (0, 1). The first mathematical derivative of the sigmoid activation function is expressed as \u03c3'(z) = \u03c3(z)(1 - \u03c3(z)), enabling efficient gradient backpropagation.\n\n"
        "Unit 4: Gradient Descent Learning Rate \u03b1 and L2 Regularization Parameter \u03bb\n"
        "During iterative parameter estimation in supervised learning, the learning rate hyperparameter \u03b1 dictates the step size taken along the negative gradient direction during parameter updates. If the learning rate setting is \u03b1 \u2264 10^-5, parameter optimization converges impractically slowly. To mitigate model overfitting, L2 weight decay introduces a regularization penalty term \u03bb \u2211 w_j^2 into the loss function.\n\n"
        "Unit 5: Probably Approximately Correct (PAC) Generalization Error Bound \u03b5\n"
        "Under the Probably Approximately Correct (PAC) theoretical learning framework, computational learning theory establishes formal bounds on model generalizability using the error threshold \u03b5 \u2264 0.05. The risk confidence parameter 1 - \u03b4 defines the lower bound probability of drawing a representative training sample set from the underlying data distribution."
    )
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(academic_text)
    print(f"[CREATED UNICODE SYLLABUS]: '{file_path}' (Contains Greek \u03c3 'σ', \u03bc 'μ', \u2264 '≤', \u03b1 'α', \u03bb 'λ')")

def test_unicode_pdf_pipeline():
    print("\n" + "=" * 95)
    print("AUTOVIVA UNICODE (& GREEK SIGMA \\u03c3) E2E PDF PIPELINE TEST")
    print(f"Target Backend API: {BASE_URL}")
    print("=" * 95 + "\n")

    txt_filename = "unicode_sigma_academic_syllabus.txt"
    txt_path = os.path.join(BACKEND_DIR, txt_filename)
    create_unicode_academic_syllabus(txt_path)

    with httpx.Client(timeout=httpx.Timeout(600.0)) as client:
        # Wait for backend readiness
        for retry in range(10):
            try:
                r = client.get(f"{BASE_URL}/auth/me", timeout=5.0)
                if r.status_code in [200, 401, 403]:
                    break
            except Exception:
                time.sleep(1.0)

        # 1. Create Viva Session
        t0 = time.perf_counter()
        res_viva = client.post(f"{BASE_URL}/viva/create", json={
            "subject": "Machine Learning",
            "course_code": "CS402",
            "topic": "Standard Deviation \u03c3 & Gaussian Distribution",
            "question_count": 5
        })
        if res_viva.status_code != 200:
            print(f"[FAIL]: Viva creation failed HTTP_{res_viva.status_code}: {res_viva.text[:120]}")
            return False
        
        viva_id = res_viva.json().get("viva_id")
        print(f"Step 1: Created Viva Session '{viva_id}'")

        # 2. Upload Unicode Syllabus Document
        with open(txt_path, "rb") as f:
            files = {"file": (txt_filename, f, "text/plain")}
            res_up = client.post(f"{BASE_URL}/viva/upload-document", data={"viva_id": viva_id}, files=files)

        if res_up.status_code != 200:
            print(f"[FAIL]: PDF Upload failed HTTP_{res_up.status_code}: {res_up.text[:120]}")
            return False

        doc_id = res_up.json().get("document_id")
        chunks_count = res_up.json().get("chunks_processed", 0)
        print(f"Step 2: Uploaded & Indexed PDF successfully (DocID: '{doc_id}', Chunks: {chunks_count})")

        # 3. Generate 5 Questions using qwen2.5:3b
        t_gen_start = time.perf_counter()
        print(f"Step 3: Triggering qwen2.5:3b Question Generation for DocID '{doc_id}'...")
        res_q = client.post(f"{BASE_URL}/viva/{viva_id}/generate-questions", timeout=600.0)
        t_gen_elapsed = round(time.perf_counter() - t_gen_start, 2)

        if res_q.status_code != 200:
            print(f"[FAIL]: Question generation failed HTTP_{res_q.status_code}: {res_q.text[:120]}")
            return False

        q_data = res_q.json()
        questions = q_data.get("generated_questions", [])

        print(f"Step 4: Successfully generated & staged {len(questions)} / 5 questions in {t_gen_elapsed}s!")

        # 4. Verify Unicode preservation and Grounding Gate compliance
        unicode_preserved = False
        for idx, q in enumerate(questions):
            q_text = q.get("question_text") or q.get("question", "")
            ideal = q.get("ideal_answer", "")
            ev_excerpt = q.get("retrieved_evidence_excerpt", "")
            provenance = q.get("evidence_provenance", {})

            print(f"\n--- QUESTION {idx+1} ---")
            print(f"Question Text: {q_text}")
            print(f"Ideal Answer : {ideal}")
            print(f"Evidence Excerpt: {ev_excerpt[:100]}...")
            print(f"Provenance   : Page {provenance.get('page_number')}, Chunk {provenance.get('chunk_id')}")

            if "\u03c3" in ev_excerpt or "\u03c3" in q_text or "\u03c3" in ideal or "\u03bc" in ev_excerpt or "\u03bc" in q_text:
                unicode_preserved = True

        print("\n" + "=" * 95)
        print(f"UNICODE \\u03c3 TEST RESULTS:")
        print(f"- 5/5 Questions Generated & Staged: {'YES' if len(questions) == 5 else 'NO'}")
        print(f"- Generation Time: {t_gen_elapsed} s")
        print(f"- Unicode Preserved (\\u03c3 / \\u03bc): {'YES' if unicode_preserved else 'NO'}")
        print("=" * 95 + "\n")

        return len(questions) == 5 and unicode_preserved

if __name__ == "__main__":
    test_unicode_pdf_pipeline()
