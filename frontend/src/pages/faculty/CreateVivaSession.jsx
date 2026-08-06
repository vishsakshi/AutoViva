import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Upload, FileText, CheckCircle2, XCircle, Edit3, ArrowLeft, Layers, Send, Loader2 } from 'lucide-react';

export default function CreateVivaSession() {
  const navigate = useNavigate();

  // Step Tracker: 1: METADATA | 2: UPLOAD | 3: REVIEW | 4: PUBLISHED
  const [step, setStep] = useState(1);

  // STEP 1: Viva Metadata
  const [subject, setSubject] = useState('Computer Networks');
  const [courseCode, setCourseCode] = useState('CS301');
  const [topic, setTopic] = useState('IP Addressing, NAT & NAPT');
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(3);
  const [durationMinutes, setDurationMinutes] = useState(15);
  const [batch, setBatch] = useState('Batch 2026');

  const [vivaRecord, setVivaRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [toast, setToast] = useState(null);

  // STEP 1: Create Viva Metadata Record
  const handleCreateMetadata = async (e) => {
    e.preventDefault();
    setLoading(true);
    setToast(null);

    try {
      const res = await fetch('/api/viva/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject,
          course_code: courseCode,
          topic,
          difficulty,
          question_count: parseInt(questionCount, 10),
          duration_minutes: parseInt(durationMinutes, 10),
          batch
        })
      });

      if (res.ok) {
        const data = await res.json();
        setVivaRecord(data);
        setStep(2);
        setToast({ type: 'success', text: `Viva session ${data.viva_id} created. Now upload academic material.` });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Error creating viva metadata.' });
    } finally {
      setLoading(false);
    }
  };

  // STEP 2: Upload File & Chunk in Knowledge Base
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !vivaRecord) return;
    setLoading(true);
    setToast(null);

    const formData = new FormData();
    formData.append('viva_id', vivaRecord.viva_id);
    formData.append('file', file);

    try {
      const res = await fetch('/api/viva/upload-document', {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setUploadedFiles(prev => [...prev, data.filename]);
        setToast({ type: 'success', text: `Uploaded and indexed ${data.filename} (${data.chunks_processed} chunks in Knowledge Base).` });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Error processing document.' });
    } finally {
      setLoading(false);
    }
  };

  // STEP 3: Generate Questions from Uploaded Context
  const handleGenerateQuestions = async () => {
    if (!vivaRecord) return;
    setLoading(true);
    setToast(null);

    try {
      const res = await fetch(`/api/viva/${vivaRecord.viva_id}/generate-questions`, {
        method: 'POST'
      });

      if (res.ok) {
        const data = await res.json();
        setVivaRecord(data);
        setStep(3);
        setToast({ type: 'success', text: `Generated ${data.generated_questions.length} questions grounded in syllabus context.` });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Error generating questions.' });
    } finally {
      setLoading(false);
    }
  };

  // STEP 4: Review Question (Approve / Reject)
  const handleReviewQuestion = async (qId, action) => {
    if (!vivaRecord) return;
    const formData = new FormData();
    formData.append('question_id', qId);
    formData.append('action', action);

    try {
      const res = await fetch(`/api/viva/${vivaRecord.viva_id}/review-question`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setVivaRecord(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // STEP 5: Publish Viva
  const handlePublishViva = async () => {
    if (!vivaRecord) return;
    setLoading(true);

    try {
      const res = await fetch(`/api/viva/${vivaRecord.viva_id}/publish`, {
        method: 'POST'
      });

      if (res.ok) {
        const data = await res.json();
        setVivaRecord(data);
        setStep(4);
        setToast({ type: 'success', text: `Viva Session Published! Students can now access and take this examination.` });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Error publishing viva.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200/80">
        <div>
          <Link to="/faculty/dashboard" className="text-xs font-semibold text-[#0F766E] hover:underline flex items-center gap-1 mb-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Faculty Workspace
          </Link>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Faculty Viva Creation Pipeline
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Upload syllabus documents, process Knowledge Base embeddings, and publish viva sessions for student examination
          </p>
        </div>
      </div>

      {toast && (
        <div className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between ${
          toast.type === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'
        }`}>
          <span>{toast.text}</span>
          <button onClick={() => setToast(null)} className="text-xs underline">Dismiss</button>
        </div>
      )}

      {/* Pipeline Progress Indicator */}
      <div className="grid grid-cols-4 gap-4 text-xs font-bold">
        <div className={`p-3.5 rounded-2xl border text-center ${step >= 1 ? 'bg-[#0F766E] text-white border-[#0F766E]' : 'bg-white text-slate-400 border-slate-200'}`}>
          1. Viva Metadata
        </div>
        <div className={`p-3.5 rounded-2xl border text-center ${step >= 2 ? 'bg-[#0F766E] text-white border-[#0F766E]' : 'bg-white text-slate-400 border-slate-200'}`}>
          2. Syllabus Upload
        </div>
        <div className={`p-3.5 rounded-2xl border text-center ${step >= 3 ? 'bg-[#0F766E] text-white border-[#0F766E]' : 'bg-white text-slate-400 border-slate-200'}`}>
          3. Question Review
        </div>
        <div className={`p-3.5 rounded-2xl border text-center ${step >= 4 ? 'bg-[#0F766E] text-white border-[#0F766E]' : 'bg-white text-slate-400 border-slate-200'}`}>
          4. Published Viva
        </div>
      </div>

      {/* STEP 1: METADATA FORM */}
      {step === 1 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 max-w-2xl mx-auto space-y-6">
          <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">
            Step 1: Configure Viva Parameters
          </h2>

          <form onSubmit={handleCreateMetadata} className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Subject Name</label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Course Code</label>
                <input
                  type="text"
                  required
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium"
                />
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Topic / Chapter</label>
              <input
                type="text"
                required
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Difficulty</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Questions</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={questionCount}
                  onChange={(e) => setQuestionCount(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Duration (Min)</label>
                <input
                  type="number"
                  min="5"
                  max="60"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium"
                />
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Student Batch</label>
              <input
                type="text"
                value={batch}
                onChange={(e) => setBatch(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Viva & Proceed to Upload →'}
            </button>
          </form>
        </div>
      )}

      {/* STEP 2: DOCUMENT UPLOAD & KNOWLEDGE BASE */}
      {step === 2 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 max-w-2xl mx-auto space-y-6">
          <h2 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">
            Step 2: Upload Syllabus & Academic Notes
          </h2>

          <div className="space-y-4 text-xs">
            <p className="text-slate-600">
              Upload PDF, PPT, DOCX, or TXT syllabus material. Text is chunked with PyMuPDF, embedded with <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-[11px]">BAAI/bge-small-en-v1.5</code>, and stored in the ChromaDB Knowledge Base.
            </p>

            <div className="border-2 border-dashed border-slate-300 rounded-2xl p-8 text-center space-y-3 hover:border-[#0F766E] transition-colors">
              <Upload className="w-8 h-8 text-[#0F766E] mx-auto" />
              <p className="font-semibold text-slate-800">Select Academic Material File</p>
              <input
                type="file"
                accept=".pdf,.ppt,.pptx,.docx,.txt"
                onChange={handleFileUpload}
                className="hidden"
                id="viva-doc-input"
              />
              <label
                htmlFor="viva-doc-input"
                className="inline-block px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold rounded-xl cursor-pointer border border-slate-200"
              >
                Browse Files
              </label>
            </div>

            {uploadedFiles.length > 0 && (
              <div className="space-y-2">
                <span className="font-bold text-slate-800">Indexed Files in Knowledge Base:</span>
                {uploadedFiles.map((fn, idx) => (
                  <div key={idx} className="p-3 bg-[#F8FAFC] border border-slate-200 rounded-xl flex items-center gap-2 font-mono text-[11px] text-slate-700">
                    <FileText className="w-4 h-4 text-[#0F766E]" /> {fn} (Indexed)
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={handleGenerateQuestions}
              disabled={loading}
              className="w-full py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Generate Questions from Knowledge Base →
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: QUESTION REVIEW TABLE */}
      {step === 3 && vivaRecord && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 space-y-6">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">Step 3: Faculty Question Review Queue</h2>
              <p className="text-xs text-slate-500 mt-0.5">Approve, reject, or edit questions generated from syllabus knowledge base.</p>
            </div>
            <button
              onClick={handlePublishViva}
              disabled={loading || (vivaRecord.approved_questions.length === 0 && vivaRecord.generated_questions.length === 0)}
              className="px-6 py-2.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center gap-2"
            >
              Publish Viva Session to Students →
            </button>
          </div>

          <div className="space-y-4">
            {vivaRecord.generated_questions.map((q, idx) => {
              const isApproved = vivaRecord.approved_questions.some(aq => aq.question_id === q.question_id);
              return (
                <div key={q.question_id} className={`p-5 rounded-2xl border text-xs space-y-3 ${isApproved ? 'bg-emerald-50/60 border-emerald-300' : 'bg-[#F8FAFC] border-slate-200'}`}>
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-900 font-mono">Q{idx + 1} ({q.question_id})</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleReviewQuestion(q.question_id, 'APPROVE')}
                        className={`px-3 py-1 rounded-lg font-bold flex items-center gap-1 ${isApproved ? 'bg-emerald-700 text-white' : 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'}`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> {isApproved ? 'Approved' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleReviewQuestion(q.question_id, 'REJECT')}
                        className="px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-800 font-bold rounded-lg flex items-center gap-1"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>
                  </div>
                  <p className="font-bold text-slate-900 text-sm">"{q.question_text}"</p>
                  <p className="text-slate-600 text-xs">Ideal Answer: {q.ideal_answer}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* STEP 4: VIVA PUBLISHED */}
      {step === 4 && vivaRecord && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-12 text-center max-w-xl mx-auto space-y-5">
          <div className="w-14 h-14 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-extrabold text-slate-900">Viva Session Published!</h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            Viva Session <code className="bg-slate-100 px-2 py-1 rounded font-mono text-slate-900 font-bold">{vivaRecord.viva_id}</code> is now published and active on the Student Portal.
          </p>

          <div className="pt-2 flex justify-center gap-4 text-xs font-bold">
            <Link
              to="/student/dashboard"
              className="px-5 py-2.5 bg-[#0F766E] text-white rounded-xl shadow-md hover:bg-[#0D645D]"
            >
              View in Student Portal →
            </Link>
            <Link
              to="/faculty/dashboard"
              className="px-5 py-2.5 bg-slate-100 text-slate-800 border border-slate-200 rounded-xl hover:bg-slate-200"
            >
              Return to Faculty Workspace
            </Link>
          </div>
        </div>
      )}

    </div>
  );
}
