import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sparkles, Upload, FileText, CheckCircle2, XCircle, Edit3, ArrowLeft, ArrowRight,
  Layers, Send, Loader2, RefreshCw, Trash2, Eye, FileCode, AlertCircle, Info, RotateCcw
} from 'lucide-react';

export default function CreateVivaSession() {
  const navigate = useNavigate();

  // Wizard Step State: 1: METADATA | 2: UPLOAD & KNOWLEDGE BASE | 3: QUESTION REVIEW | 4: PUBLISHED
  const [step, setStep] = useState(1);

  // STEP 1: Viva Metadata (Preserved across Step 1 <-> 2 <-> 3 <-> 4)
  const [subject, setSubject] = useState('Computer Networks');
  const [courseCode, setCourseCode] = useState('CS301');
  const [topic, setTopic] = useState('IP Addressing, NAT & NAPT');
  const [questionCount, setQuestionCount] = useState(3);
  const [durationMinutes, setDurationMinutes] = useState(15);
  const [batch, setBatch] = useState('Batch 2026');

  // Viva Record & Uploaded File Metadata List
  const [vivaRecord, setVivaRecord] = useState(null);
  const [uploadedFilesList, setUploadedFilesList] = useState([]); // List of { id, filename, size, upload_time, chunks, status }

  // Upload & Indexing Pipeline Progress States
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStageText, setCurrentStageText] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);

  // Modal & Edit State
  const [selectedFileModal, setSelectedFileModal] = useState(null);
  const [editingQuestionId, setEditingQuestionId] = useState(null);
  const [editedQuestionText, setEditedQuestionText] = useState('');

  // General Loading & Toast Notification
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // STEP 1: Create or Update Viva Metadata Record
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
          question_count: parseInt(questionCount, 10),
          duration_minutes: parseInt(durationMinutes, 10),
          batch
        })
      });

      const data = await res.json();

      if (res.ok) {
        setVivaRecord(prev => prev ? { ...prev, ...data } : data);
        setStep(2);
        setToast({ type: 'success', text: `Viva parameters configured. Now upload syllabus material for Knowledge Base indexing.` });
      } else {
        setToast({ type: 'error', text: data.detail || 'Failed to configure viva session parameters.' });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Server connection error while creating viva session.' });
    } finally {
      setLoading(false);
    }
  };

  // STEP 2: Process Document Upload with Live Indexing Progress Pipeline
  const processDocumentUpload = async (file) => {
    if (!file) return;

    // File Validation: Max 50 MB
    const maxSizeBytes = 50 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setToast({ type: 'error', text: `File size exceeds 50 MB limit. Selected file size: ${(file.size / (1024 * 1024)).toFixed(1)} MB.` });
      return;
    }

    if (!vivaRecord) {
      setToast({ type: 'error', text: 'Missing viva session record. Please configure Step 1 first.' });
      return;
    }

    setIsUploading(true);
    setUploadProgress(10);
    setCurrentStageText('Uploading file to server...');
    setToast(null);

    // Live Pipeline Stage Simulation for Smooth Progress UX
    const stageTimer1 = setTimeout(() => {
      setUploadProgress(35);
      setCurrentStageText('Extracting document structure (PyMuPDF / docx)...');
    }, 600);

    const stageTimer2 = setTimeout(() => {
      setUploadProgress(60);
      setCurrentStageText('Generating heading-aware text chunks...');
    }, 1400);

    const stageTimer3 = setTimeout(() => {
      setUploadProgress(82);
      setCurrentStageText('Creating BAAI/bge-small-en-v1.5 embeddings & indexing into ChromaDB...');
    }, 2200);

    const formData = new FormData();
    formData.append('viva_id', vivaRecord.viva_id);
    formData.append('file', file);

    try {
      const res = await fetch('/api/viva/upload-document', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);

      if (res.ok) {
        setUploadProgress(100);
        setCurrentStageText('Knowledge Base Ready');

        const newFileItem = {
          id: `file_${Date.now()}`,
          filename: data.filename,
          size: data.file_size || `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
          upload_time: data.upload_time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          chunks: data.chunks_processed || 12,
          status: 'Indexed'
        };

        setUploadedFilesList(prev => [...prev.filter(f => f.filename !== file.filename), newFileItem]);
        setToast({ type: 'success', text: `✔ ${data.filename} uploaded and indexed successfully into Knowledge Base.` });
      } else {
        setToast({ type: 'error', text: data.detail || `Upload failed for ${file.filename}.` });
      }
    } catch (err) {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);
      setToast({ type: 'error', text: `Document processing failed: ${err.message || 'Server connection error'}` });
    } finally {
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
        setCurrentStageText('');
      }, 500);
    }
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) processDocumentUpload(file);
    e.target.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processDocumentUpload(e.dataTransfer.files[0]);
    }
  };

  // Remove File from List
  const handleRemoveFile = (filename) => {
    setUploadedFilesList(prev => prev.filter(f => f.filename !== filename));
    setToast({ type: 'success', text: `Removed ${filename} from Knowledge Base index list.` });
  };

  // STEP 3: Generate Questions Grounded in Syllabus
  const handleGenerateQuestions = async () => {
    if (!vivaRecord) return;
    setLoading(true);
    setToast(null);

    try {
      const res = await fetch(`/api/viva/${vivaRecord.viva_id}/generate-questions`, {
        method: 'POST'
      });

      const data = await res.json();

      if (res.ok) {
        setVivaRecord(data);
        setStep(3);
        setToast({ type: 'success', text: `Generated ${data.generated_questions.length} questions grounded in syllabus context.` });
      } else {
        setToast({ type: 'error', text: data.detail || 'Failed to generate questions.' });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Server connection error during question generation.' });
    } finally {
      setLoading(false);
    }
  };

  // Review Question (Approve / Reject / Edit)
  const handleReviewQuestion = async (qId, action, customText = null) => {
    if (!vivaRecord) return;

    const formData = new FormData();
    formData.append('question_id', qId);
    formData.append('action', action);
    if (customText) {
      formData.append('edited_text', customText);
    }

    try {
      const res = await fetch(`/api/viva/${vivaRecord.viva_id}/review-question`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setVivaRecord(data);
        if (action === 'EDIT') setEditingQuestionId(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // STEP 4: Publish Viva Session
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
      } else {
        setToast({ type: 'error', text: 'Error publishing viva session.' });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Server connection error while publishing viva.' });
    } finally {
      setLoading(false);
    }
  };

  // Full Pipeline Reset
  const handleResetPipeline = () => {
    if (window.confirm('Are you sure you want to reset the wizard? All entered metadata, uploaded files, and generated questions will be cleared.')) {
      setStep(1);
      setVivaRecord(null);
      setUploadedFilesList([]);
      setToast(null);
    }
  };

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
      
      {/* Header Bar */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200/80">
        <div>
          <Link to="/faculty/dashboard" className="text-xs font-semibold text-[#0F766E] hover:underline flex items-center gap-1 mb-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Faculty Workspace
          </Link>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Faculty Viva Creation Pipeline
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Configure metadata, upload syllabus material into ChromaDB Knowledge Base, review grounded questions, and publish.
          </p>
        </div>

        {step > 1 && (
          <button
            type="button"
            onClick={handleResetPipeline}
            className="px-3.5 py-2 bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 font-bold text-xs rounded-xl border border-slate-200 transition-all flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset Form
          </button>
        )}
      </div>

      {/* Toast Alert */}
      {toast && (
        <div className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between shadow-xs ${
          toast.type === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'
        }`}>
          <div className="flex items-center gap-2">
            {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />}
            <span>{toast.text}</span>
          </div>
          <button onClick={() => setToast(null)} className="text-xs underline font-bold">Dismiss</button>
        </div>
      )}

      {/* 4-Step Interactive Wizard Bar */}
      <div className="grid grid-cols-4 gap-3 text-xs font-bold">
        {[
          { num: 1, title: '1. Viva Metadata' },
          { num: 2, title: '2. Syllabus Upload' },
          { num: 3, title: '3. Question Review' },
          { num: 4, title: '4. Published Viva' }
        ].map(item => (
          <button
            key={item.num}
            type="button"
            onClick={() => {
              if (item.num === 1) setStep(1);
              if (item.num === 2 && vivaRecord) setStep(2);
              if (item.num === 3 && vivaRecord && uploadedFilesList.length > 0) setStep(3);
              if (item.num === 4 && vivaRecord && vivaRecord.status === 'PUBLISHED') setStep(4);
            }}
            disabled={
              (item.num === 2 && !vivaRecord) ||
              (item.num === 3 && (!vivaRecord || uploadedFilesList.length === 0)) ||
              (item.num === 4 && (!vivaRecord || vivaRecord.status !== 'PUBLISHED'))
            }
            className={`py-3.5 px-4 rounded-2xl border text-center transition-all flex items-center justify-center gap-2 ${
              step === item.num
                ? 'bg-[#0F766E] text-white border-[#0F766E] shadow-sm'
                : step > item.num
                ? 'bg-emerald-50 text-[#0F766E] border-emerald-200 hover:bg-emerald-100'
                : 'bg-white text-slate-400 border-slate-200 opacity-60 cursor-not-allowed'
            }`}
          >
            <span>{item.title}</span>
            {step > item.num && <CheckCircle2 className="w-3.5 h-3.5 text-[#0F766E]" />}
          </button>
        ))}
      </div>

      {/* ========================================================================= */}
      {/* STEP 1: VIVA METADATA CONFIGURATION */}
      {/* ========================================================================= */}
      {step === 1 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 max-w-2xl mx-auto space-y-6">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900">
              Step 1: Configure Viva Parameters
            </h2>
            <span className="text-xs font-semibold text-slate-500">Step 1 of 4</span>
          </div>

          <form onSubmit={handleCreateMetadata} className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Subject Name</label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Computer Networks"
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:border-[#0F766E] focus:outline-none transition-all"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Course Code</label>
                <input
                  type="text"
                  required
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                  placeholder="e.g. CS301"
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:border-[#0F766E] focus:outline-none transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Topic / Unit Name</label>
              <input
                type="text"
                required
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. IP Addressing, NAT & NAPT"
                className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:border-[#0F766E] focus:outline-none transition-all"
              />
            </div>

            {/* Balanced Paper Auto Distribution Banner (No Manual Difficulty Selector) */}
            <div className="p-3.5 rounded-2xl bg-teal-50/70 border border-teal-200/80 text-teal-900 flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 text-[#0F766E] shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-bold text-xs block text-[#0F766E]">Automatic Balanced Question Paper</span>
                <p className="text-[11px] text-teal-800 leading-relaxed">
                  Questions are generated automatically with a balanced academic difficulty mix (~30% Easy, ~40% Medium, ~30% Hard) grounded in uploaded syllabus material. Manual difficulty selection is disabled.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Question Count</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  required
                  value={questionCount}
                  onChange={(e) => setQuestionCount(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:border-[#0F766E] focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Duration (Minutes)</label>
                <input
                  type="number"
                  min="5"
                  max="60"
                  required
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:border-[#0F766E] focus:outline-none transition-all"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Student Batch</label>
                <input
                  type="text"
                  required
                  value={batch}
                  onChange={(e) => setBatch(e.target.value)}
                  placeholder="e.g. Batch 2026"
                  className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 font-medium focus:bg-white focus:border-[#0F766E] focus:outline-none transition-all"
                />
              </div>
            </div>

            <div className="pt-2 flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Save & Proceed to Syllabus Upload <ArrowRight className="w-4 h-4" /></>}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 2: SYLLABUS UPLOAD & LIVE INDEXING PIPELINE */}
      {/* ========================================================================= */}
      {step === 2 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 max-w-3xl mx-auto space-y-6">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Step 2: Upload Syllabus & Knowledge Base Indexing
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Upload lecture slides, textbooks, or syllabus documents to build the ChromaDB vector context.
              </p>
            </div>
            <span className="text-xs font-semibold text-slate-500">Step 2 of 4</span>
          </div>

          <div className="space-y-5 text-xs">
            
            {/* Drag & Drop Upload Card */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-3xl p-8 text-center space-y-4 transition-all ${
                isDragOver
                  ? 'border-[#0F766E] bg-teal-50/50 scale-[1.01]'
                  : 'border-slate-300 bg-[#F8FAFC] hover:border-[#0F766E]/70 hover:bg-slate-50'
              }`}
            >
              <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 text-[#0F766E] flex items-center justify-center mx-auto shadow-xs">
                <Upload className="w-7 h-7" />
              </div>

              <div>
                <p className="font-extrabold text-sm text-slate-800">
                  Drag and drop syllabus file here
                </p>
                <p className="text-xs text-slate-500 mt-1 font-medium">
                  Supports <span className="font-bold text-slate-700">PDF, PPT, PPTX, DOCX, TXT</span> (Max 50 MB)
                </p>
              </div>

              <input
                type="file"
                accept=".pdf,.ppt,.pptx,.docx,.txt"
                onChange={handleFileInputChange}
                disabled={isUploading}
                className="hidden"
                id="viva-doc-upload-input"
              />
              <label
                htmlFor="viva-doc-upload-input"
                className={`inline-flex items-center gap-2 px-5 py-2.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold rounded-xl cursor-pointer shadow-md shadow-[#0F766E]/20 transition-all ${
                  isUploading ? 'opacity-50 pointer-events-none' : ''
                }`}
              >
                <Upload className="w-4 h-4" /> Browse Files
              </label>

              {/* Supported Format Pills */}
              <div className="flex justify-center gap-2 pt-2">
                {['PDF', 'PPT', 'PPTX', 'DOCX', 'TXT'].map(ext => (
                  <span key={ext} className="px-2.5 py-1 bg-white border border-slate-200 text-slate-600 font-mono text-[10px] font-bold rounded-lg shadow-2xs">
                    .{ext.toLowerCase()}
                  </span>
                ))}
              </div>
            </div>

            {/* Live Upload & Indexing Pipeline Progress Bar */}
            {isUploading && (
              <div className="p-4 rounded-2xl bg-teal-50/80 border border-teal-200 text-teal-900 space-y-2.5 animate-pulse">
                <div className="flex justify-between items-center font-bold text-xs">
                  <span className="flex items-center gap-2 text-[#0F766E]">
                    <Loader2 className="w-4 h-4 animate-spin" /> {currentStageText}
                  </span>
                  <span className="font-mono text-[#0F766E]">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-teal-200/70 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-[#0F766E] h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Uploaded Files Management List */}
            {uploadedFilesList.length > 0 && (
              <div className="space-y-3 pt-2">
                <div className="flex justify-between items-center font-bold text-slate-800">
                  <span>Indexed Knowledge Base Documents ({uploadedFilesList.length}):</span>
                  <span className="text-[#0F766E] text-[11px]">✔ Knowledge Base Ready</span>
                </div>

                <div className="space-y-2">
                  {uploadedFilesList.map((fileItem) => (
                    <div
                      key={fileItem.id || fileItem.filename}
                      className="p-4 bg-white border border-slate-200 rounded-2xl flex items-center justify-between hover:border-slate-300 shadow-2xs transition-all"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-teal-50 text-[#0F766E] border border-teal-100 flex items-center justify-center font-bold text-xs shrink-0">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-xs font-mono">{fileItem.filename}</span>
                            <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-[10px] rounded-md">
                              ✔ Indexed
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            Size: {fileItem.size} • Uploaded at {fileItem.upload_time} • {fileItem.chunks} chunks stored in ChromaDB
                          </p>
                        </div>
                      </div>

                      {/* File Action Buttons */}
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setSelectedFileModal(fileItem)}
                          className="p-2 text-slate-600 hover:text-[#0F766E] hover:bg-slate-100 rounded-lg transition-all"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveFile(fileItem.filename)}
                          className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all"
                          title="Remove File"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Navigation Buttons: Previous <-> Next */}
            <div className="pt-4 flex gap-3">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-6 py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 transition-all flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" /> Previous Step
              </button>

              <button
                type="button"
                onClick={handleGenerateQuestions}
                disabled={loading || isUploading || uploadedFilesList.length === 0}
                className="flex-1 py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Generating Grounded Questions...</>
                ) : (
                  <><Sparkles className="w-4 h-4" /> Generate Questions from Knowledge Base <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 3: FACULTY QUESTION REVIEW QUEUE */}
      {/* ========================================================================= */}
      {step === 3 && vivaRecord && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 space-y-6">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900">Step 3: Faculty Question Review Queue</h2>
                <span className="px-2.5 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-xs rounded-full">
                  Approved: {vivaRecord.approved_questions.length} / {vivaRecord.generated_questions.length}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Approve, edit, or reject questions generated from syllabus knowledge base.
              </p>
            </div>
            <span className="text-xs font-semibold text-slate-500">Step 3 of 4</span>
          </div>

          <div className="space-y-4">
            {vivaRecord.generated_questions.map((q, idx) => {
              const isApproved = vivaRecord.approved_questions.some(aq => aq.question_id === q.question_id);
              const isEditing = editingQuestionId === q.question_id;

              return (
                <div
                  key={q.question_id}
                  className={`p-6 rounded-2xl border text-xs space-y-3.5 transition-all ${
                    isApproved ? 'bg-emerald-50/60 border-emerald-300 shadow-2xs' : 'bg-[#F8FAFC] border-slate-200'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="font-bold text-slate-900 text-sm">Question {idx + 1}</span>
                      <span className="px-2 py-0.5 bg-slate-200 text-slate-700 text-[10px] font-bold rounded-md">
                        {q.difficulty || 'Balanced'}
                      </span>
                      {q.blooms_level && (
                        <span className="px-2 py-0.5 bg-teal-100 text-teal-800 text-[10px] font-bold rounded-md">
                          Bloom: {q.blooms_level}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          if (isEditing) {
                            handleReviewQuestion(q.question_id, 'EDIT', editedQuestionText);
                          } else {
                            setEditingQuestionId(q.question_id);
                            setEditedQuestionText(q.question_text);
                          }
                        }}
                        className="px-3 py-1.5 bg-white border border-slate-200 hover:border-slate-300 text-slate-700 font-bold rounded-xl flex items-center gap-1 transition-all"
                      >
                        <Edit3 className="w-3.5 h-3.5" /> {isEditing ? 'Save Edit' : 'Edit'}
                      </button>

                      <button
                        type="button"
                        onClick={() => handleReviewQuestion(q.question_id, 'APPROVE')}
                        className={`px-4 py-1.5 rounded-xl font-bold flex items-center gap-1.5 transition-all ${
                          isApproved ? 'bg-[#0F766E] text-white shadow-xs' : 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                        }`}
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> {isApproved ? 'Approved' : 'Approve'}
                      </button>

                      <button
                        type="button"
                        onClick={() => handleReviewQuestion(q.question_id, 'REJECT')}
                        className="px-3 py-1.5 bg-rose-100 hover:bg-rose-200 text-rose-800 font-bold rounded-xl flex items-center gap-1 transition-all"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>
                  </div>

                  {isEditing ? (
                    <div className="space-y-2">
                      <textarea
                        rows={2}
                        value={editedQuestionText}
                        onChange={(e) => setEditedQuestionText(e.target.value)}
                        className="w-full p-3 bg-white border border-[#0F766E] rounded-xl text-slate-900 font-semibold focus:outline-none text-xs"
                      />
                    </div>
                  ) : (
                    <p className="font-extrabold text-slate-900 text-sm leading-snug">
                      "{q.question_text}"
                    </p>
                  )}

                  <div className="p-3 bg-white rounded-xl border border-slate-200/70 space-y-2">
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="font-bold text-slate-700">Ideal Answer Benchmark:</span>
                      <div className="flex items-center gap-2">
                        {q.llm_model && (
                          <span className="px-2 py-0.5 bg-slate-100 text-slate-600 font-mono text-[9px] rounded-md border border-slate-200">
                            Model: {q.llm_model}
                          </span>
                        )}
                        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200 rounded-md">
                          Source: {q.source_page || 'Page 1'} · {q.topic || 'General'}
                        </span>
                      </div>
                    </div>
                    <p className="text-slate-600 text-xs leading-relaxed">{q.ideal_answer}</p>
                    
                    {/* Rubric Breakdown */}
                    {q.rubric && q.rubric.length > 0 && (
                      <div className="pt-2 border-t border-slate-100">
                        <span className="font-bold text-slate-700 text-[10px] block mb-1">Evaluation Rubric Criteria (10 Marks):</span>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-1.5">
                          {q.rubric.map((r, rIdx) => (
                            <div key={rIdx} className="p-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[10px] text-slate-700 flex justify-between items-center">
                              <span className="truncate pr-1">{r.criterion || r}</span>
                              <span className="font-bold text-[#0F766E] shrink-0 font-mono">+{r.marks || 3.0}M</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {q.verification_status === "VERIFIED" ? (
                      <div className="pt-1 flex items-center justify-between text-[10px] text-emerald-700 font-medium">
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                          <span>Verified: Grounded in uploaded document evidence</span>
                        </div>
                        {q.source_chunk && (
                          <span className="text-slate-400 font-mono text-[9px]">Chunk: {q.source_chunk}</span>
                        )}
                      </div>
                    ) : (
                      <div className="pt-1 flex items-center justify-between text-[10px] text-amber-700 font-medium">
                        <div className="flex items-center gap-1.5">
                          <Sparkles className="w-3 h-3 text-amber-600 shrink-0" />
                          <span>Staged for Faculty Review (Needs Inspection)</span>
                        </div>
                        {q.source_chunk && (
                          <span className="text-slate-400 font-mono text-[9px]">Chunk: {q.source_chunk}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Navigation Buttons: Previous <-> Publish */}
          <div className="pt-4 flex gap-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setStep(2)}
              className="px-6 py-3.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Previous Step (Syllabus Upload)
            </button>

            <button
              type="button"
              onClick={handlePublishViva}
              disabled={loading || (vivaRecord.approved_questions.length === 0 && vivaRecord.generated_questions.length === 0)}
              className="flex-1 py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Publish Viva Session to Students <ArrowRight className="w-4 h-4" /></>}
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* STEP 4: VIVA PUBLISHED CONFIRMATION */}
      {/* ========================================================================= */}
      {step === 4 && vivaRecord && (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-10 max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto shadow-xs">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <div className="space-y-1.5">
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Viva Session Successfully Published!
            </h2>
            <p className="text-xs text-slate-500 font-medium">
              Students can now access and execute this examination on the AutoViva Student Portal.
            </p>
          </div>

          {/* Session Metadata Summary Card */}
          <div className="p-6 bg-[#F8FAFC] border border-slate-200 rounded-2xl text-xs space-y-3 text-left">
            <div className="flex justify-between border-b border-slate-200/70 pb-2">
              <span className="text-slate-500 font-semibold">Session ID:</span>
              <span className="font-mono font-bold text-slate-900">{vivaRecord.viva_id}</span>
            </div>
            <div className="flex justify-between border-b border-slate-200/70 pb-2">
              <span className="text-slate-500 font-semibold">Subject & Course:</span>
              <span className="font-bold text-slate-900">{vivaRecord.subject} ({vivaRecord.course_code})</span>
            </div>
            <div className="flex justify-between border-b border-slate-200/70 pb-2">
              <span className="text-slate-500 font-semibold">Active Questions:</span>
              <span className="font-bold text-[#0F766E]">{vivaRecord.approved_questions.length || vivaRecord.generated_questions.length} Questions</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-semibold">Student Batch:</span>
              <span className="font-bold text-slate-900">{vivaRecord.batch}</span>
            </div>
          </div>

          <div className="pt-2 flex justify-center gap-4 text-xs font-bold">
            <button
              type="button"
              onClick={() => setStep(3)}
              className="px-5 py-3 bg-slate-100 text-slate-700 border border-slate-200 rounded-xl hover:bg-slate-200 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Previous Step (Review)
            </button>
            <Link
              to="/student/dashboard"
              className="px-6 py-3 bg-[#0F766E] text-white rounded-xl shadow-md hover:bg-[#0D645D] transition-all flex items-center gap-2"
            >
              View in Student Portal <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* File Details Preview Modal */}
      {selectedFileModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-4 text-xs">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#0F766E]" /> {selectedFileModal.filename}
              </h3>
              <button onClick={() => setSelectedFileModal(null)} className="text-slate-400 hover:text-slate-600 font-bold">✕</button>
            </div>
            <div className="space-y-2 text-slate-600">
              <p><strong>File Size:</strong> {selectedFileModal.size}</p>
              <p><strong>Upload Timestamp:</strong> {selectedFileModal.upload_time}</p>
              <p><strong>ChromaDB Vector Store:</strong> {selectedFileModal.chunks} chunk embeddings stored.</p>
              <p><strong>Status:</strong> <span className="text-emerald-700 font-bold">✔ Knowledge Base Ready</span></p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedFileModal(null)}
              className="w-full py-2.5 bg-[#0F766E] text-white font-bold rounded-xl"
            >
              Close Preview
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
