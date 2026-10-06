import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getApiUrl, getAuthHeaders } from '../../services/api';
import {
  Mic, MicOff, Video, VideoOff, Volume2, Play, Pause, Square,
  Clock, HelpCircle, BarChart2, Award, CheckCircle2, ShieldCheck,
  ChevronRight, Loader2, AlertCircle, RefreshCw, XCircle, Eye
} from 'lucide-react';
import { facialExpressionAnalyzer } from '../../services/facialExpressionAnalyzer';

// ---------------------------------------------------------------------------
// VIVA STATE MACHINE
// LOADING       — fetching questions from backend
// LOAD_ERROR    — fetch failed
// AI_SPEAKING   — TTS is reading the question aloud
// LISTENING     — question read; awaiting student to start recording
// RECORDING     — student is recording
// PAUSED        — recording paused
// PROCESSING    — STT transcription in progress
// TRANSCRIPT_READY — transcript available; student can review & submit
// SUBMITTING    — POST /api/evaluation/submit in flight
// SUBMIT_ERROR  — submission failed; allow retry
// NEXT_LOADING  — brief transition before next question
// VIVA_COMPLETE — all questions answered
// ---------------------------------------------------------------------------

const VIVA_STORAGE_KEY = 'autoviva_progress'; // localStorage key
const VIDEO_FRAME_STYLE = {
  height: 'clamp(180px, 24vh, 220px)',
  width: 'min(100%, calc(clamp(180px, 24vh, 220px) * 16 / 9))',
};

