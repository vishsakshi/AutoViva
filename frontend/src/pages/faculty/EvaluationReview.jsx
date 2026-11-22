import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileCheck, ArrowLeft, CheckCircle2, Edit3, AlertTriangle, Layers, CalendarClock, ShieldCheck, Award, Send } from 'lucide-react';
import { getApiUrl } from '../../services/api';

const getActiveVersion = (record) => record?.faculty_version_v2 || record?.ai_version_v1;
const getScore = (record) => getActiveVersion(record)?.evaluation_summary?.final_score ?? 0;
const getMaxScore = (record) => getActiveVersion(record)?.evaluation_summary?.max_score ?? 0;

export default function EvaluationReview() {
  const [sessions, setSessions] = useState([]);
  const [publishedSessions, setPublishedSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [selectedEval, setSelectedEval] = useState(null);
  const [criterionScores, setCriterionScores] = useState({});
  const [newTotalScore, setNewTotalScore] = useState('');
  const [comment, setComment] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [queueError, setQueueError] = useState('');
  const [message, setMessage] = useState(null);

  const selectRecord = useCallback((record) => {
    setSelectedEval(record);
    const initialScores = {};
    getActiveVersion(record)?.criterion_feedback?.forEach((criterion) => {
      initialScores[criterion.criterion_id] = criterion.earned_marks;
    });
    setCriterionScores(initialScores);
    setNewTotalScore(getScore(record));
    setComment('');
    setReason('');
  }, []);

  const fetchSessions = useCallback(async (preferredSessionId = selectedSessionId, preferredEvalId = selectedEval?.evaluation_id) => {
    setQueueError('');
    try {
      const res = await fetch(getApiUrl('/api/evaluation/sessions'));
      if (!res.ok) throw new Error(`Could not load evaluation sessions (${res.status}).`);
      const data = await res.json();
      const loaded = Array.isArray(data) ? data : [];
      setSessions(loaded);

      const session = loaded.find((item) => item.session_id === preferredSessionId) || loaded[0];
      setSelectedSessionId(session?.session_id || '');
      const record = session?.evaluations?.find((item) => item.evaluation_id === preferredEvalId)
        || session?.evaluations?.[0];
      if (record) selectRecord(record);
      else setSelectedEval(null);
    } catch (error) {
      setQueueError(error.message || 'Could not load evaluation sessions.');
    }
  }, [selectedEval?.evaluation_id, selectedSessionId, selectRecord]);

  const fetchPublishedSessions = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl('/api/evaluation/published-sessions'));
      if (!res.ok) throw new Error(`Could not load published results (${res.status}).`);
      const data = await res.json();
      setPublishedSessions(Array.isArray(data) ? data : []);
    } catch (error) {
      setQueueError((current) => current || error.message || 'Could not load published results.');
    }
  }, []);

  useEffect(() => {
    fetchSessions('', '');
    fetchPublishedSessions();
  }, []);

  const selectedSession = sessions.find((session) => session.session_id === selectedSessionId) || null;

  const selectSession = (session) => {
    setSelectedSessionId(session.session_id);
    selectRecord(session.evaluations[0]);
  };

  const handleCriterionScoreChange = (criterionId, val) => {
    const num = parseFloat(val) || 0;
    const updated = { ...criterionScores, [criterionId]: num };
    setCriterionScores(updated);
    setNewTotalScore(Object.values(updated).reduce((acc, curr) => acc + curr, 0).toFixed(2));
  };

  const handleApprove = async (record = selectedEval) => {
    if (!record) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(getApiUrl(`/api/evaluation/${record.evaluation_id}/approve?comment=${encodeURIComponent(comment)}`), {
        method: 'POST',
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `Could not approve evaluation (${res.status}).`);
      }
      setMessage({ type: 'success', text: `Question evaluation approved.` });
      await fetchSessions(selectedSessionId, record.evaluation_id);
      await fetchPublishedSessions();
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Error approving evaluation.' });
    } finally {
      setLoading(false);
    }
  };

  const handleOverride = async () => {
    if (!selectedEval) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(getApiUrl(`/api/evaluation/${selectedEval.evaluation_id}/override`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'OVERRIDE',
          criterion_score_overrides: criterionScores,
          reason_for_change: reason,
          faculty_comment: comment,
        }),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `Could not save mark override (${res.status}).`);
      }
      setMessage({ type: 'success', text: `Faculty override saved.` });
      await fetchSessions(selectedSessionId, selectedEval.evaluation_id);
      await fetchPublishedSessions();
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Error overriding marks.' });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (value) => {
    if (!value) return 'Date unavailable';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  };

  const handlePublishSession = async () => {
    if (!selectedSession) return;
    const allReviewed = selectedSession.evaluations.every(
      (record) => record.status === 'APPROVED' || record.status === 'OVERRIDDEN'
    );
    if (!allReviewed) {
      setMessage({ type: 'error', text: 'Approve or override every question before publishing the viva result.' });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch(getApiUrl(`/api/evaluation/sessions/${encodeURIComponent(selectedSession.session_id)}/publish`), {
        method: 'POST',
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.detail || `Could not publish viva result (${res.status}).`);
      }
      setMessage({ type: 'success', text: 'Viva result approved and published to the student portal.' });
      await fetchSessions(selectedSessionId, selectedEval?.evaluation_id);
      await fetchPublishedSessions();
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Could not publish viva result.' });
    } finally {
      setLoading(false);
    }
  };

  const openReviewControls = (record) => {
    selectRecord(record);
    requestAnimationFrame(() => document.getElementById('question-review-controls')?.scrollIntoView({ behavior: 'smooth' }));
  };

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
      <div className="flex justify-between items-center pb-6 border-b border-slate-200/80">
        <div>
          <Link to="/faculty/dashboard" className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1 mb-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Faculty Control Center
          </Link>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">AutoViva Faculty Evaluation Review Workspace</h1>
          <p className="text-xs text-slate-500 mt-1">
            Review question answers and AI rubric evidence within each student viva attempt.
          </p>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-2xl border text-xs font-semibold flex items-center justify-between ${
          message.type === 'success' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'
        }`}>
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="text-xs underline">Dismiss</button>
        </div>
      )}

      {queueError && (
        <div className="p-4 rounded-2xl border border-rose-200 bg-rose-50 text-xs font-semibold text-rose-800 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {queueError}
          <button onClick={() => fetchSessions()} className="ml-auto underline">Retry</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <aside className="lg:col-span-4 bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <FileCheck className="w-4 h-4 text-blue-600" /> Viva Attempts ({sessions.length})
          </h3>

          {sessions.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-4 text-center">
              {queueError ? 'Evaluation sessions could not be loaded.' : 'No evaluations submitted yet.'}
            </p>
          ) : (
            <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
              {sessions.map((session) => {
                const isSelected = selectedSessionId === session.session_id;
                return (
                  <button
                    key={session.session_id}
                    type="button"
                    onClick={() => selectSession(session)}
                    className={`w-full text-left p-4 rounded-2xl border transition-all text-xs space-y-2 ${
                      isSelected ? 'bg-blue-50/80 border-blue-500 shadow-sm' : 'bg-[#F8FAFC] border-slate-200/80 hover:bg-slate-100/80'
                    }`}
                  >
                    <div className="flex justify-between items-center gap-2">
                      <span className="font-bold text-slate-900">{session.student_name || 'Student name unavailable'}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">{session.status.replaceAll('_', ' ')}</span>
                    </div>
                    <div className="text-[11px] text-slate-500">Student ID: {session.student_id || 'Unavailable'}</div>
                    <div className="font-semibold text-slate-800">{session.viva_title}</div>
                    <div className="text-[11px] text-slate-600">
                      {session.legacy ? 'Attempt ID unavailable (historical record)' : `Attempt: ${session.attempt_id}`}
                    </div>
                    <div className="flex items-center gap-1 text-[10px] text-slate-500">
                      <CalendarClock className="w-3 h-3" /> {formatDate(session.started_at)}
                    </div>
                    <div className="flex justify-between items-center pt-1 border-t border-slate-200/70">
                      <span>{session.question_count} question{session.question_count === 1 ? '' : 's'}</span>
                      <span className="font-bold text-blue-700">{session.total_marks} / {session.max_marks}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </aside>

        <section className="lg:col-span-8 space-y-5 min-w-0">
          {selectedSession ? (
            <>
              <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6">
                <div className="flex flex-wrap justify-between gap-4 items-start">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-blue-600">Session Review</p>
                    <h2 className="text-lg font-extrabold text-slate-900 mt-1">{selectedSession.student_name || 'Student name unavailable'}</h2>
                    <p className="text-xs text-slate-500 mt-1">Student ID: {selectedSession.student_id || 'Unavailable'}</p>
                    <p className="text-sm font-semibold text-slate-800 mt-3">{selectedSession.viva_title}</p>
                    <p className="text-[11px] text-slate-500 mt-1">
                      {selectedSession.legacy ? 'Attempt ID unavailable — this historical evaluation is isolated.' : `Attempt ID: ${selectedSession.attempt_id}`}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-1">{formatDate(selectedSession.started_at)}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-500 block">Session Total</span>
                    <span className="text-2xl font-black text-blue-600 font-mono">
                      {selectedSession.total_marks} / {selectedSession.max_marks}
                    </span>
                    <span className="block text-[10px] text-slate-500 mt-1">{selectedSession.question_count} questions · {selectedSession.status.replaceAll('_', ' ')}</span>
                  </div>
                </div>
                {selectedSession.status !== 'PUBLISHED' && (
                  <div className="mt-4 flex justify-end">
                    <button
                      type="button"
                      onClick={handlePublishSession}
                      disabled={loading || !selectedSession.evaluations.every(
                        (record) => record.status === 'APPROVED' || record.status === 'OVERRIDDEN'
                      )}
                      className="px-4 py-2.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send className="w-4 h-4" /> Approve & Publish Viva Result
                    </button>
                  </div>
                )}
                {selectedSession.legacy && (
                  <p className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800">
                    This evaluation predates attempt IDs. It is shown separately because its original session cannot be recovered safely.
                  </p>
                )}
              </div>

              <div className="space-y-4">
                {selectedSession.evaluations.map((record, index) => {
                  const version = getActiveVersion(record);
                  const summary = version?.evaluation_summary;
                  return (
                    <article key={record.evaluation_id} className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-5 space-y-4">
                      <div className="flex flex-wrap justify-between items-start gap-3 border-b border-slate-100 pb-3">
                        <div className="min-w-0 flex-1">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-blue-600">
                            Question {record.question_number || index + 1}
                          </p>
                          <h3 className="text-sm font-bold text-slate-900 mt-1">{record.question_text}</h3>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="text-[10px] text-slate-500 block">Question Score</span>
                          <span className="font-black text-blue-700 font-mono">{summary?.final_score ?? 0} / {summary?.max_score ?? 0}</span>
                        </div>
                      </div>
                      <div>
                        <p className="text-[11px] font-bold text-slate-700 mb-1">Student Answer</p>
                        <div className="p-3 bg-[#F8FAFC] rounded-xl border border-slate-200/80 text-xs text-slate-800 leading-relaxed whitespace-pre-wrap">
                          {record.student_answer}
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-[11px] font-bold text-slate-700">AI Evaluation & Rubric Criteria</p>
                        {(version?.criterion_feedback || []).map((criterion) => (
                          <div key={criterion.criterion_id} className="p-3 bg-[#F8FAFC] rounded-xl border border-slate-200/80 text-[11px] space-y-1">
                            <div className="flex flex-wrap justify-between gap-2">
                              <span className="font-bold text-slate-900">
                                {criterion.criterion_id.toUpperCase()}: {criterion.criterion_text}
                              </span>
                              <span className="font-bold text-blue-700">
                                {criterion.earned_marks} / {criterion.allocated_marks} marks
                              </span>
                            </div>
                            <p className="text-slate-600">
                              Classification: <span className="font-semibold">{criterion.classification}</span>
                            </p>
                            {criterion.evidence_quote && <p className="text-slate-600">Evidence: “{criterion.evidence_quote}”</p>}
                            {criterion.feedback_note && <p className="text-slate-600">Reasoning: {criterion.feedback_note}</p>}
                          </div>
                        ))}
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => openReviewControls(record)}
                          className="px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-xl text-[11px] font-bold flex items-center gap-1"
                        >
                          <Edit3 className="w-3.5 h-3.5" /> Edit Marks
                        </button>
                        {record.status === 'PENDING_REVIEW' && (
                          <button
                            type="button"
                            disabled={loading}
                            onClick={() => handleApprove(record)}
                            className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-[11px] font-bold flex items-center gap-1 disabled:opacity-50"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" /> Approve Question
                          </button>
                        )}
                      </div>
                    </article>
                  );
                })}
              </div>

              {selectedEval && (
                <div id="question-review-controls" className="bg-white rounded-3xl border border-blue-200 shadow-sm p-6 space-y-5">
                  <div className="border-b border-slate-100 pb-3">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-blue-600">Question Override Controls</p>
                    <h3 className="text-sm font-bold text-slate-900 mt-1">Question {selectedEval.question_number || '?'} — {selectedEval.question_text}</h3>
                    <p className="text-xs text-slate-500 mt-1">Current score: {newTotalScore} / {getMaxScore(selectedEval)}</p>
                  </div>
                  <div className="space-y-3">
                    {(getActiveVersion(selectedEval)?.criterion_feedback || []).map((criterion) => (
                      <div key={criterion.criterion_id} className="p-4 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 text-xs space-y-2">
                        <div className="flex justify-between items-center gap-3">
                          <span className="font-bold text-slate-900">{criterion.criterion_id.toUpperCase()}: {criterion.criterion_text}</span>
                          <div className="flex items-center gap-2 shrink-0">
                            <input
                              aria-label={`Marks for ${criterion.criterion_text}`}
                              type="number"
                              step="0.5"
                              min="0"
                              max={criterion.allocated_marks}
                              value={criterionScores[criterion.criterion_id] ?? criterion.earned_marks}
                              onChange={(event) => handleCriterionScoreChange(criterion.criterion_id, event.target.value)}
                              className="w-16 px-2 py-1 bg-white border border-slate-300 rounded-lg text-slate-900 font-bold font-mono text-center focus:outline-none focus:border-blue-500"
                            />
                            <span className="text-slate-400">/ {criterion.allocated_marks}</span>
                          </div>
                        </div>
                        <p className="text-[11px] text-slate-600">Classification: <strong>{criterion.classification}</strong> · Confidence: {criterion.confidence}</p>
                        {criterion.evidence_quote && <p className="text-[11px] text-slate-600">Evidence: “{criterion.evidence_quote}”</p>}
                        {criterion.feedback_note && <p className="text-[11px] text-slate-600">Reasoning: {criterion.feedback_note}</p>}
                      </div>
                    ))}
                  </div>
                  <div className="p-4 bg-[#F8FAFC] border border-slate-200/80 rounded-2xl text-xs space-y-2">
                    <p className="font-bold text-slate-800 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-teal-600" /> Supplementary Facial-Expression Analytics
                    </p>
                    {selectedEval.facial_expression_analytics ? (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px] text-slate-700">
                        <p>Dominant expression: <strong>{selectedEval.facial_expression_analytics.dominantExpression || 'Unavailable'}</strong></p>
                        <p>Face detection coverage: <strong>{selectedEval.facial_expression_analytics.faceDetectedCoveragePercent ?? 'Unavailable'}{selectedEval.facial_expression_analytics.faceDetectedCoveragePercent != null ? '%' : ''}</strong></p>
                        <p>Average confidence: <strong>{selectedEval.facial_expression_analytics.averageConfidence ?? 'Unavailable'}</strong></p>
                      </div>
                    ) : (
                      <p className="text-[11px] text-slate-500">
                        No facial-expression summary was stored with this evaluation. Facial signals do not affect academic marks.
                      </p>
                    )}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label className="text-xs font-bold text-slate-700">
                      Faculty Comment
                      <input
                        type="text"
                        value={comment}
                        onChange={(event) => setComment(event.target.value)}
                        placeholder="Optional feedback for student..."
                        className="mt-1 w-full px-3 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 text-xs font-normal focus:outline-none focus:border-blue-500"
                      />
                    </label>
                    <label className="text-xs font-bold text-slate-700">
                      Override Reason
                      <input
                        type="text"
                        value={reason}
                        onChange={(event) => setReason(event.target.value)}
                        placeholder="Justification for mark change..."
                        className="mt-1 w-full px-3 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 text-xs font-normal focus:outline-none focus:border-blue-500"
                      />
                    </label>
                  </div>
                  <div className="flex flex-wrap justify-end gap-3">
                    {selectedEval.status === 'PENDING_REVIEW' && (
                      <button
                        onClick={() => handleApprove(selectedEval)}
                        disabled={loading}
                        className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 disabled:opacity-50"
                      >
                        <CheckCircle2 className="w-4 h-4" /> Approve Question
                      </button>
                    )}
                    <button
                      onClick={handleOverride}
                      disabled={loading}
                      className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 disabled:opacity-50"
                    >
                      <Edit3 className="w-4 h-4" /> Apply Faculty Mark Override
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center p-12 bg-white rounded-3xl border border-slate-200/80 text-slate-400 text-xs">
              <Layers className="w-4 h-4 mr-2" /> Select a viva attempt to review its questions.
            </div>
          )}
        </section>
      </div>

      <section className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <Award className="w-5 h-5 text-[#0F766E]" />
              Published Student Marks ({publishedSessions.length})
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Approved viva results visible to students.
            </p>
          </div>
          <button
            type="button"
            onClick={fetchPublishedSessions}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold"
          >
            Refresh
          </button>
        </div>

        {publishedSessions.length === 0 ? (
          <div className="p-6 bg-[#F8FAFC] border border-slate-200/80 rounded-2xl text-center text-xs text-slate-500 italic">
            No viva results have been published yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {publishedSessions.map((session) => {
              const percentage = session.max_marks > 0
                ? ((session.total_marks / session.max_marks) * 100).toFixed(1)
                : '0.0';
              return (
                <article key={session.session_id} className="p-5 bg-[#F8FAFC] border border-emerald-200 rounded-2xl space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-slate-900">
                        {session.student_name || 'Student name unavailable'}
                      </p>
                      <p className="text-[10px] text-slate-500 mt-1">
                        {session.viva_title}
                      </p>
                    </div>
                    <span className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded-lg text-[10px] font-bold">
                      PUBLISHED
                    </span>
                  </div>
                  <div className="flex items-end justify-between border-t border-slate-200 pt-3">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Final Marks</p>
                      <p className="text-xl font-black text-emerald-700 font-mono">
                        {session.total_marks} / {session.max_marks}
                      </p>
                    </div>
                    <p className="text-sm font-bold text-slate-700">{percentage}%</p>
                  </div>
                  <p className="text-[10px] text-slate-500">
                    {formatDate(session.started_at)} · {session.question_count} question{session.question_count === 1 ? '' : 's'}
                  </p>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
