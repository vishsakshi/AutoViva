import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileCheck, ArrowLeft, CheckCircle2, Edit3, ShieldCheck, AlertTriangle, Layers, UserCheck } from 'lucide-react';
import { getApiUrl } from '../../services/api';

export default function EvaluationReview() {
  const [evaluations, setEvaluations] = useState([]);
  const [selectedEval, setSelectedEval] = useState(null);
  const [criterionScores, setCriterionScores] = useState({});
  const [newTotalScore, setNewTotalScore] = useState('');
  const [comment, setComment] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchEvaluations = async () => {
    try {
      const res = await fetch(getApiUrl('/api/evaluation/all'));
      if (res.ok) {
        const data = await res.json();
        setEvaluations(data || []);
        if (data && data.length > 0 && !selectedEval) {
          selectRecord(data[0]);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchEvaluations();
  }, []);

  const selectRecord = (record) => {
    setSelectedEval(record);
    const activeVersion = record.faculty_version_v2 || record.ai_version_v1;
    const initialScores = {};
    if (activeVersion && activeVersion.criterion_feedback) {
      activeVersion.criterion_feedback.forEach(c => {
        initialScores[c.criterion_id] = c.earned_marks;
      });
    }
    setCriterionScores(initialScores);
    setNewTotalScore(activeVersion?.evaluation_summary?.final_score || 0);
    setComment('');
    setReason('');
  };

  const handleCriterionScoreChange = (criterionId, val) => {
    const num = parseFloat(val) || 0;
    const updated = { ...criterionScores, [criterionId]: num };
    setCriterionScores(updated);
    
    const total = Object.values(updated).reduce((acc, curr) => acc + curr, 0);
    setNewTotalScore(total.toFixed(2));
  };

  const handleApprove = async () => {
    if (!selectedEval) return;
    setLoading(true);
    try {
      const res = await fetch(getApiUrl(`/api/evaluation/${selectedEval.evaluation_id}/approve?comment=${encodeURIComponent(comment)}`), {
        method: 'POST'
      });
      if (res.ok) {
        setMessage({ type: 'success', text: `Evaluation ${selectedEval.evaluation_id} approved by faculty.` });
        fetchEvaluations();
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Error approving evaluation.' });
    } finally {
      setLoading(false);
    }
  };

  const handleOverride = async () => {
    if (!selectedEval || !reason.trim()) {
      alert('Override reason is required.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(getApiUrl(`/api/evaluation/${selectedEval.evaluation_id}/override`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          criterion_scores: criterionScores,
          override_reason: reason,
          faculty_comment: comment
        })
      });
      if (res.ok) {
        setMessage({ type: 'success', text: `Faculty override saved for ${selectedEval.evaluation_id}.` });
        fetchEvaluations();
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Error overriding marks.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200/80">
        <div>
          <Link to="/faculty/dashboard" className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1 mb-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Faculty Control Center
          </Link>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            AutoViva Faculty Evaluation Review Workspace
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Faculty review & mark override interface with verbatim evidence verification and dual version tracking
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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left List (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 space-y-4 h-fit">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <FileCheck className="w-4 h-4 text-blue-600" /> Pending Review Records ({evaluations.length})
          </h3>

          {evaluations.length === 0 ? (
            <p className="text-xs text-slate-400 italic py-4 text-center">No evaluations submitted yet.</p>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {evaluations.map((rec) => {
                const isSelected = selectedEval?.evaluation_id === rec.evaluation_id;
                const score = rec.faculty_version_v2?.evaluation_summary?.final_score || rec.ai_version_v1?.evaluation_summary?.final_score;
                return (
                  <div
                    key={rec.evaluation_id}
                    onClick={() => selectRecord(rec)}
                    className={`p-4 rounded-2xl border cursor-pointer transition-all text-xs space-y-2 ${
                      isSelected
                        ? 'bg-blue-50/80 border-blue-500 shadow-sm'
                        : 'bg-[#F8FAFC] border-slate-200/80 hover:bg-slate-100/80'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-900 font-mono">{rec.evaluation_id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rec.status === 'PUBLISHED' ? 'bg-emerald-100 text-emerald-800' :
                        rec.status === 'FACULTY_OVERRIDDEN' ? 'bg-indigo-100 text-indigo-800' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {rec.status}
                      </span>
                    </div>
                    <p className="text-slate-700 font-medium line-clamp-1">{rec.question_text}</p>
                    <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                      <span>Student: {rec.student_id}</span>
                      <span className="font-bold text-blue-600">{score} / 10.0</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Detail & Override Controls (8 cols) */}
        {selectedEval ? (
          <div className="lg:col-span-8 space-y-6">
            
            {/* Record Summary */}
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 space-y-4">
              <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                <div>
                  <span className="text-[11px] font-mono text-slate-400 uppercase">Record ID: {selectedEval.evaluation_id}</span>
                  <h2 className="text-base font-bold text-slate-900 mt-1">"{selectedEval.question_text}"</h2>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-500 block">Current Marks</span>
                  <span className="text-xl font-black text-blue-600 font-mono">{newTotalScore} / 10.0</span>
                </div>
              </div>

              {/* Student Verified Transcript */}
              <div className="space-y-1">
                <span className="text-xs font-bold text-slate-700">Student Verified Transcript:</span>
                <div className="p-4 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 text-xs text-slate-800 leading-relaxed font-sans">
                  "{selectedEval.student_answer}"
                </div>
              </div>

              {/* Criteria Feedback Grid */}
              <div className="space-y-3 pt-2">
                <span className="text-xs font-bold text-slate-700">Rubric Criteria Breakdown & Override:</span>
                {(selectedEval.faculty_version_v2 || selectedEval.ai_version_v1)?.criterion_feedback?.map((c) => (
                  <div key={c.criterion_id} className="p-4 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 text-xs space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-slate-900">{c.criterion_id.toUpperCase()}: {c.criterion_text}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-500 text-[11px]">Marks:</span>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          max={c.allocated_marks}
                          value={criterionScores[c.criterion_id] !== undefined ? criterionScores[c.criterion_id] : c.earned_marks}
                          onChange={(e) => handleCriterionScoreChange(c.criterion_id, e.target.value)}
                          className="w-16 px-2 py-1 bg-white border border-slate-300 rounded-lg text-slate-900 font-bold font-mono text-center focus:outline-none focus:border-blue-500"
                        />
                        <span className="text-slate-400">/ {c.allocated_marks}</span>
                      </div>
                    </div>
                    <div className="text-[11px] text-slate-600 space-y-1">
                      <div>Classification: <span className="font-bold text-blue-600">{c.classification}</span> (Confidence: {c.confidence})</div>
                      {c.evidence_quote && <div>Verbatim Evidence: <span className="italic text-slate-800">"{c.evidence_quote}"</span></div>}
                      <div>Reasoning: {c.reasoning}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Supplementary Facial Expression Analytics */}
              <div className="p-4 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 text-xs space-y-3">
                <div className="flex justify-between items-center border-b border-slate-200/60 pb-2">
                  <span className="font-bold text-slate-800 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-teal-600" /> Supplementary Facial-Expression Analytics
                  </span>
                  <span className="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full font-medium">
                    Non-Grading Monitoring Signal
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-slate-700 text-[11px]">
                  <div className="p-2.5 bg-white rounded-xl border border-slate-200">
                    <span className="text-slate-400 block text-[10px]">Dominant Visible Expression</span>
                    <span className="font-bold text-slate-900 text-xs">
                      {selectedEval?.facial_expression_analytics?.dominantExpression || 'NEUTRAL'}
                    </span>
                  </div>

                  <div className="p-2.5 bg-white rounded-xl border border-slate-200">
                    <span className="text-slate-400 block text-[10px]">Face Detection Coverage</span>
                    <span className="font-bold text-teal-700 text-xs">
                      {selectedEval?.facial_expression_analytics?.faceDetectedCoveragePercent || 96}%
                    </span>
                  </div>

                  <div className="p-2.5 bg-white rounded-xl border border-slate-200">
                    <span className="text-slate-400 block text-[10px]">Average Confidence</span>
                    <span className="font-bold text-slate-900 text-xs">
                      {selectedEval?.facial_expression_analytics?.averageConfidence || 0.86}
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5 pt-1">
                  <span className="text-[10px] font-bold text-slate-500 block uppercase tracking-wider">
                    Visible Expression Distribution
                  </span>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {Object.entries(selectedEval?.facial_expression_analytics?.expressionDistribution || {
                      NEUTRAL: 68,
                      HAPPY: 14,
                      FEAR: 7,
                      SAD: 5,
                      SURPRISE: 4,
                      ANGRY: 2
                    }).map(([expr, pct]) => (
                      <div key={expr} className="flex justify-between items-center p-1.5 bg-white rounded-lg border border-slate-200 text-[10px]">
                        <span className="font-medium text-slate-600">{expr}</span>
                        <span className="font-bold text-slate-900">{pct}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                <p className="text-[10px] text-slate-400 italic">
                  Note: Facial-expression analytics are supplementary visible signals and do NOT affect academic evaluation scores.
                </p>
              </div>
              <div className="pt-4 border-t border-slate-100 space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Faculty General Comment</label>
                  <input
                    type="text"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Optional feedback for student..."
                    className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Override Reason (Required if modifying marks)</label>
                  <input
                    type="text"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Justification for mark override..."
                    className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 text-xs focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={handleApprove}
                    disabled={loading}
                    className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" /> Approve & Publish AI Evaluation
                  </button>

                  <button
                    onClick={handleOverride}
                    disabled={loading || !reason.trim()}
                    className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Edit3 className="w-4 h-4" /> Apply Faculty Mark Override
                  </button>
                </div>
              </div>

            </div>

          </div>
        ) : (
          <div className="lg:col-span-8 flex items-center justify-center p-12 bg-white rounded-3xl border border-slate-200/80 text-slate-400 text-xs">
            Select an evaluation record from the left panel to review.
          </div>
        )}

      </div>
    </div>
  );
}
