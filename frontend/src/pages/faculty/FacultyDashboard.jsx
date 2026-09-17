import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, FileCheck, ArrowRight, PlusCircle, Trash2, BookOpen, AlertTriangle, Loader2 } from 'lucide-react';

export default function FacultyDashboard() {
  const [publishedVivas, setPublishedVivas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteModalViva, setDeleteModalViva] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [toast, setToast] = useState(null);

  const fetchPublishedVivas = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/viva/published');
      if (res.ok) {
        const data = await res.json();
        setPublishedVivas(data || []);
      }
    } catch (e) {
      console.error('Failed to fetch published vivas:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPublishedVivas();
  }, []);

  const handleDeleteConfirm = async () => {
    if (!deleteModalViva) return;
    const vivaId = deleteModalViva.viva_id;
    setDeletingId(vivaId);

    try {
      const token = localStorage.getItem('autoviva_jwt_token') || sessionStorage.getItem('autoviva_jwt_token');
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`/api/viva/${vivaId}`, {
        method: 'DELETE',
        headers
      });

      if (res.ok) {
        setToast({ type: 'success', text: `Successfully deleted examination '${deleteModalViva.subject}' (${deleteModalViva.course_code}).` });
        setPublishedVivas(prev => prev.filter(v => v.viva_id !== vivaId));
        setDeleteModalViva(null);
      } else {
        const errData = await res.json();
        setToast({ type: 'error', text: errData.detail || 'Failed to delete examination.' });
      }
    } catch (err) {
      setToast({ type: 'error', text: 'Server connection error during deletion.' });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200/80">
        <div>
          <span className="text-xs font-bold text-[#0F766E] uppercase tracking-widest block mb-1">
            Faculty Portal
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            AutoViva Faculty Control Center
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Create viva sessions, upload syllabus documents to Knowledge Base, review AI evaluation outputs, and manage published examinations
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#0F766E]" /> Faculty Signature Authority
          </span>
        </div>
      </div>

      {/* Toast Alert */}
      {toast && (
        <div className={`p-4 rounded-2xl text-xs font-bold border flex items-center justify-between shadow-xs transition-all ${
          toast.type === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'
        }`}>
          <span>{toast.text}</span>
          <button onClick={() => setToast(null)} className="text-slate-400 hover:text-slate-600 font-bold ml-4">✕</button>
        </div>
      )}

      {/* Clean 2-Card Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* CARD 1: CREATE FACULTY VIVA PIPELINE */}
        <div className="p-8 bg-white rounded-3xl border-2 border-[#0F766E] shadow-sm hover:shadow-md transition-all space-y-5 relative overflow-hidden flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <div className="w-12 h-12 rounded-2xl bg-[#0F766E] text-white flex items-center justify-center shadow-md shadow-[#0F766E]/20">
                <PlusCircle className="w-6 h-6" />
              </div>
              <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-extrabold uppercase tracking-wider">
                PRIMARY WORKFLOW
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">Create Faculty Viva Pipeline</h3>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                Configure viva metadata parameters, upload syllabus PDF/PPT/DOCX documents to Knowledge Base, automatically extract grounded questions, review evaluation rubrics, and publish the official viva session.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <Link
              to="/faculty/viva/create"
              className="w-full py-4 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs text-center rounded-2xl transition-all shadow-md shadow-[#0F766E]/20 flex items-center justify-center gap-2"
            >
              Start Viva Creation Pipeline <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* CARD 2: FACULTY REVIEW QUEUE */}
        <div className="p-8 bg-white rounded-3xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-700">
              <FileCheck className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">Faculty Review & Override Queue</h3>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                Review AI preliminary evaluation scores, inspect verbatim student evidence quotes, override criterion marks, provide custom feedback, and publish official academic results.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <Link
              to="/faculty/evaluations"
              className="w-full py-4 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 font-bold text-xs text-center rounded-2xl transition-all flex items-center justify-center gap-2"
            >
              Open Evaluation Review Queue <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

      </div>

      {/* MANAGED PUBLISHED EXAMINATIONS SECTION */}
      <div className="p-8 bg-white rounded-3xl border border-slate-200/80 shadow-sm space-y-6">
        <div className="flex justify-between items-center border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-[#0F766E]" /> Managed Published Examinations ({publishedVivas.length})
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Active examinations published to student portal. Deleting an examination permanently removes its session metadata, questions, and associated vector store embeddings.
            </p>
          </div>
          <button
            onClick={fetchPublishedVivas}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition-all"
          >
            Refresh List
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-[#0F766E]" /> Loading active published examinations...
          </div>
        ) : publishedVivas.length === 0 ? (
          <div className="p-6 bg-[#F8FAFC] border border-slate-200/80 rounded-2xl text-center text-xs text-slate-500 italic">
            No active published examinations. Use the "Create Faculty Viva Pipeline" wizard above to create and publish a new viva session.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {publishedVivas.map((viva) => (
              <div key={viva.viva_id} className="p-5 bg-white border border-slate-200 rounded-2xl hover:border-slate-300 shadow-2xs transition-all space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex justify-between items-start">
                    <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 text-[10px] font-extrabold rounded-md uppercase tracking-wider">
                      {viva.course_code || 'CS301'}
                    </span>
                    <span className="font-mono text-[10px] text-slate-400">{viva.viva_id}</span>
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-900 text-sm truncate">{viva.subject}</h4>
                    <p className="text-xs text-slate-600 mt-0.5 truncate">Topic: {viva.topic}</p>
                  </div>

                  <div className="pt-1 text-[11px] text-slate-500 space-y-1">
                    <div className="flex justify-between">
                      <span>Questions:</span>
                      <span className="font-bold text-slate-800">{(viva.approved_questions || viva.generated_questions || []).length} Verified</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Duration / Batch:</span>
                      <span className="font-semibold text-slate-700">{viva.duration_minutes} Mins • {viva.batch}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex justify-between items-center">
                  <span className="text-[10px] text-slate-400">Created: {viva.created_at || 'Recent'}</span>
                  
                  {/* DELETE BUTTON WITH TRASH ICON */}
                  <button
                    type="button"
                    onClick={() => setDeleteModalViva(viva)}
                    className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs rounded-xl transition-all flex items-center gap-1.5 shadow-2xs"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-rose-600" /> Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* CONFIRMATION DIALOG MODAL FOR DELETION */}
      {deleteModalViva && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-5 text-xs">
            <div className="flex items-center gap-3 text-rose-600 border-b border-slate-100 pb-3">
              <div className="w-10 h-10 rounded-2xl bg-rose-100 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5 text-rose-600" />
              </div>
              <div>
                <h3 className="font-extrabold text-slate-900 text-sm">Delete Published Examination?</h3>
                <p className="text-[11px] text-slate-500 font-medium">This action cannot be undone.</p>
              </div>
            </div>

            <p className="text-slate-600 leading-relaxed">
              Are you sure you want to delete the published examination for <strong className="text-slate-900">{deleteModalViva.subject} ({deleteModalViva.course_code})</strong>?
            </p>

            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-[11px] space-y-1">
              <p className="font-bold">Deletion Scope:</p>
              <ul className="list-disc list-inside space-y-0.5 text-amber-800">
                <li>Permanently deletes session record from MongoDB database</li>
                <li>Removes vector embeddings for document ID '{deleteModalViva.document_id || 'N/A'}' from ChromaDB</li>
                <li>Removes examination from Student Portal list</li>
              </ul>
            </div>

            <div className="pt-2 flex gap-3">
              <button
                type="button"
                onClick={() => setDeleteModalViva(null)}
                disabled={deletingId !== null}
                className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 transition-all"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={deletingId !== null}
                className="flex-1 py-3 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl shadow-md shadow-rose-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {deletingId ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Delete Examination</>}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
