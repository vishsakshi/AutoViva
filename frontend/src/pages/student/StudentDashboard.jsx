import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Mic, BookOpen, Clock, Award, CheckCircle2, ArrowRight,
  ShieldCheck, AlertCircle, Loader2, RefreshCw, GraduationCap
} from 'lucide-react';
import { getApiUrl, getAuthHeaders } from '../../services/api';

// Read which vivas this student has already completed (stored locally after viva finish)
const getCompletedVivas = () => {
  try { return JSON.parse(localStorage.getItem('autoviva_completed') || '{}'); } catch { return {}; }
};

const getUserFromStorage = () => {
  try { return JSON.parse(localStorage.getItem('autoviva_user') || '{}'); } catch { return {}; }
};

export default function StudentDashboard() {
  const navigate = useNavigate();
  const user = getUserFromStorage();

  const [publishedVivas, setPublishedVivas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState('');
  const [completedVivas, setCompletedVivas] = useState({});

  const fetchPublished = async () => {
    setLoading(true);
    setFetchError('');
    try {
      const res = await fetch(getApiUrl('/api/viva/published'), { headers: getAuthHeaders() });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      setPublishedVivas(Array.isArray(data) ? data : []);
    } catch (e) {
      setFetchError('Could not load available viva sessions. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPublished();
    setCompletedVivas(getCompletedVivas());
  }, []);

  const getVivaStatus = (vivaId) => {
    const completed = completedVivas[vivaId];
    if (completed) return 'COMPLETED';
    // Check for in-progress (saved progress in localStorage)
    try {
      const stdId = user.user_id || 'std_anonymous';
      const saved = JSON.parse(localStorage.getItem(`autoviva_progress_${vivaId}_${stdId}`) || 'null');
      if (saved && !saved.completedAt) return 'IN_PROGRESS';
    } catch (_) {}
    return 'NOT_STARTED';
  };

  const statusBadge = (status) => {
    if (status === 'COMPLETED') return (
      <span className="flex items-center gap-1 px-2.5 py-0.5 bg-emerald-100 border border-emerald-300 text-emerald-800 text-[10px] font-bold rounded-full">
        <CheckCircle2 className="w-3 h-3" /> Completed
      </span>
    );
    if (status === 'IN_PROGRESS') return (
      <span className="flex items-center gap-1 px-2.5 py-0.5 bg-amber-100 border border-amber-300 text-amber-800 text-[10px] font-bold rounded-full">
        <Clock className="w-3 h-3" /> In Progress
      </span>
    );
    return (
      <span className="flex items-center gap-1 px-2.5 py-0.5 bg-teal-50 border border-teal-200 text-teal-700 text-[10px] font-bold rounded-full">
        Available
      </span>
    );
  };

  const handleStartViva = (vivaId) => {
    // Route through pre-viva instructions screen, passing viva_id
    navigate(`/student/viva/pre?viva_id=${encodeURIComponent(vivaId)}`);
  };

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">

      {/* Header */}
      <div className="flex justify-between items-start pb-6 border-b border-slate-200/80 flex-wrap gap-4">
        <div>
          <span className="text-xs font-bold text-[#0F766E] uppercase tracking-widest block mb-1">
            Student Portal
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Examination Workspace
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Attend live AI oral viva examinations. Answers are evaluated and reviewed by faculty.
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {user.name && (
            <span className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5">
              <GraduationCap className="w-4 h-4 text-[#0F766E]" /> {user.name}
            </span>
          )}
          <span className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#0F766E]" /> Student Access
          </span>
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center gap-3 py-16">
          <Loader2 className="w-6 h-6 text-[#0F766E] animate-spin" />
          <p className="text-slate-500 text-sm">Loading available viva sessions…</p>
        </div>
      )}

      {/* Error state */}
      {!loading && fetchError && (
        <div className="p-5 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-bold text-rose-800">Could not load viva sessions</p>
            <p className="text-xs text-rose-700 mt-0.5">{fetchError}</p>
          </div>
          <button
            onClick={fetchPublished}
            className="px-3 py-1.5 bg-rose-600 text-white text-xs font-bold rounded-xl flex items-center gap-1 hover:bg-rose-700"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry
          </button>
        </div>
      )}

      {/* No vivas available */}
      {!loading && !fetchError && publishedVivas.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center">
            <BookOpen className="w-7 h-7 text-slate-400" />
          </div>
          <div>
            <p className="text-slate-700 font-bold text-sm">No viva sessions available yet</p>
            <p className="text-slate-400 text-xs mt-1">
              Your faculty has not published any viva sessions yet. Check back later.
            </p>
          </div>
          <button
            onClick={fetchPublished}
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl border border-slate-200 flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>
      )}

      {/* Published viva list */}
      {!loading && !fetchError && publishedVivas.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900">
              Available Examinations
              <span className="ml-2 text-[#0F766E]">({publishedVivas.length})</span>
            </h2>
            <button
              onClick={fetchPublished}
              className="flex items-center gap-1.5 text-[11px] text-slate-500 hover:text-slate-700 font-semibold"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {publishedVivas.map((v) => {
              const status = getVivaStatus(v.viva_id);
              const isCompleted = status === 'COMPLETED';
              const isInProgress = status === 'IN_PROGRESS';
              const completedData = completedVivas[v.viva_id];

              return (
                <div
                  key={v.viva_id}
                  className={`p-6 bg-white rounded-3xl border shadow-sm flex flex-col gap-4 transition-all hover:shadow-md ${
                    isCompleted ? 'border-emerald-200' : 'border-slate-200/80'
                  }`}
                >
                  {/* Header */}
                  <div className="flex justify-between items-start gap-2">
                    <div className="w-9 h-9 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center shrink-0">
                      <Mic className="w-4 h-4 text-[#0F766E]" />
                    </div>
                    {statusBadge(status)}
                  </div>

                  {/* Info */}
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-slate-900 leading-tight">
                      {v.subject}
                      {v.course_code ? ` (${v.course_code})` : ''}
                    </h3>
                    <p className="text-xs text-slate-500 font-medium">{v.topic}</p>
                  </div>

                  {/* Meta */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    {[
                      { label: 'Questions', value: v.question_count ?? (v.approved_questions?.length ?? '—') },
                      { label: 'Duration', value: v.duration_minutes ? `${v.duration_minutes}m` : '—' },
                      { label: 'Batch', value: v.batch || '—' },
                    ].map(({ label, value }) => (
                      <div key={label} className="p-2 bg-slate-50 rounded-xl border border-slate-100">
                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wide">{label}</p>
                        <p className="text-xs font-bold text-slate-800 mt-0.5 truncate">{value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Completed info */}
                  {isCompleted && completedData && (
                    <div className="p-2.5 bg-emerald-50 border border-emerald-100 rounded-2xl text-[11px] text-emerald-700">
                      ✓ Submitted {completedData.submittedCount} answer{completedData.submittedCount !== 1 ? 's' : ''}
                      {completedData.completedAt && (
                        <span className="text-emerald-500 ml-1">
                          · {new Date(completedData.completedAt).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  )}

                  {/* CTA */}
                  {isCompleted ? (
                    <button
                      disabled
                      className="w-full py-2.5 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold rounded-2xl flex items-center justify-center gap-2 cursor-default"
                    >
                      <CheckCircle2 className="w-4 h-4" /> Viva Completed
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStartViva(v.viva_id)}
                      className="w-full py-2.5 bg-[#0F766E] hover:bg-[#0D645D] text-white text-xs font-bold rounded-2xl flex items-center justify-center gap-2 shadow-md shadow-[#0F766E]/15 transition-all"
                    >
                      {isInProgress ? (
                        <><RefreshCw className="w-3.5 h-3.5" /> Resume Viva <ArrowRight className="w-3.5 h-3.5" /></>
                      ) : (
                        <><Mic className="w-3.5 h-3.5" /> Start Viva <ArrowRight className="w-3.5 h-3.5" /></>
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}