// Helpers
const formatTime = (secs) => {
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

const getUserFromStorage = () => {
  try { return JSON.parse(localStorage.getItem('autoviva_user') || '{}'); } catch { return {}; }
};

// Build a rubric array that the backend EvaluateAnswerRequest expects.
// Question objects may store rubric as `evaluation_rubric` (list of {criterion, marks})
// or `rubric` (list of {criterion, marks}) — handle both.
const extractRubric = (question) => {
  const raw = (question.evaluation_rubric && question.evaluation_rubric.length > 0)
    ? question.evaluation_rubric
    : (question.rubric && question.rubric.length > 0)
      ? question.rubric
      : [];

  if (raw.length > 0) {
    return raw.map(r => ({ criterion: r.criterion || r.criterion_text || '', marks: parseFloat(r.marks || r.allocated_marks || 3) }));
  }

  // Fallback: generic 3-criterion rubric derived from question topic
  const topic = question.topic || 'the concept';
  return [
    { criterion: `Understanding of ${topic}`, marks: 3.0 },
    { criterion: 'Accurate explanation of key mechanisms', marks: 4.0 },
    { criterion: 'Reasoning and supporting detail', marks: 3.0 },
  ];
};

// ---------------------------------------------------------------------------
// TALKING AVATAR COMPONENT
// ---------------------------------------------------------------------------
function TalkingAvatar({ isSpeaking, examinerState }) {
  const bars = [0.45, 0.7, 1.0, 0.85, 0.6, 0.9, 0.5, 0.75, 0.4, 0.65, 0.95, 0.55];

  const stateLabel = {
    AI_SPEAKING: 'Speaking…',
    LISTENING: 'Listening',
    RECORDING: null,
    PAUSED: null,
    PROCESSING: 'Processing…',
    SUBMITTING: 'Evaluating…',
    NEXT_LOADING: 'Next Question…',
    TRANSCRIPT_READY: 'Awaiting Response',
    SUBMIT_ERROR: 'Please Retry',
    VIVA_COMPLETE: 'Viva Complete',
  }[examinerState] ?? 'Idle';

  return (
    <div style={VIDEO_FRAME_STYLE} className={`rounded-2xl overflow-hidden bg-slate-800 flex items-center justify-center relative shadow-inner select-none ${
      isSpeaking ? 'ring-4 ring-[#0F766E]/40' : ''
    }`}>
      <img
        src="/professor_avatar.jpg"
        alt="AI Examiner"
        className="w-full h-full object-cover object-top"
        onError={(e) => { e.target.style.display = 'none'; }}
      />

      {/* Speaking overlay — animated mouth bars */}
      <div
        className={`absolute bottom-0 left-0 right-0 flex flex-col items-center pb-3 pointer-events-none transition-opacity duration-300 ${
          isSpeaking ? 'opacity-100' : 'opacity-0'
        }`}
        aria-hidden="true"
      >
        <div className="flex items-end gap-[3px] px-4 py-2 bg-black/50 backdrop-blur-sm rounded-full border border-white/10 shadow-lg">
          {bars.map((base, i) => (
            <span
              key={i}
              className="inline-block w-[3px] rounded-full bg-[#34D399]"
              style={{
                height: isSpeaking ? `${Math.round(base * 16) + 4}px` : '4px',
                animation: isSpeaking
                  ? `talkBar ${0.32 + (i % 4) * 0.07}s ease-in-out ${(i * 0.04).toFixed(2)}s infinite alternate`
                  : 'none',
                transition: 'height 0.1s ease',
              }}
            />
          ))}
        </div>
      </div>

      {/* Idle / state label pill */}
      {!isSpeaking && stateLabel && (
        <div className="absolute bottom-0 left-0 right-0 flex justify-center pb-2.5 pointer-events-none">
          <span className={`px-3 py-1 rounded-full text-[10px] font-semibold tracking-wide uppercase backdrop-blur-sm border ${
            examinerState === 'RECORDING'
              ? 'bg-rose-900/60 text-rose-200 border-rose-400/20'
              : examinerState === 'PROCESSING' || examinerState === 'SUBMITTING'
              ? 'bg-slate-900/60 text-slate-300 border-slate-500/20'
              : examinerState === 'VIVA_COMPLETE'
              ? 'bg-emerald-900/60 text-emerald-200 border-emerald-400/20'
              : 'bg-black/40 text-white/70 border-white/10'
          }`}>
            {stateLabel}
          </span>
        </div>
      )}

      {/* Pulsing border while speaking */}
      {isSpeaking && (
        <div className="absolute inset-0 border-4 border-[#0F766E]/50 rounded-2xl pointer-events-none animate-pulse" />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// VIVA COMPLETE SCREEN
// ---------------------------------------------------------------------------
function VivaCompleteScreen({ vivaInfo, submittedCount, totalCount, completedAt, onReturn }) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-lg w-full bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 space-y-6 text-center">
        <div className="w-16 h-16 rounded-full bg-emerald-100 border-2 border-emerald-300 flex items-center justify-center mx-auto">
          <CheckCircle2 className="w-8 h-8 text-[#0F766E]" />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Viva Examination Complete
          </h2>
          <p className="text-sm text-slate-500">
            Your responses have been submitted for evaluation and faculty review.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-left">
          {[
            { label: 'Subject', value: vivaInfo?.subject || '—' },
            { label: 'Course', value: vivaInfo?.course_code || '—' },
            { label: 'Questions Attempted', value: `${submittedCount} / ${totalCount}` },
            { label: 'Status', value: submittedCount === totalCount ? 'All Submitted' : 'Partial Submission' },
          ].map(({ label, value }) => (
            <div key={label} className="p-3 bg-slate-50 rounded-2xl border border-slate-100">
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold mb-0.5">{label}</p>
              <p className="text-xs font-bold text-slate-900">{value}</p>
            </div>
          ))}
        </div>

        {completedAt && (
          <p className="text-[11px] text-slate-400">
            Completed at {new Date(completedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}

        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-800 text-left">
          <strong>Note:</strong> Results will be reviewed by your faculty and made available after assessment is complete. Do not close this session until all answers are confirmed submitted.
        </div>

        <button
          onClick={onReturn}
          className="w-full py-3 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-sm rounded-2xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2"
        >
          Back to Student Dashboard
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// MAIN COMPONENT
// ---------------------------------------------------------------------------
export default function LiveVivaSession() {
  const navigate = useNavigate();
  const location = useLocation();

  // --- Viva session metadata from URL ---
  const searchParams = new URLSearchParams(location.search);
  const vivaId = searchParams.get('viva_id') || '';
  const user = getUserFromStorage();
  const studentId = user.user_id || 'std_anonymous';

  // --- Questions ---
  const [questions, setQuestions] = useState([]);
  const [vivaInfo, setVivaInfo] = useState(null);
  const [vivaState, setVivaState] = useState('LOADING'); // top-level state machine
  const [loadError, setLoadError] = useState('');

  // --- Progress ---
  const [currentIdx, setCurrentIdx] = useState(0);
  const [submittedIds, setSubmittedIds] = useState({}); // { question_id: eval_id }
  const [completedAt, setCompletedAt] = useState(null);

  // --- Recording ---
  const videoRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const utteranceRef = useRef(null);
  const ttsGenerationRef = useRef(0);
  const isRecordingRef = useRef(false);
  const isPausedRef = useRef(false);
  const liveTranscriptRef = useRef('');
  const vivaStateRef = useRef('LOADING');
  const stopInFlightRef = useRef(false);

  const [permissionGranted, setPermissionGranted] = useState(false);
  const [permissionError, setPermissionError] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordTimer, setRecordTimer] = useState(120);
  const [micVolume, setMicVolume] = useState(30);

  // --- Transcript ---
  const [liveTranscript, setLiveTranscript] = useState('');
  const [isProcessingSTT, setIsProcessingSTT] = useState(false);

  // --- Submission ---
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const submissionInFlightRef = useRef(false);

  // --- Timers ---
  const [elapsedTimer, setElapsedTimer] = useState(0);

  // --- Facial analysis ---
  const [facialAnalysis, setFacialAnalysis] = useState({
    state: 'LOADING', displayLabel: 'Loading analysis…', confidence: 0, faceDetected: false,
  });

  // examinerState drives avatar display separately from vivaState
  const isSpeaking = vivaState === 'AI_SPEAKING';
  vivaStateRef.current = vivaState;

  const setTranscript = (text) => {
    const next = text || '';
    liveTranscriptRef.current = next;
    setLiveTranscript(next);
  };

  // ---------------------------------------------------------------------------
  // PERSISTENCE HELPERS
  // ---------------------------------------------------------------------------
  const persistenceKey = `${VIVA_STORAGE_KEY}_${vivaId}_${studentId}`;

  const saveProgress = useCallback((idx, submitted, completedTimestamp) => {
    try {
      localStorage.setItem(persistenceKey, JSON.stringify({
        currentIdx: idx,
        submittedIds: submitted,
        completedAt: completedTimestamp,
        savedAt: Date.now(),
      }));
    } catch (_) {}
  }, [persistenceKey]);

  const loadProgress = useCallback(() => {
    try {
      const raw = localStorage.getItem(persistenceKey);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (_) { return null; }
  }, [persistenceKey]);

  const clearProgress = useCallback(() => {
    try { localStorage.removeItem(persistenceKey); } catch (_) {}
  }, [persistenceKey]);

  // ---------------------------------------------------------------------------
  // FETCH QUESTIONS ON MOUNT — restore progress if available
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const fetchQuestions = async () => {
      setVivaState('LOADING');
      setLoadError('');
      try {
        const url = vivaId
          ? getApiUrl(`/api/viva/active-questions?viva_id=${encodeURIComponent(vivaId)}`)
          : getApiUrl('/api/viva/active-questions');

        const res = await fetch(url, { headers: getAuthHeaders() });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${res.status}`);
        }
        const data = await res.json();
        if (!Array.isArray(data) || data.length === 0) {
          throw new Error(
            'No approved questions found for this viva. The faculty may not have published it yet.'
          );
        }
        setQuestions(data);

        // Load viva metadata for the completion screen
        if (vivaId) {
          try {
            const vRes = await fetch(getApiUrl(`/api/viva/session/${vivaId}`), { headers: getAuthHeaders() });
            if (vRes.ok) setVivaInfo(await vRes.json());
          } catch (_) {}
        }

        // Restore prior progress if still valid
        const saved = loadProgress();
        let resumeIdx = 0;
        let resumeSubmitted = {};
        let resumeCompleted = null;

        if (saved && saved.savedAt && Date.now() - saved.savedAt < 3 * 60 * 60 * 1000) {
          resumeIdx = Math.min(saved.currentIdx || 0, data.length - 1);
          resumeSubmitted = saved.submittedIds || {};
          resumeCompleted = saved.completedAt || null;
        }

        setCurrentIdx(resumeIdx);
        setSubmittedIds(resumeSubmitted);

        if (resumeCompleted) {
          setCompletedAt(resumeCompleted);
          setVivaState('VIVA_COMPLETE');
        } else {
          // TTS effect will move this to AI_SPEAKING as soon as questions are set
          setVivaState('LISTENING');
        }
      } catch (e) {
        setLoadError(e.message || 'Failed to load viva questions.');
        setVivaState('LOAD_ERROR');
      }
    };

    fetchQuestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------------------------------------------------------------------
  // MEDIA PERMISSIONS
  // ---------------------------------------------------------------------------
  const requestMediaPermissions = useCallback(async () => {
    setPermissionError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      mediaStreamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setPermissionGranted(true);
    } catch (err) {
      const msg = err.name === 'NotAllowedError'
        ? 'Camera/microphone access denied. Please allow access in your browser settings and refresh.'
        : `Media error: ${err.message}`;
      setPermissionError(msg);
      setPermissionGranted(false);
    }
  }, []);

  useEffect(() => {
    requestMediaPermissions();
    return () => {
      if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach(t => t.stop());
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    };
  }, [requestMediaPermissions]);

  // ---------------------------------------------------------------------------
  // FACIAL EXPRESSION ANALYSIS
  // ---------------------------------------------------------------------------
  useEffect(() => {
    let animFrameId = null;
    let active = true;

    const run = async () => {
      if (!permissionGranted || !videoRef.current) return;
      const loaded = await facialExpressionAnalyzer.initialize();
      if (!loaded || !active) {
        setFacialAnalysis({ state: 'MODEL_UNAVAILABLE', displayLabel: 'Analysis unavailable', confidence: 0, faceDetected: false });
        return;
      }
      const loop = (ts) => {
        if (!active) return;
        if (videoRef.current && videoRef.current.readyState >= 2) {
          const result = facialExpressionAnalyzer.analyzeVideoFrame(videoRef.current, ts);
          if (result && active) setFacialAnalysis(result);
        }
        animFrameId = requestAnimationFrame(loop);
      };
      animFrameId = requestAnimationFrame(loop);
    };

    if (permissionGranted) run();
    return () => { active = false; if (animFrameId) cancelAnimationFrame(animFrameId); };
  }, [permissionGranted]);

  // ---------------------------------------------------------------------------
  // TIMERS
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (vivaState === 'VIVA_COMPLETE' || vivaState === 'LOADING' || vivaState === 'LOAD_ERROR') return;
    const id = setInterval(() => setElapsedTimer(p => p + 1), 1000);
    return () => clearInterval(id);
  }, [vivaState]);

  useEffect(() => {
    if (!isRecording || isPaused) return;
    if (recordTimer <= 0) { handleStopRecording(); return; }
    const id = setInterval(() => {
      setRecordTimer(p => p - 1);
      setMicVolume(Math.floor(25 + Math.random() * 65));
    }, 1000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRecording, isPaused, recordTimer]);

  // ---------------------------------------------------------------------------
  // TTS — SPEAK QUESTION
  // ---------------------------------------------------------------------------
  const finishSpeaking = useCallback((generation) => {
    if (generation !== ttsGenerationRef.current) return;
    const blocked = ['RECORDING', 'PAUSED', 'PROCESSING', 'SUBMITTING', 'NEXT_LOADING', 'VIVA_COMPLETE', 'LOAD_ERROR', 'LOADING'];
    if (blocked.includes(vivaStateRef.current)) return;
    setVivaState('LISTENING');
  }, []);

  const speakQuestion = useCallback((text) => {
    if (!text) {
      setVivaState('LISTENING');
      return;
    }
    if (['RECORDING', 'PAUSED', 'PROCESSING', 'SUBMITTING', 'VIVA_COMPLETE'].includes(vivaStateRef.current)) {
      return;
    }

    const generation = ttsGenerationRef.current + 1;
    ttsGenerationRef.current = generation;
    setVivaState('AI_SPEAKING');

    if ('speechSynthesis' in window) {
      try { window.speechSynthesis.cancel(); } catch (_) {}
      const utt = new SpeechSynthesisUtterance(text);
      utteranceRef.current = utt;
      utt.rate = 0.92;
      utt.pitch = 1.0;
      utt.onend = () => finishSpeaking(generation);
      utt.onerror = () => finishSpeaking(generation);
      try {
        window.speechSynthesis.speak(utt);
      } catch (_) {
        finishSpeaking(generation);
      }
      const fallbackMs = Math.min(45000, Math.max(5000, text.split(/\s+/).length * 380 + 1500));
      setTimeout(() => finishSpeaking(generation), fallbackMs);
    } else {
      setTimeout(() => finishSpeaking(generation), 2800);
    }
  }, [finishSpeaking]);

  useEffect(() => {
    if (vivaState !== 'AI_SPEAKING' || !('speechSynthesis' in window)) return;
    const id = setInterval(() => {
      try {
        if (window.speechSynthesis.speaking && window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
        }
      } catch (_) {}
    }, 4000);
    return () => clearInterval(id);
  }, [vivaState]);

  useEffect(() => {
    if (!questions.length) return;
    if (vivaStateRef.current === 'VIVA_COMPLETE') return;
    const q = questions[currentIdx];
    if (q?.question_text) speakQuestion(q.question_text);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentIdx, questions]);

  // ---------------------------------------------------------------------------
  // RECORDING
  // ---------------------------------------------------------------------------
  const pickAudioMimeType = () => {
    if (typeof MediaRecorder === 'undefined' || !MediaRecorder.isTypeSupported) return '';
    const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];
    return candidates.find((t) => MediaRecorder.isTypeSupported(t)) || '';
  };

  const handleStartRecording = () => {
    if (!permissionGranted || !mediaStreamRef.current) {
      setPermissionError('Please grant camera and microphone permissions to record your answer.');
      return;
    }
    if (stopInFlightRef.current) return;

    ttsGenerationRef.current += 1;
    try { window.speechSynthesis?.cancel(); } catch (_) {}

    setVivaState('RECORDING');
    isRecordingRef.current = true;
    isPausedRef.current = false;
    setIsRecording(true);
    setIsPaused(false);
    setRecordTimer(120);
    setTranscript('');
    setSubmitError('');
    audioChunksRef.current = [];

    try {
      const audioTracks = mediaStreamRef.current.getAudioTracks().filter((t) => t.enabled && t.readyState === 'live');
      if (!audioTracks.length) {
        throw new Error('No live microphone track');
      }
      const audioStream = new MediaStream(audioTracks);
      const mimeType = pickAudioMimeType();
      const recorder = mimeType
        ? new MediaRecorder(audioStream, { mimeType })
        : new MediaRecorder(audioStream);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      recorder.start(250);
    } catch (e) {
      isRecordingRef.current = false;
      setVivaState('LISTENING');
      setIsRecording(false);
      setPermissionError('Could not start recording. Check microphone permissions.');
      return;
    }

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
      const rec = new SpeechRec();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';
      rec.onresult = (ev) => {
        let t = '';
        for (let i = 0; i < ev.results.length; i++) {
          t += ev.results[i][0].transcript + ' ';
        }
        setTranscript(t.trim());
      };
      rec.onerror = (err) => {
        console.debug('Speech recognition error:', err.error);
      };
      rec.onend = () => {
        if (isRecordingRef.current && !isPausedRef.current) {
          try { rec.start(); } catch (_) {}
        }
      };
      try { rec.start(); } catch (_) {}
      recognitionRef.current = rec;
    }
  };

  const handlePauseResume = () => {
    if (!isRecordingRef.current) return;
    if (isPausedRef.current) {
      mediaRecorderRef.current?.resume?.();
      try { recognitionRef.current?.start?.(); } catch (_) {}
      isPausedRef.current = false;
      setIsPaused(false);
      setVivaState('RECORDING');
    } else {
      mediaRecorderRef.current?.pause?.();
      try { recognitionRef.current?.stop(); } catch (_) {}
      isPausedRef.current = true;
      setIsPaused(true);
      setVivaState('PAUSED');
    }
  };

  const transcribeRecording = async (mimeType) => {
    const type = mimeType || 'audio/webm';
    const blob = new Blob(audioChunksRef.current, { type });
    const browserTranscript = (liveTranscriptRef.current || '').trim();

    if (blob.size < 50) {
      if (browserTranscript) return browserTranscript;
      throw new Error('The recording was too short to transcribe. Please re-record your answer.');
    }

    try {
      const form = new FormData();
      const ext = type.includes('mp4') ? 'mp4' : 'webm';
      form.append('file', blob, `answer.${ext}`);

      const res = await fetch(getApiUrl('/api/viva/transcribe'), {
        method: 'POST',
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Transcription failed (${res.status}).`);
      }

      const d = await res.json();
      const serverText = (d.transcript || '').trim();
      if (serverText) return serverText;
      if (browserTranscript) return browserTranscript;
      throw new Error('No speech was detected. Please re-record or type your answer below.');
    } catch (error) {
      if (browserTranscript) return browserTranscript;
      throw error;
    }
  };

  const handleStopRecording = useCallback(() => {
    if (!isRecordingRef.current || stopInFlightRef.current) return;
    stopInFlightRef.current = true;
    isRecordingRef.current = false;
    isPausedRef.current = false;
    setIsRecording(false);
    setIsPaused(false);
    setVivaState('PROCESSING');
    setIsProcessingSTT(true);

    try { recognitionRef.current?.stop(); } catch (_) {}

    const recorder = mediaRecorderRef.current;
    const mimeType = recorder?.mimeType || '';
    let finished = false;

    const finish = async () => {
      if (finished) return;
      finished = true;
      try {
        const text = await transcribeRecording(mimeType);
        setTranscript(text);
        if (!text) {
          setSubmitError('No speech was detected. Please re-record or type your answer in the box below.');
        } else {
          setSubmitError('');
        }
      } catch (_) {
        setSubmitError(_.message || 'Transcription failed. You can type your answer in the box below, then submit.');
      } finally {
        setIsProcessingSTT(false);
        setVivaState('TRANSCRIPT_READY');
        stopInFlightRef.current = false;
      }
    };

    if (recorder && recorder.state !== 'inactive') {
      recorder.onstop = () => { finish(); };
      try {
        recorder.requestData?.();
        recorder.stop();
      } catch (_) {
        finish();
      }
      setTimeout(() => {
        if (vivaStateRef.current === 'PROCESSING') finish();
      }, 2500);
    } else {
      finish();
    }
  }, []);

  // ---------------------------------------------------------------------------
  // ANSWER SUBMISSION
  // ---------------------------------------------------------------------------
  const handleSubmitAnswer = async () => {
    if (submissionInFlightRef.current) return;

    const answer = liveTranscriptRef.current ?? liveTranscript;
    if (!answer.trim()) {
      setSubmitError('Please record or type an answer before submitting. Your answer is empty.');
      return;
    }

    const question = questions[currentIdx];
    if (!question) return;

    const rubric = extractRubric(question);
    const isLastQuestion = currentIdx >= questions.length - 1;

    submissionInFlightRef.current = true;
    setIsSubmitting(true);
    setSubmitError('');
    setVivaState('SUBMITTING');

    try {
      const payload = {
        question_text: question.question_text,
        ideal_answer: (question.ideal_answer || question.question_text || '').trim(),
        evaluation_rubric: rubric,
        student_answer: answer,
        subject: question.subject || vivaInfo?.subject || 'General',
        topic: question.topic || vivaInfo?.topic || 'General',
        question_id: question.question_id || '',
        student_id: studentId,
        viva_id: vivaId || '',
      };

      const res = await fetch(getApiUrl('/api/evaluation/submit'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let detail = err.detail;
        if (Array.isArray(detail)) {
          detail = detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
        }
        throw new Error(detail || `Submission failed (${res.status})`);
      }

      const evalRecord = await res.json();
      const evalId = evalRecord?.evaluation_id;
      if (typeof evalId !== 'string' || !evalId.trim()) {
        throw new Error('Evaluation completed without a valid evaluation record. Please retry submission.');
      }

      const updatedSubmitted = { ...submittedIds, [question.question_id || currentIdx]: evalId };
      setSubmittedIds(updatedSubmitted);

      if (isLastQuestion) {
        const ts = new Date().toISOString();
        setCompletedAt(ts);
        saveProgress(currentIdx, updatedSubmitted, ts);
        try {
          const completedVivas = JSON.parse(localStorage.getItem('autoviva_completed') || '{}');
          completedVivas[vivaId] = { completedAt: ts, submittedCount: Object.keys(updatedSubmitted).length };
          localStorage.setItem('autoviva_completed', JSON.stringify(completedVivas));
        } catch (_) {}
        try { window.speechSynthesis?.cancel(); } catch (_) {}
        setVivaState('VIVA_COMPLETE');
      } else {
        saveProgress(currentIdx + 1, updatedSubmitted, null);
        setTranscript('');
        setSubmitError('');
        ttsGenerationRef.current += 1;
        try { window.speechSynthesis?.cancel(); } catch (_) {}
        setVivaState('NEXT_LOADING');
        setTimeout(() => {
          setCurrentIdx((prev) => prev + 1);
          setRecordTimer(120);
        }, 700);
      }
    } catch (e) {
      setSubmitError(e.message || 'Answer could not be submitted. Please try again.');
      setVivaState('SUBMIT_ERROR');
    } finally {
      submissionInFlightRef.current = false;
      setIsSubmitting(false);
    }
  };

  const handleRepeatQuestion = () => {
    if (isRecordingRef.current || isSubmitting) return;
    if (questions[currentIdx]) speakQuestion(questions[currentIdx].question_text);
  };

  const handleRetryRecord = () => {
    setTranscript('');
    setSubmitError('');
    setVivaState('LISTENING');
  };

  // ---------------------------------------------------------------------------
  // RENDER — LOADING / ERROR
  // ---------------------------------------------------------------------------
  if (vivaState === 'LOADING') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
        <Loader2 className="w-8 h-8 text-[#0F766E] animate-spin" />
        <p className="text-slate-600 text-sm font-medium">Loading your viva questions…</p>
      </div>
    );
  }

  if (vivaState === 'LOAD_ERROR') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
        <AlertCircle className="w-8 h-8 text-rose-500" />
        <p className="text-slate-800 font-bold text-sm">Unable to load questions</p>
        <p className="text-slate-500 text-xs max-w-md">{loadError}</p>
        <button
          onClick={() => navigate('/student/dashboard')}
          className="mt-2 px-5 py-2 bg-[#0F766E] text-white text-xs font-bold rounded-xl hover:bg-[#0D645D]"
        >
          ← Back to Dashboard
        </button>
      </div>
    );
  }

  if (vivaState === 'VIVA_COMPLETE') {
    return (
      <div className="flex-1 flex flex-col bg-[#F8FAFC]">
        <VivaCompleteScreen
          vivaInfo={vivaInfo}
          submittedCount={Object.keys(submittedIds).length}
          totalCount={questions.length}
          completedAt={completedAt}
          onReturn={() => navigate('/student/dashboard')}
        />
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // RENDER — LIVE VIVA
  // ---------------------------------------------------------------------------
  const activeQ = questions[currentIdx] || questions[0];
  const isLastQuestion = currentIdx >= questions.length - 1;
  const alreadySubmittedThisQ = !!submittedIds[activeQ?.question_id || currentIdx];
  const submittedCount = Object.keys(submittedIds).length;
  const progressPct = questions.length > 0 ? Math.round((submittedCount / questions.length) * 100) : 0;

  const canRecord = ['LISTENING', 'AI_SPEAKING', 'TRANSCRIPT_READY', 'SUBMIT_ERROR'].includes(vivaState) && permissionGranted && !isRecording;
  const canSubmit = ['TRANSCRIPT_READY', 'SUBMIT_ERROR', 'LISTENING'].includes(vivaState) && liveTranscript.trim().length > 0 && !isSubmitting;
  const canEditAnswer = ['TRANSCRIPT_READY', 'SUBMIT_ERROR', 'LISTENING'].includes(vivaState);
  const showTranscript = ['TRANSCRIPT_READY', 'SUBMITTING', 'SUBMIT_ERROR', 'NEXT_LOADING'].includes(vivaState)
    || (vivaState === 'RECORDING' && liveTranscript.length > 0)
    || (vivaState === 'PROCESSING');

  return (
    <div className="min-h-[calc(100dvh-4rem)] lg:h-[calc(100dvh-4rem)] lg:min-h-0 w-full bg-[#F8FAFC] text-slate-800 flex flex-col font-sans antialiased lg:overflow-hidden">

      {/* Permission banner */}
      {permissionError && (
        <div className="shrink-0 bg-rose-50 border-b border-rose-200 px-6 py-2 text-rose-700 text-xs font-medium flex items-center justify-between">
          <span className="flex items-center gap-2"><AlertCircle className="w-4 h-4" /> {permissionError}</span>
          <button onClick={requestMediaPermissions} className="px-3 py-1 bg-rose-600 text-white rounded-md text-[11px] font-bold hover:bg-rose-700">
            Retry
          </button>
        </div>
      )}

      <div className="flex-1 min-h-0 w-full max-w-[1700px] mx-auto p-2 grid grid-cols-1 lg:grid-cols-12 gap-2 lg:overflow-hidden">

        {/* ── LEFT COLUMN ──────────────────────────────────────────── */}
        <div className="lg:col-span-9 flex flex-col gap-2 lg:min-h-0 lg:overflow-hidden">

          {/* Progress bar */}
          <div className="shrink-0 flex items-center gap-2 px-0.5">
            <span className="text-[10px] font-bold text-[#0F766E] uppercase tracking-widest whitespace-nowrap">
              Q {currentIdx + 1} / {questions.length}
            </span>
            <div className="flex-1 h-1 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-[#0F766E] rounded-full transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-400 font-mono whitespace-nowrap">{progressPct}%</span>
          </div>

          {/* Avatar + Camera row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 shrink-0">

            {/* Examiner panel */}
            <div className={`p-2 bg-white rounded-2xl border shadow-sm transition-all duration-300 ${
              isSpeaking ? 'border-[#0F766E] ring-2 ring-[#0F766E]/10' : 'border-slate-200/80'
            }`}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">AI Examiner</span>
                <span className={`w-2 h-2 rounded-full ${
                  isSpeaking ? 'bg-[#0F766E] animate-ping' :
                  vivaState === 'RECORDING' ? 'bg-rose-500 animate-pulse' :
                  vivaState === 'SUBMITTING' || vivaState === 'PROCESSING' ? 'bg-amber-400 animate-pulse' :
                  'bg-slate-300'
                }`} />
              </div>
              <div className="w-full flex justify-center">
                <TalkingAvatar isSpeaking={isSpeaking} examinerState={vivaState} />
              </div>
              <button
                onClick={handleRepeatQuestion}
                disabled={vivaState === 'RECORDING' || isSubmitting}
                className="mt-1.5 w-full py-1 text-[10px] font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 flex items-center justify-center gap-1 disabled:opacity-40 transition-colors"
              >
                <Volume2 className="w-3 h-3 text-[#0F766E]" /> Repeat Question
              </button>
            </div>

            {/* Student camera */}
            <div className="p-2 bg-white rounded-2xl border border-slate-200/80 shadow-sm flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Your Camera</span>
                <div className="flex items-center gap-1.5 text-[10px]">
                  <span className={`flex items-center gap-0.5 font-semibold ${permissionGranted ? 'text-emerald-600' : 'text-rose-500'}`}>
                    {permissionGranted ? <Mic className="w-2.5 h-2.5" /> : <MicOff className="w-2.5 h-2.5" />}
                    {permissionGranted ? 'Mic' : 'Off'}
                  </span>
                  <span className={`flex items-center gap-0.5 font-semibold ${permissionGranted ? 'text-emerald-600' : 'text-rose-500'}`}>
                    {permissionGranted ? <Video className="w-2.5 h-2.5" /> : <VideoOff className="w-2.5 h-2.5" />}
                    {permissionGranted ? 'Cam' : 'Off'}
                  </span>
                </div>
              </div>

              <div className="w-full flex justify-center">
                <div style={VIDEO_FRAME_STYLE} className="relative bg-slate-900 rounded-xl overflow-hidden shrink-0">
                  <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover object-center" />
                {!permissionGranted && (
                  <div className="absolute inset-0 bg-slate-800 flex flex-col items-center justify-center gap-1.5">
                    <VideoOff className="w-5 h-5 text-slate-400" />
                    <p className="text-slate-400 text-[10px]">Camera offline</p>
                    <button onClick={requestMediaPermissions} className="px-2 py-1 bg-[#0F766E] text-white text-[10px] font-bold rounded-lg">
                      Enable
                    </button>
                  </div>
                )}
                {permissionGranted && (
                  <div className="absolute top-1.5 left-1.5 right-1.5 flex justify-between items-center px-2 py-1 bg-slate-900/80 backdrop-blur rounded-lg text-[9px] font-semibold text-white border border-white/10">
                    <span className="flex items-center gap-0.5 text-slate-200">
                      <span className="text-sm">🎭</span> {facialAnalysis.displayLabel}
                    </span>
                    {facialAnalysis.faceDetected && facialAnalysis.confidence > 0 && (
                      <span className="text-teal-300 font-mono">{Math.round(facialAnalysis.confidence * 100)}%</span>
                    )}
                  </div>
                )}
                {isRecording && !isPaused && (
                  <div className="absolute bottom-1.5 right-1.5 flex items-center gap-1 px-1.5 py-0.5 bg-rose-600/90 rounded-full text-[9px] font-bold text-white animate-pulse">
                    <span className="w-1 h-1 bg-white rounded-full" /> REC {formatTime(recordTimer)}
                  </div>
                )}
                </div>
              </div>
            </div>
          </div>

          {/* Question card */}
          <div className="shrink-0 p-2 bg-white rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <span className="text-[9px] font-bold text-[#0F766E] uppercase tracking-widest">
                  {activeQ?.subject} · {activeQ?.topic}
                </span>
                <h2 className="text-xs font-bold text-slate-900 leading-snug mt-0.5">
                  "{activeQ?.question_text}"
                </h2>
              </div>
              {alreadySubmittedThisQ && (
                <span className="shrink-0 flex items-center gap-0.5 text-[9px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                  <CheckCircle2 className="w-2.5 h-2.5" /> Submitted
                </span>
              )}
            </div>
          </div>

          {/* Transcript + Controls */}
          <div className="flex-1 min-h-[230px] lg:min-h-0 flex flex-col p-2 bg-white rounded-2xl border border-slate-200/80 shadow-sm gap-1.5 overflow-hidden">

            {/* Controls row */}
            <div className="shrink-0 flex items-center justify-between gap-1.5 flex-wrap">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-bold text-slate-700">Your Response</span>
                {vivaState === 'RECORDING' && (
                  <span className="flex items-center gap-1 text-[10px] text-rose-600 font-mono font-semibold animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500" /> Recording ({formatTime(recordTimer)})
                  </span>
                )}
                {vivaState === 'PROCESSING' && (
                  <span className="flex items-center gap-0.5 text-[10px] text-amber-600 font-medium">
                    <Loader2 className="w-2.5 h-2.5 animate-spin" /> Processing audio…
                  </span>
                )}
              </div>

              <div className="flex items-center gap-1.5">
                {/* Start recording */}
                {canRecord && !isRecording && (
                  <button
                    onClick={handleStartRecording}
                    className="px-3 py-1.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-lg flex items-center gap-1 shadow-sm transition-all"
                  >
                    <Play className="w-3 h-3 fill-current" /> Start Recording
                  </button>
                )}

                {/* Pause/Resume */}
                {isRecording && (
                  <button
                    onClick={handlePauseResume}
                    className="px-2 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 flex items-center gap-1"
                  >
                    {isPaused
                      ? <><Play className="w-3 h-3 text-[#0F766E] fill-current" /> Resume</>
                      : <><Pause className="w-3 h-3 text-amber-600 fill-current" /> Pause</>
                    }
                  </button>
                )}

                {/* Stop recording */}
                {isRecording && (
                  <button
                    onClick={handleStopRecording}
                    className="px-2 py-1.5 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-lg flex items-center gap-1 shadow-sm transition-all"
                  >
                    <Square className="w-3 h-3 fill-current" /> Stop
                  </button>
                )}

                {/* Retry recording */}
                {vivaState === 'TRANSCRIPT_READY' && (
                  <button
                    onClick={handleRetryRecord}
                    className="px-2 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold rounded-lg border border-slate-200 flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" /> Re-record
                  </button>
                )}
              </div>
            </div>

            {/* Transcript area - HIGHLY VISIBLE */}
            <div className="flex-1 min-h-[72px] bg-gradient-to-br from-[#F8FAFC] to-[#f0f9ff] rounded-xl border-2 border-slate-300 p-2 overflow-y-auto shadow-inner">
              {vivaState === 'PROCESSING' && !liveTranscript ? (
                <div className="flex flex-col items-center justify-center gap-2 h-full text-slate-400 text-xs">
                  <Loader2 className="w-4 h-4 animate-spin text-[#0F766E]" />
                  <p className="font-medium">Transcribing audio…</p>
                  <p className="text-[10px] italic">Please wait while we process your recording.</p>
                </div>
              ) : canEditAnswer ? (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Your Answer
                  </p>
                  <textarea
                    aria-label="Your Answer"
                    value={liveTranscript}
                    onChange={(event) => setTranscript(event.target.value)}
                    placeholder="Review or type your answer here…"
                    className="w-full h-[clamp(64px,10vh,96px)] min-h-[64px] max-h-[96px] resize-none text-xs leading-relaxed text-slate-900 bg-white rounded-lg p-2 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#0F766E]/30"
                  />
                </div>
              ) : liveTranscript ? (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Your Answer
                  </p>
                  <p className="text-xs leading-relaxed whitespace-pre-wrap text-slate-900 bg-white rounded-lg p-2 border border-slate-200">{liveTranscript}</p>
                </div>
              ) : vivaState === 'RECORDING' ? (
                <div className="flex flex-col items-center justify-center gap-2 h-full text-slate-500 text-xs">
                  <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                  <p className="font-medium">Recording… your answer will appear here</p>
                  <p className="text-[10px] italic text-slate-400">Speak naturally and clearly.</p>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center gap-1.5 h-full text-slate-400 text-xs">
                  <Mic className="w-4 h-4 text-[#0F766E] opacity-40" />
                  <p className="font-medium text-center">Your spoken answer will appear here…</p>
                  <p className="text-[10px] italic">Click "Start Recording" to begin.</p>
                </div>
              )}
            </div>

            {/* Mic waveform */}
            {isRecording && (
              <div className="shrink-0 flex items-center gap-1.5">
                <div className="flex items-end gap-1 h-4 px-1.5 bg-slate-100 rounded-md border border-slate-200">
                  {[30, 60, 90, 50, 80, 40, 70].map((v, i) => (
                    <div
                      key={i}
                      className="w-1 rounded-full bg-[#0F766E] animate-pulse"
                      style={{ height: `${Math.max(2, (micVolume * (v / 100)) / 5)}px` }}
                    />
                  ))}
                </div>
                <span className="text-[9px] text-slate-500 font-mono whitespace-nowrap">Mic {micVolume}%</span>
              </div>
            )}

            {/* Error banner */}
            {submitError && (
              <div className="shrink-0 p-2 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-start gap-1.5">
                <XCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-500" />
                <span>{submitError}</span>
              </div>
            )}

            {/* Bottom action bar */}
            <div className="shrink-0 flex items-center justify-between pt-1 border-t border-slate-100">
              <div className="text-[10px] text-slate-400">
                {liveTranscript
                  ? `${liveTranscript.trim().split(/\s+/).length} words recorded`
                  : 'No transcript yet'}
              </div>

              <div className="flex items-center gap-2">
                {/* Submit answer / Submit & Finish */}
                <button
                  onClick={handleSubmitAnswer}
                  disabled={!canSubmit || vivaState === 'NEXT_LOADING'}
                  className={`px-3 py-1.5 font-bold text-xs rounded-lg flex items-center gap-1 shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                    isLastQuestion
                      ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/20'
                      : 'bg-[#0F766E] hover:bg-[#0D645D] text-white shadow-[#0F766E]/20'
                  }`}
                >
                  {isSubmitting ? (
                    <><Loader2 className="w-3 h-3 animate-spin" /> Evaluating…</>
                  ) : vivaState === 'NEXT_LOADING' ? (
                    <><Loader2 className="w-3 h-3 animate-spin" /> Loading next question…</>
                  ) : isLastQuestion ? (
                    <><CheckCircle2 className="w-3 h-3" /> Submit &amp; Finish Viva</>
                  ) : (
                    <>Submit &amp; Next <ChevronRight className="w-3.5 h-3.5" /></>
                  )}
                </button>
              </div>
            </div>

          </div>
        </div>

        {/* ── RIGHT SIDEBAR ─────────────────────────────────────────── */}
        <div className="lg:col-span-3 flex flex-col gap-2 overflow-hidden">
          <div className="flex-1 p-2.5 bg-white rounded-2xl border border-slate-200/80 shadow-sm flex flex-col gap-2.5 overflow-y-auto">

            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-widest border-b border-slate-100 pb-1.5 flex items-center gap-1.5">
              <BarChart2 className="w-3.5 h-3.5 text-[#0F766E]" /> Viva Status
            </h3>

            {/* Stats */}
            {[
              { icon: <Clock className="w-3.5 h-3.5 text-[#0F766E]" />, label: 'Elapsed Time', value: formatTime(elapsedTimer) },
              { icon: <HelpCircle className="w-3.5 h-3.5 text-indigo-500" />, label: 'Question', value: `${currentIdx + 1} / ${questions.length}` },
              { icon: <Award className="w-3.5 h-3.5 text-emerald-500" />, label: 'Submitted', value: `${submittedCount} / ${questions.length}` },
              {
                icon: <Mic className="w-3.5 h-3.5 text-[#0F766E]" />,
                label: 'Microphone',
                value: isRecording ? 'Recording' : permissionGranted ? 'Ready' : 'Offline',
                valueColor: isRecording ? 'text-rose-600' : permissionGranted ? 'text-emerald-600' : 'text-slate-500',
              },
              {
                icon: <Video className="w-3.5 h-3.5 text-[#0F766E]" />,
                label: 'Camera',
                value: permissionGranted ? 'Active' : 'Offline',
                valueColor: permissionGranted ? 'text-emerald-600' : 'text-slate-500',
              },
            ].map(({ icon, label, value, valueColor }) => (
              <div key={label} className="p-2 bg-[#F8FAFC] rounded-lg border border-slate-100 flex justify-between items-center">
                <span className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">{icon} {label}</span>
                <span className={`text-xs font-bold font-mono ${valueColor || 'text-slate-900'}`}>{value}</span>
              </div>
            ))}

            {/* Question progress dots */}
            <div>
              <p className="text-[9px] text-slate-400 uppercase tracking-widest font-bold mb-1.5">Progress</p>
              <div className="flex flex-wrap gap-1">
                {questions.map((q, i) => {
                  const submitted = !!submittedIds[q.question_id || i];
                  const active = i === currentIdx;
                  return (
                    <div
                      key={i}
                      title={`Q${i + 1}: ${submitted ? 'Submitted' : active ? 'Current' : 'Pending'}`}
                      className={`w-6 h-6 rounded-md flex items-center justify-center text-[9px] font-bold border transition-all ${
                        submitted
                          ? 'bg-emerald-100 border-emerald-300 text-emerald-700'
                          : active
                          ? 'bg-[#0F766E] border-[#0F766E] text-white shadow-sm'
                          : 'bg-slate-100 border-slate-200 text-slate-400'
                      }`}
                    >
                      {submitted ? '✓' : i + 1}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Subject info */}
            <div className="mt-auto pt-1.5 border-t border-slate-100 text-center">
              <p className="text-[10px] text-slate-500 font-semibold">{activeQ?.subject}</p>
              {vivaInfo?.batch && (
                <p className="text-[9px] text-slate-400 mt-0.5">{vivaInfo.batch}</p>
              )}
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
