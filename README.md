# AutoViva — Evidence-Driven AI Viva Examination Platform

AutoViva is an explainable, evidence-grounded AI-assisted oral examination platform for higher education. It enables faculty members to upload real academic syllabi (PDF, DOCX, PPTX, TXT), automatically generate document-grounded viva questions using a locally hosted LLM (`qwen2.5:3b`), and conduct oral examinations for students with automated 3-module answer evaluation, speech-to-text transcription, and supplementary facial telemetry.

---

## 1. Architecture & System Overview

```
+-----------------------------------------------------------------------------------+
|                                 AUTOVIVA PLATFORM                                 |
+-----------------------------------------------------------------------------------+
|  Faculty Interface (React Vite)            |  Student Interface (React Vite)      |
|  - Viva Creation & PDF Upload              |  - Published Viva Session Discovery  |
|  - Evidence-Grounded Question Generation   |  - Sequential Question Navigation    |
|  - Question Review / Edit / Publish        |  - Microphone Audio Recording (STT)  |
|  - Student Evaluation & Audit Review       |  - 120s Question Timer & Results     |
+--------------------------------------------+--------------------------------------+
                                      |
                                      v
+-----------------------------------------------------------------------------------+
|                               FASTAPI BACKEND API                                 |
+-----------------------------------------------------------------------------------+
|  [Document Processor]   | Extract PDF/DOCX/PPTX/TXT text & structure             |
|  [Vector Store]         | ChromaDB + BGE-small-en-v1.5 embeddings               |
|  [Question Generator]   | qwen2.5:3b via local Ollama engine                   |
|  [Verification Gate]    | Document-grounded claim & evidence entailment filter  |
|  [STT Speech Engine]    | OpenAI Whisper Speech-to-Text service                |
|  [3-Module Evaluation]  | Explainable 3-stage rubric answer evaluator           |
|  [Faculty Audit Review] | Version 1 AI vs Version 2 Faculty Overrides & Audits |
+-----------------------------------------------------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+----------------------------------+             +----------------------------------+
|            CHROMADB              |             |             MONGODB              |
| Document-Scoped Chunks Vector DB |             | Users, Viva Sessions, & Audits   |
+----------------------------------+             +----------------------------------+
```

---

## 2. Core Technology Stack

- **Backend Framework**: Python 3.13 + FastAPI + Uvicorn
- **Frontend Framework**: React 18 + Vite + Tailwind CSS + Lucide Icons
- **Local LLM Engine**: Ollama running `qwen2.5:3b`
- **Embedding Model**: `BAAI/bge-small-en-v1.5` (sentence-transformers)
- **Vector Database**: ChromaDB (document-scoped chunk retrieval)
- **Primary Database**: MongoDB (`viva_sessions`, user authentication, audit logs)
- **Speech-to-Text**: OpenAI Whisper STT API / local PyTorch speech transcriber
- **Security & Auth**: PyJWT + Passlib (Bcrypt password hashing) + Role-Based Access Control

---

## 3. Evidence-First RAG Pipeline

1. **Multi-Format Document Processing**:
   - Accepts PDF, DOCX, PPTX, and TXT files.
   - Extracts structured headers, sections, and body text.
   - Rejects empty, garbled, or scanned image-only documents.
2. **Structure-Aware Chunking**:
   - Chunks text logically with section hierarchy preservation.
   - Generates unique `chunk_id` and tracks exact page provenance.
3. **Document-Scoped Vector Retrieval**:
   - Embeds text chunks using `BGE-small-en-v1.5`.
   - Stores chunks in ChromaDB with metadata filter `{"document_id": doc_id}`.
   - Queries are strictly isolated to the uploaded document to prevent cross-document contamination.

---

## 4. Question Generation & Verification Pipeline

1. **Evidence Window Assembly**:
   - Retrieves coherent, contiguous context windows from ChromaDB.
2. **LLM Question Generation (`qwen2.5:3b`)**:
   - Generates viva questions directly from retrieved evidence excerpts.
   - Eliminates generic fallback templates (e.g., no "core definition and key mechanism" generic patterns).
3. **Ideal Answer & Rubric Synthesis**:
   - Generates benchmark ideal answers and point-by-point evaluation rubrics grounded strictly in document evidence.
