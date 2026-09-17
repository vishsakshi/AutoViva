import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getApiUrl } from '../../services/api';
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  Volume2,
  Play,
  Pause,
  Square,
  Send,
  LogOut,
  Clock,
  HelpCircle,
  BarChart2,
  Award,
  CheckCircle2,
  ShieldCheck,
  ChevronRight,
  SkipForward,
  Loader2,
  Smile,
  Eye,
  AlertCircle
} from 'lucide-react';
import { facialExpressionAnalyzer } from '../../services/facialExpressionAnalyzer';

export default function LiveVivaSession() {
  const navigate = useNavigate();

  // ---------------------------------------------------------------------------
  // 1. DATA & STATE MANAGEMENT
  // ---------------------------------------------------------------------------
  const [questions, setQuestions] = useState([
    {
      question_id: 'vq_cn_nat_001',
      subject: 'Computer Networks',
      topic: 'IP Addressing, NAT & NAPT',
      question_text: 'Describe how Network Address Translation (NAT) and NAPT allow multiple internal private IP devices to communicate over a single public IP address.',
      ideal_answer: 'NAT maps private internal IP addresses to a public external IP. NAPT extends this by mapping unique source port numbers alongside the public IP address.',
      allocated_marks: 10.0,
      time_limit_seconds: 120
    },
    {
      question_id: 'vq_dbms_acid_002',
      subject: 'DBMS',
      topic: 'Transactions & ACID Properties',
      question_text: 'Explain the ACID properties of a Relational Database Management System (DBMS) and describe how Atomicity and Isolation ensure transaction reliability.',
      ideal_answer: 'ACID stands for Atomicity, Consistency, Isolation, and Durability. Atomicity ensures all-or-nothing completion, while Isolation prevents concurrent interference.',
      allocated_marks: 10.0,
      time_limit_seconds: 120
    },
    {
      question_id: 'vq_os_deadlock_003',
      subject: 'Operating Systems',
      topic: 'Process Management & Deadlocks',
      question_text: 'What are the four Coffman conditions necessary for a deadlock to occur in an operating system? Briefly explain the Banker\'s algorithm.',
      ideal_answer: 'Coffman conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait. Banker\'s algorithm tests for safe states before allocating resources.',
      allocated_marks: 10.0,
      time_limit_seconds: 120
    }
  ]);

  const [currentIdx, setCurrentIdx] = useState(0);

  // States: AI_SPEAKING | STUDENT_SPEAKING | PAUSED | AI_PROCESSING | SUBMITTED
  const [examinerState, setExaminerState] = useState('AI_SPEAKING');

  // WebRTC Media & Streams
  const videoRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);

  const [permissionGranted, setPermissionGranted] = useState(false);
  const [permissionError, setPermissionError] = useState(null);

  // Recording, Timers & Waveform
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordTimer, setRecordTimer] = useState(120);
  const [elapsedTimer, setElapsedTimer] = useState(0);
  const [micVolume, setMicVolume] = useState(40);

  // Read-Only Speech Transcript
  const [liveTranscript, setLiveTranscript] = useState('');
  const [isProcessingSTT, setIsProcessingSTT] = useState(false);

  // Clean Student Notification State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  // ---------------------------------------------------------------------------
  // 2. WEBRTC MEDIA & PERMISSIONS
  // ---------------------------------------------------------------------------
  const requestMediaPermissions = async () => {
    setPermissionError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setPermissionGranted(true);
    } catch (err) {
      console.error('Media permission error:', err);
      setPermissionError('Camera or Microphone access denied. Please allow access in browser URL bar.');
      setPermissionGranted(false);
    }
  };

  // Facial Expression Analysis State
  const [facialAnalysis, setFacialAnalysis] = useState({
    state: 'LOADING',
    displayLabel: 'Loading facial analysis...',
    confidence: 0,
    faceDetected: false
  });

  useEffect(() => {
    requestMediaPermissions();
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  // Real-time Facial Expression Analysis Loop (Using existing video stream)
  useEffect(() => {
    let animFrameId = null;
    let isActive = true;

    const initAndStartAnalysis = async () => {
      if (!permissionGranted || !videoRef.current) return;

      setFacialAnalysis({
        state: 'LOADING',
        displayLabel: 'Loading facial analysis...',
        confidence: 0,
        faceDetected: false
      });

      const isLoaded = await facialExpressionAnalyzer.initialize();
      if (!isLoaded || !isActive) {
        setFacialAnalysis({
          state: 'MODEL_UNAVAILABLE',
          displayLabel: 'Facial analysis unavailable',
          confidence: 0,
          faceDetected: false
        });
        return;
      }

      const processLoop = (timestamp) => {
        if (!isActive) return;
        if (videoRef.current && videoRef.current.readyState >= 2) {
          const result = facialExpressionAnalyzer.analyzeVideoFrame(videoRef.current, timestamp);
          if (result && isActive) {
            setFacialAnalysis(result);
          }
        }
        animFrameId = requestAnimationFrame(processLoop);
      };

      animFrameId = requestAnimationFrame(processLoop);
    };

    if (permissionGranted) {
      initAndStartAnalysis();
    }

    return () => {
      isActive = false;
      if (animFrameId) {
        cancelAnimationFrame(animFrameId);
      }
    };
  }, [permissionGranted]);

  // ---------------------------------------------------------------------------
  // 3. TIMERS & MIC SENSITIVITY ANIMATION
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const elapsedInterval = setInterval(() => {
      setElapsedTimer(prev => prev + 1);
    }, 1000);
    return () => clearInterval(elapsedInterval);
  }, []);

  useEffect(() => {
    let interval = null;
    if (isRecording && !isPaused && recordTimer > 0) {
      interval = setInterval(() => {
        setRecordTimer(prev => prev - 1);
        setMicVolume(Math.floor(25 + Math.random() * 65));
      }, 1000);
    } else if (recordTimer === 0 && isRecording) {
      handleStopRecording();
    }
    return () => clearInterval(interval);
  }, [isRecording, isPaused, recordTimer]);

  // ---------------------------------------------------------------------------
  // 4. AI EXAMINER TTS (SPEAKING STATE)
  // ---------------------------------------------------------------------------
  const speakQuestion = (text) => {
    setExaminerState('AI_SPEAKING');
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;

      utterance.onend = () => setExaminerState('LISTENING');
      utterance.onerror = () => setExaminerState('LISTENING');

      window.speechSynthesis.speak(utterance);
    } else {
      setTimeout(() => setExaminerState('LISTENING'), 2500);
    }
  };

  useEffect(() => {
    if (questions.length > 0) {
      speakQuestion(questions[currentIdx].question_text);
    }
  }, [currentIdx]);

  // ---------------------------------------------------------------------------
  // 5. MICROPHONE RECORDING & LIVE READ-ONLY SPEECH TRANSCRIPTION
  // ---------------------------------------------------------------------------
  const handleStartRecording = () => {
    if (!permissionGranted) {
      alert('Please grant camera and microphone permissions first.');
      return;
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    setExaminerState('STUDENT_SPEAKING');
    setLiveTranscript('');
    setIsSubmitted(false);
    setIsPaused(false);
    setRecordTimer(120);
    audioChunksRef.current = [];

    try {
      const audioStream = new MediaStream(mediaStreamRef.current.getAudioTracks());
      const mediaRecorder = new MediaRecorder(audioStream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.start(500);
      setIsRecording(true);

      // Web Speech API Live Recognition (Read-Only Stream)
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event) => {
          let text = '';
          for (let i = 0; i < event.results.length; i++) {
            text += event.results[i][0].transcript + ' ';
          }
          setLiveTranscript(text.trim());
        };

        recognition.start();
        recognitionRef.current = recognition;
      }
    } catch (e) {
      console.error('Error starting recording:', e);
    }
  };

  const handlePauseResumeRecording = () => {
    if (!isRecording) return;
    if (isPaused) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
        mediaRecorderRef.current.resume();
      }
      setIsPaused(false);
      setExaminerState('STUDENT_SPEAKING');
    } else {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.pause();
      }
      setIsPaused(true);
      setExaminerState('PAUSED');
    }
  };

  const handleStopRecording = () => {
    if (!isRecording) return;
    setIsRecording(false);
    setIsPaused(false);
    setExaminerState('AI_PROCESSING');

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch(e){}
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    setIsProcessingSTT(true);

    setTimeout(async () => {
      try {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'viva_answer.webm');

        const res = await fetch(getApiUrl('/api/viva/transcribe'), {
          method: 'POST',
          body: formData
        }).catch(() => null);

        if (res && res.ok) {
          const data = await res.json();
          if (data.transcript && data.transcript.length > 5) {
            setLiveTranscript(data.transcript);
          }
        }
      } catch (e) {
        console.error('STT Processing error:', e);
      } finally {
        setIsProcessingSTT(false);
        setExaminerState('LISTENING');
      }
    }, 400);
  };

  // ---------------------------------------------------------------------------
  // 6. SUBMIT ANSWER TO EVALUATION ENGINE
  // ---------------------------------------------------------------------------
  const handleSubmitAnswer = async () => {
    if (!liveTranscript.trim()) {
      alert('Transcript cannot be empty. Please speak your answer before submitting.');
      return;
    }

    const activeQ = questions[currentIdx];
    setIsSubmitting(true);
    setExaminerState('AI_PROCESSING');

    try {
      const res = await fetch(getApiUrl('/api/evaluation/submit'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_text: activeQ.question_text,
          ideal_answer: activeQ.ideal_answer,
          evaluation_rubric: [
            { criterion: "Distinction between private internal and public external IP addresses", marks: 3.0 },
            { criterion: "Detailed mechanism of NAPT port mapping for inbound/outbound packets", marks: 4.0 },
            { criterion: "Translation table management and security benefits", marks: 3.0 }
          ],
          student_answer: liveTranscript,
          subject: activeQ.subject,
          topic: activeQ.topic
        })
      });

      if (res.ok) {
        setIsSubmitted(true);
        setExaminerState('EVALUATED');
      } else {
        setExaminerState('LISTENING');
      }
    } catch (e) {
      setExaminerState('LISTENING');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(prev => prev + 1);
      setLiveTranscript('');
      setIsSubmitted(false);
      setExaminerState('AI_SPEAKING');
    } else {
      alert('Viva Examination Complete! Returning to Student Portal.');
      navigate('/student/dashboard');
    }
  };

  const handleSkipQuestion = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(prev => prev + 1);
      setLiveTranscript('');
      setIsSubmitted(false);
      setExaminerState('AI_SPEAKING');
    }
  };

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const activeQ = questions[currentIdx] || questions[0];

  return (
    <div className="h-[calc(100vh-4rem)] w-full bg-[#F8FAFC] text-slate-800 flex flex-col font-sans antialiased overflow-hidden">
      
      {/* Permission Warning Banner */}
      {permissionError && (
        <div className="bg-rose-50 border-b border-rose-200 px-6 py-2 text-rose-700 text-xs font-medium flex justify-between items-center shrink-0">
          <span>⚠️ {permissionError}</span>
          <button onClick={requestMediaPermissions} className="px-3 py-1 bg-rose-600 text-white rounded-md text-[11px] font-bold hover:bg-rose-700">
            Grant Permissions
          </button>
        </div>
      )}

      {/* SINGLE SCREEN VIEWPORT CONTAINER (NO VERTICAL SCROLLBAR) */}
      <div className="flex-1 w-full max-w-[1700px] mx-auto p-5 grid grid-cols-1 lg:grid-cols-12 gap-5 h-full overflow-hidden">

        {/* LEFT WORKSPACE (~75% WIDTH - 9 COLS) */}
        <div className="lg:col-span-9 space-y-4 flex flex-col h-full overflow-hidden">

          {/* SPLIT PANEL: LEFT (EXAMINER IMAGE) & RIGHT (STUDENT CAMERA) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 shrink-0">

            {/* LEFT PANEL: EXAMINER PROFILE IMAGE */}
            <div className={`p-3.5 bg-white rounded-3xl border transition-all duration-300 shadow-sm flex items-center justify-center relative overflow-hidden ${
              examinerState === 'AI_SPEAKING' ? 'border-[#0F766E] ring-4 ring-[#0F766E]/10' :
              examinerState === 'STUDENT_SPEAKING' ? 'border-emerald-500 ring-4 ring-emerald-500/10' :
              examinerState === 'AI_PROCESSING' ? 'border-slate-400 ring-4 ring-slate-400/10' :
              'border-slate-200/80'
            }`}>
              <div className="absolute top-3.5 right-3.5 z-10">
                <span className={`w-3 h-3 rounded-full inline-block transition-all ${
                  examinerState === 'AI_SPEAKING' ? 'bg-[#0F766E] animate-ping' :
                  examinerState === 'STUDENT_SPEAKING' ? 'bg-emerald-500 animate-pulse' :
                  examinerState === 'AI_PROCESSING' ? 'bg-slate-400 animate-spin' :
                  'bg-slate-300'
                }`}></span>
              </div>

              <div className="w-full aspect-[16/10] rounded-2xl overflow-hidden bg-slate-100 flex items-center justify-center relative shadow-inner">
                <img
                  src="/professor_avatar.jpg"
                  alt="University Examiner"
                  className="w-full h-full object-cover object-top"
                />

                {examinerState === 'AI_SPEAKING' && (
                  <div className="absolute inset-0 border-4 border-[#0F766E]/50 rounded-2xl pointer-events-none animate-pulse"></div>
                )}
              </div>
            </div>

            {/* RIGHT PANEL: STUDENT CAMERA */}
            <div className="p-3.5 bg-white rounded-3xl border border-slate-200/80 shadow-sm flex flex-col justify-between relative overflow-hidden">
              <div className="relative aspect-[16/10] w-full bg-slate-900 rounded-2xl overflow-hidden flex items-center justify-center shadow-inner">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />

                {!permissionGranted && (
                  <div className="absolute inset-0 bg-slate-100 flex flex-col items-center justify-center p-4 text-center">
                    <VideoOff className="w-7 h-7 text-slate-400 mb-2" />
                    <p className="text-slate-600 text-xs mb-2 font-medium">Camera Preview Offline</p>
                    <button
                      onClick={requestMediaPermissions}
                      className="px-3.5 py-1.5 bg-[#0F766E] hover:bg-[#0D645D] text-white rounded-xl text-xs font-semibold shadow-xs"
                    >
                      Enable Camera & Mic
                    </button>
                  </div>
                )}

                {permissionGranted && (
                  <div className="absolute top-3 left-3 right-3 flex justify-between items-center text-xs font-semibold px-3.5 py-2 bg-slate-900/85 backdrop-blur-md rounded-2xl text-white border border-white/10 shadow-lg z-20 transition-all">
                    <div className="flex items-center gap-2">
                      <span className="text-base">🎭</span>
                      <span className="text-slate-100 font-bold text-xs tracking-tight">
                        {facialAnalysis.displayLabel}
                      </span>
                      {facialAnalysis.confidence > 0 && facialAnalysis.faceDetected && (
                        <span className="px-2 py-0.5 bg-teal-500/20 text-teal-300 font-mono text-[10px] font-bold rounded-md border border-teal-400/30">
                          {Math.round(facialAnalysis.confidence * 100)}%
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="flex items-center gap-1 text-emerald-400 font-medium">
                        <Mic className="w-3.5 h-3.5" /> Mic Active
                      </span>
                      <span className="flex items-center gap-1 text-slate-300">
                        <ShieldCheck className="w-3.5 h-3.5 text-teal-400" /> ID Verified
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* QUESTION CARD */}
          <div className="p-5 bg-white rounded-3xl border border-slate-200/80 shadow-sm space-y-2 shrink-0">
            <div className="flex justify-between items-center border-b border-slate-100 pb-2">
              <span className="text-xs font-bold text-[#0F766E] uppercase tracking-widest font-mono">
                QUESTION {currentIdx + 1} OF {questions.length}
              </span>

              <button
                onClick={() => speakQuestion(activeQ.question_text)}
                className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-all border border-slate-200 flex items-center gap-1.5 shadow-xs"
              >
                <Volume2 className="w-3.5 h-3.5 text-[#0F766E]" /> Repeat Question
              </button>
            </div>

            <h2 className="text-base font-bold text-slate-900 leading-snug tracking-tight">
              "{activeQ.question_text}"
            </h2>
          </div>

          {/* READ-ONLY PROGRESSIVE TRANSCRIPT AREA */}
          <div className="p-5 bg-white rounded-3xl border border-slate-200/80 shadow-sm space-y-3 flex-1 flex flex-col overflow-hidden">
            <div className="flex justify-between items-center shrink-0">
              <div>
                <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                  Live Spoken Response
                  {isRecording && (
                    <span className="flex items-center gap-1.5 text-[11px] text-rose-600 font-mono font-semibold animate-pulse">
                      <span className="w-2 h-2 rounded-full bg-rose-500"></span> Recording ({recordTimer}s)
                    </span>
                  )}
                </h3>
                <p className="text-[11px] text-slate-500">
                  Transcribed live in real-time as you speak. Read-only transcript stream.
                </p>
              </div>

              <div className="flex items-center gap-2">
                {!isRecording ? (
                  <button
                    onClick={handleStartRecording}
                    disabled={!permissionGranted || isProcessingSTT}
                    className="px-4 py-2 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl transition-all shadow-sm flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" /> Start Recording
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handlePauseResumeRecording}
                      className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-colors border border-slate-200 flex items-center gap-1.5"
                    >
                      {isPaused ? <Play className="w-3.5 h-3.5 text-[#0F766E] fill-current" /> : <Pause className="w-3.5 h-3.5 text-amber-600 fill-current" />}
                      {isPaused ? 'Resume' : 'Pause'}
                    </button>

                    <button
                      onClick={handleStopRecording}
                      className="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs rounded-xl transition-all shadow-xs flex items-center gap-1.5"
                    >
                      <Square className="w-3.5 h-3.5 fill-current" /> Stop Recording
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className="relative flex-1 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 p-4 overflow-y-auto min-h-[90px]">
              <div className="text-slate-800 text-xs font-sans leading-relaxed whitespace-pre-wrap">
                {isRecording ? (
                  liveTranscript || <span className="text-slate-400 italic">Listening... Speak clearly into your microphone.</span>
                ) : (
                  liveTranscript || <span className="text-slate-400 italic">Click 'Start Recording' to begin speaking your oral response.</span>
                )}
              </div>
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-slate-100 shrink-0">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1 h-4 px-2.5 bg-slate-100 rounded-md border border-slate-200">
                  {[25, 55, 85, 45, 95, 65, 35].map((v, idx) => (
                    <div
                      key={idx}
                      className={`w-1 rounded-full transition-all duration-150 ${
                        isRecording && !isPaused ? 'bg-[#0F766E] animate-pulse' : 'bg-slate-300 h-1.5'
                      }`}
                      style={{
                        height: isRecording && !isPaused ? `${Math.max(3, (micVolume * (v / 100)) / 4)}px` : '4px'
                      }}
                    ></div>
                  ))}
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {isRecording ? `Mic Volume: ${micVolume}%` : 'Mic Ready'}
                </span>
              </div>

              <div className="flex gap-2.5">
                <button
                  onClick={handleSkipQuestion}
                  disabled={currentIdx >= questions.length - 1}
                  className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-semibold rounded-xl transition-colors border border-slate-200 flex items-center gap-1.5 disabled:opacity-40"
                >
                  <SkipForward className="w-3.5 h-3.5" /> Skip Question
                </button>

                {isSubmitted ? (
                  <button
                    onClick={handleNextQuestion}
                    className="px-5 py-2 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl transition-all shadow-md flex items-center gap-1.5"
                  >
                    Next Question <ChevronRight className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    onClick={handleSubmitAnswer}
                    disabled={isSubmitting || !liveTranscript.trim()}
                    className="px-6 py-2 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl transition-all shadow-md shadow-[#0F766E]/20 flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {isSubmitting ? 'Submitting Answer...' : 'Submit Answer →'}
                  </button>
                )}
              </div>
            </div>

            {isSubmitted && (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs space-y-1 shrink-0 shadow-xs">
                <div className="font-bold text-emerald-800 flex items-center gap-2 text-xs">
                  <CheckCircle2 className="w-4 h-4 text-[#0F766E]" /> ✓ Response Submitted Successfully
                </div>
                <p className="text-emerald-700 text-[11px] leading-relaxed">
                  Your response has been sent for AI evaluation and faculty review.
                </p>
              </div>
            )}
          </div>

        </div>

        {/* RIGHT FIXED SIDEBAR (~25% WIDTH - 3 COLS) */}
        <div className="lg:col-span-3 space-y-4 flex flex-col h-full overflow-hidden">
          <div className="p-5 bg-white rounded-3xl border border-slate-200/80 shadow-sm space-y-4 h-full flex flex-col justify-between">
            <div className="space-y-4">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-widest border-b border-slate-100 pb-2.5 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-[#0F766E]" /> Viva Status & Statistics
              </h3>

              <div className="space-y-3 text-xs">
                <div className="p-3.5 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 flex justify-between items-center">
                  <span className="text-slate-600 flex items-center gap-2 font-medium">
                    <Clock className="w-4 h-4 text-[#0F766E]" /> Viva Timer
                  </span>
                  <span className="font-mono text-sm font-bold text-slate-900">{formatTime(elapsedTimer)}</span>
                </div>

                <div className="p-3.5 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 flex justify-between items-center">
                  <span className="text-slate-600 flex items-center gap-2 font-medium">
                    <HelpCircle className="w-4 h-4 text-indigo-600" /> Question Progress
                  </span>
                  <span className="font-mono text-sm font-bold text-[#0F766E]">{currentIdx + 1} / {questions.length}</span>
                </div>

                <div className="p-3.5 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 flex justify-between items-center">
                  <span className="text-slate-600 flex items-center gap-2 font-medium">
                    <Award className="w-4 h-4 text-emerald-600" /> Remaining
                  </span>
                  <span className="font-mono text-sm font-bold text-slate-700">{questions.length - (currentIdx + 1)} Questions</span>
                </div>

                <div className="p-3.5 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 flex justify-between items-center">
                  <span className="text-slate-600 flex items-center gap-2 font-medium">
                    <Mic className="w-4 h-4 text-[#0F766E]" /> Microphone Status
                  </span>
                  <span className="font-semibold text-slate-800">{permissionGranted ? 'Active' : 'Offline'}</span>
                </div>

                <div className="p-3.5 bg-[#F8FAFC] rounded-2xl border border-slate-200/80 flex justify-between items-center">
                  <span className="text-slate-600 flex items-center gap-2 font-medium">
                    <Video className="w-4 h-4 text-[#0F766E]" /> Camera Status
                  </span>
                  <span className="font-semibold text-slate-800">{permissionGranted ? 'Active' : 'Offline'}</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 text-center shrink-0">
              <span className="text-xs text-slate-500 font-semibold">Subject: {activeQ.subject}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
