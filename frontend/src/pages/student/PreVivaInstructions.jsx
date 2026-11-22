import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Mic, Video, BookOpen, CheckCircle2, AlertCircle, Loader2,
  Volume2, ShieldCheck, Clock, ArrowRight, ArrowLeft
} from 'lucide-react';
import { getApiUrl, getAuthHeaders } from '../../services/api';

export default function PreVivaInstructions() {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const vivaId = searchParams.get('viva_id') || '';
  const resumeAttempt = searchParams.get('resume') === '1';

  const [vivaInfo, setVivaInfo] = useState(null);
  const [questionCount, setQuestionCount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [micChecked, setMicChecked] = useState(false);
  const [readyChecked, setReadyChecked] = useState(false);
  const [permTested, setPermTested] = useState(false);
  const [permError, setPermError] = useState('');
  const [warningLimitReached, setWarningLimitReached] = useState(false);

  // Fetch viva metadata and question count
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setLoadError('');
      try {
        let currentUser = {};
        try {
          currentUser = JSON.parse(localStorage.getItem('autoviva_user') || '{}');
        } catch {
          currentUser = {};
        }
        if (vivaId) {
          const warningKey = `autoviva_proctoring_${vivaId}_${currentUser.user_id || 'std_anonymous'}`;
          try {
            const warningRecord = JSON.parse(localStorage.getItem(warningKey) || '{}');
            if (warningRecord.terminated === true || Number(warningRecord.warningCount) >= 4) {
              setWarningLimitReached(true);
              return;
            }
          } catch (error) {
            console.error('Could not read the saved viva warning state.', error);
          }
        }

        // Get viva session details
        if (vivaId) {
          const vRes = await fetch(getApiUrl(`/api/viva/session/${vivaId}`), { headers: getAuthHeaders() });
          if (vRes.ok) {
            const vData = await vRes.json();
            setVivaInfo(vData);
          }
        }

        // Get approved question count
        const qUrl = vivaId
          ? getApiUrl(`/api/viva/active-questions?viva_id=${encodeURIComponent(vivaId)}`)
          : getApiUrl('/api/viva/active-questions');
        const qRes = await fetch(qUrl, { headers: getAuthHeaders() });
        if (!qRes.ok) {
          const err = await qRes.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${qRes.status}`);
        }
        const qData = await qRes.json();
        if (!Array.isArray(qData) || qData.length === 0) {
          throw new Error('This viva has no approved questions yet. Please wait for the faculty to publish it.');
        }
        setQuestionCount(qData.length);
      } catch (e) {
        setLoadError(e.message || 'Could not load viva information.');
      } finally {
        setLoading(false);
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const testPermissions = async () => {
    setPermError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      stream.getTracks().forEach(t => t.stop()); // release immediately — LiveVivaSession will re-request
      setPermTested(true);
      setMicChecked(true);
    } catch (err) {
      const msg = err.name === 'NotAllowedError'
        ? 'Permission denied. Please allow camera and microphone access in your browser settings, then try again.'
        : `Could not access media: ${err.message}`;
      setPermError(msg);
      setPermTested(false);
    }
  };

  const canBegin = micChecked && readyChecked && !loadError && !warningLimitReached && questionCount !== null;

  const handleBeginViva = () => {
    let user = {};
    let savedProgress = null;
    try {
      user = JSON.parse(localStorage.getItem('autoviva_user') || '{}');
      if (vivaId) {
        const warningKey = `autoviva_proctoring_${vivaId}_${user.user_id || 'std_anonymous'}`;
        const warningRecord = JSON.parse(localStorage.getItem(warningKey) || '{}');
        if (warningRecord.terminated === true || Number(warningRecord.warningCount) >= 4) {
          setWarningLimitReached(true);
          return;
        }
      }
      if (resumeAttempt && vivaId) {
        savedProgress = JSON.parse(
          localStorage.getItem(`autoviva_progress_${vivaId}_${user.user_id || 'std_anonymous'}`) || 'null'
        );
      }
    } catch {
      savedProgress = null;
    }
    const attemptId = savedProgress?.attempt_id || crypto.randomUUID();
    const attemptStartedAt = savedProgress?.attempt_started_at || new Date().toISOString();
    const params = new URLSearchParams();
    if (vivaId) params.set('viva_id', vivaId);
    params.set('attempt_id', attemptId);
    params.set('attempt_started_at', attemptStartedAt);
    const dest = `/student/viva?${params.toString()}`;
    navigate(dest);
  };

  return (
    <div className="flex-1 flex items-center justify-center p-6 bg-[#F8FAFC]">
      <div className="max-w-xl w-full bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 space-y-6">

        {/* Back link */}
        <button
          onClick={() => navigate('/student/dashboard')}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 font-semibold"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
        </button>

        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-[#0F766E] flex items-center justify-center mx-auto shadow-md shadow-[#0F766E]/20">
            <Mic className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Before You Begin</h1>
          <p className="text-xs text-slate-500">Review these requirements and confirm you are ready.</p>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center gap-3 py-6">
            <Loader2 className="w-5 h-5 text-[#0F766E] animate-spin" />
            <p className="text-sm text-slate-500">Loading viva details…</p>
          </div>
        )}

        {/* Error */}
        {!loading && loadError && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <div>
              <p className="text-xs font-bold text-rose-800">Unable to load viva</p>
              <p className="text-xs text-rose-700 mt-0.5">{loadError}</p>
            </div>
          </div>
        )}

        {!loading && warningLimitReached && (
          <div role="alert" className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <div>
              <p className="text-xs font-bold text-rose-800">Viva unavailable</p>
              <p className="text-xs text-rose-700 mt-0.5">
                You have reached your warning limit. You cannot give the viva now.
              </p>
            </div>
          </div>
        )}

        {/* Viva summary */}
        {!loading && !loadError && !warningLimitReached && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
            <h2 className="text-xs font-bold text-slate-700 uppercase tracking-widest flex items-center gap-2">
              <BookOpen className="w-3.5 h-3.5 text-[#0F766E]" /> Examination Details
            </h2>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                { label: 'Subject', value: vivaInfo?.subject || '—' },
                { label: 'Course', value: vivaInfo?.course_code || '—' },
                { label: 'Topic', value: vivaInfo?.topic || '—' },
                { label: 'Questions', value: questionCount !== null ? `${questionCount} questions` : '—' },
                { label: 'Duration', value: vivaInfo?.duration_minutes ? `~${vivaInfo.duration_minutes} minutes` : '—' },
                { label: 'Batch', value: vivaInfo?.batch || '—' },
              ].map(({ label, value }) => (
                <div key={label} className="p-2.5 bg-white rounded-xl border border-slate-100">
                  <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wide">{label}</p>
                  <p className="text-slate-900 font-semibold mt-0.5 truncate">{value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {!loading && !loadError && !warningLimitReached && (
          <div className="space-y-2.5">
            <h2 className="text-xs font-bold text-slate-700 uppercase tracking-widest">Instructions</h2>
            {[
              { icon: <Mic className="w-4 h-4 text-[#0F766E]" />, text: 'Each question will be read aloud by the AI examiner. Wait for it to finish before recording.' },
              { icon: <Volume2 className="w-4 h-4 text-[#0F766E]" />, text: 'You may replay the question at any time using the "Repeat Question" button.' },
              { icon: <Clock className="w-4 h-4 text-amber-500" />, text: `You have up to 2 minutes to record your answer for each question.` },
              { icon: <CheckCircle2 className="w-4 h-4 text-[#0F766E]" />, text: 'After stopping the recording, review your transcript then click "Submit Answer".' },
              { icon: <ShieldCheck className="w-4 h-4 text-[#0F766E]" />, text: 'Your answers are submitted directly to the backend for AI evaluation and faculty review.' },
              { icon: <AlertCircle className="w-4 h-4 text-rose-500" />, text: 'Do not close or refresh the page once the viva has started — your progress is auto-saved.' },
              { icon: <AlertCircle className="w-4 h-4 text-rose-500" />, text: 'Do not switch tabs. Each incident counts as one warning; the fourth warning ends the viva.' },
              { icon: <Video className="w-4 h-4 text-[#0F766E]" />, text: 'In-browser camera checks look for additional people, cell phones, books, and laptops. Paper or tablets may not be detected reliably.' },
            ].map(({ icon, text }, i) => (
              <div key={i} className="flex items-start gap-3 text-xs text-slate-600">
                <span className="shrink-0 mt-0.5">{icon}</span>
                <span>{text}</span>
              </div>
            ))}
          </div>
        )}

        {/* Pre-flight checks */}
        {!loading && !loadError && !warningLimitReached && (
          <div className="space-y-3">
            <h2 className="text-xs font-bold text-slate-700 uppercase tracking-widest">Pre-flight Checks</h2>

            {/* Mic/camera test */}
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                  <Video className="w-4 h-4 text-[#0F766E]" />
                  Camera &amp; Microphone
                  {permTested && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                </div>
                <button
                  onClick={testPermissions}
                  className={`px-3 py-1.5 text-[11px] font-bold rounded-xl border transition-all ${
                    permTested
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                      : 'bg-[#0F766E] text-white border-[#0F766E] hover:bg-[#0D645D]'
                  }`}
                >
                  {permTested ? '✓ Verified' : 'Test Access'}
                </button>
              </div>
              {permError && (
                <p className="text-[11px] text-rose-600 font-medium">{permError}</p>
              )}
              {!permTested && !permError && (
                <p className="text-[11px] text-slate-400">Click "Test Access" to verify your camera and microphone work before starting.</p>
              )}
            </div>

            {/* Mic ready checkbox */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <div
                onClick={() => setMicChecked(p => !p)}
                className={`w-5 h-5 rounded-lg border-2 flex items-center justify-center shrink-0 mt-0.5 transition-all ${
                  micChecked ? 'bg-[#0F766E] border-[#0F766E]' : 'border-slate-300 group-hover:border-[#0F766E]'
                }`}
              >
                {micChecked && <CheckCircle2 className="w-3 h-3 text-white" />}
              </div>
              <span className="text-xs text-slate-700">
                I am in a quiet environment and my microphone is working correctly.
              </span>
            </label>

            {/* Ready checkbox */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <div
                onClick={() => setReadyChecked(p => !p)}
                className={`w-5 h-5 rounded-lg border-2 flex items-center justify-center shrink-0 mt-0.5 transition-all ${
                  readyChecked ? 'bg-[#0F766E] border-[#0F766E]' : 'border-slate-300 group-hover:border-[#0F766E]'
                }`}
              >
                {readyChecked && <CheckCircle2 className="w-3 h-3 text-white" />}
              </div>
              <span className="text-xs text-slate-700">
                I have read the instructions above and I am ready to begin my viva examination.
              </span>
            </label>
          </div>
        )}

        {/* Begin button */}
        {!loading && !loadError && !warningLimitReached && (
          <button
            onClick={handleBeginViva}
            disabled={!canBegin}
            className="w-full py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-sm rounded-2xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Begin Viva Examination <ArrowRight className="w-4 h-4" />
          </button>
        )}

        {!canBegin && !loading && !loadError && !warningLimitReached && (
          <p className="text-center text-[11px] text-slate-400">
            Please complete all pre-flight checks before beginning.
          </p>
        )}

      </div>
    </div>
  );
}