4. **Strict Quality & Grounding Gates**:
   - Filters out metadata headers (course codes, author names, syllabus footers).
   - Verifies evidence entailment: rejects unsupported causal or modal words (`required`, `necessary`, `benefit`) unless supported by evidence.
   - Validates question evidence sufficiency before acceptance.

---

## 5. 3-Module Answer Evaluation Engine

The 3-module explainable evaluation engine separates AI classification from numerical scoring and explainable feedback:

```
[Student Answer + Rubric + Ideal Answer]
                   |
                   v
   +-------------------------------+
   |  MODULE 1: CLASSIFICATION    |  --> LLM classifies each rubric criterion as:
   |  (Explainable LLM Engine)     |      SUPPORTED, PARTIALLY_SUPPORTED,
   +-------------------------------+      NOT_MENTIONED, or CONTRADICTED
                   |
                   v
   +-------------------------------+
   |  MODULE 2: DETERMINISTIC SCORING|  --> Standalone math engine applying multiplier:
   |  (No LLM - Pure Math)         |      - SUPPORTED: 1.0 (100% marks)
   +-------------------------------+      - PARTIALLY_SUPPORTED: 0.60 - 0.90
                   |                      - NOT_MENTIONED / CONTRADICTED: 0.0
                   v                      - Confidence < 0.55: REVIEW_REQUIRED (0.0)
   +-------------------------------+
   |  MODULE 3: FEEDBACK GENERATOR |  --> Verifies verbatim evidence quotes from transcript,
   |  (Verbatim Quote Verification)|      generates strengths, improvements, & summary.
   +-------------------------------+
```

---

## 6. Facial Telemetry (Non-Marking Supplementary Telemetry)

- **Purely Supplementary**: WebRTC facial attention and expression telemetry runs client-side to provide faculty with supplementary context (e.g., student focus percentage).
- **ZERO Marks Contribution**: The evaluation engine derives 100% of marks strictly from text rubric criteria. Facial telemetry contributes **0.0 marks**.
- **Fault-Tolerant Execution**: If the camera is disabled, ungranted, or unavailable, the student viva examination continues without interruption.

---

## 7. Faculty & Student Workflows

### Faculty Workflow:
1. **Login & Register**: Faculty authentication via `/api/auth/login`.
2. **Create Viva Session**: Define subject, course code, topic, question count, and time limit (`POST /api/viva/create`).
3. **Upload Syllabus PDF**: Upload document to index into ChromaDB (`POST /api/viva/upload-document`).
4. **Generate Grounded Questions**: Trigger `qwen2.5:3b` grounded question generation (`POST /api/viva/{viva_id}/generate-questions`).
5. **Review & Publish**: Edit, approve, or reject generated questions (`POST /api/viva/{viva_id}/review-question`), then publish (`POST /api/viva/{viva_id}/publish`).
6. **Audit & Override**: View student submission evaluations (`GET /api/evaluation/all`) and override scores with audit history logging.

### Student Workflow:
1. **Login & Browse**: Access active published viva sessions (`GET /api/viva/published`).
2. **Start Examination**: Receive active approved questions with 120s timer per question (`GET /api/viva/active-questions`).
3. **Record Oral Response**: Speak into microphone; audio is transcribed via STT (`POST /api/viva/transcribe`).
4. **Submit & Next**: Submit answer payload to 3-module evaluation pipeline (`POST /api/evaluation/submit`); progress sequentially to the next question.
5. **View Results**: Receive score, criterion breakdown, strengths, and actionable feedback.

---

## 8. Local Setup & Execution Guide

### Prerequisites:
- Python 3.10+
- Node.js 18+
- Ollama installed with model `qwen2.5:3b` pulled (`ollama pull qwen2.5:3b`)
- MongoDB running locally or accessible via URI string

### Step 1: Start Ollama Model
```bash
ollama serve
# In a separate terminal:
ollama run qwen2.5:3b
```

### Step 2: Start FastAPI Backend Server
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
pip install -r requirements.txt

# Start Backend:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Step 3: Start React Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 9. Verification & Audit Scripts

AutoViva includes automated end-to-end and audit validation scripts:

```bash
# Run 22-Step E2E Faculty-to-Student Smoke Test:
python -u backend/scripts/run_e2e_faculty_student_smoke_test.py

# Run System Audit & Edge Case Validation Suite:
python -u backend/scripts/run_system_audit_validation.py
```
