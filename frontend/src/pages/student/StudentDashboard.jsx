import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Mic, BookOpen, Clock, Award, CheckCircle2, ArrowRight, ShieldCheck, HelpCircle } from 'lucide-react';
import { getApiUrl } from '../../services/api';

export default function StudentDashboard() {
  const [publishedVivas, setPublishedVivas] = useState([]);

  useEffect(() => {
    const fetchPublished = async () => {
      try {
        const res = await fetch(getApiUrl('/api/viva/published'));
        if (res.ok) {
          const data = await res.json();
          setPublishedVivas(data || []);
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchPublished();
  }, []);

  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200/80">
        <div>
          <span className="text-xs font-bold text-[#0F766E] uppercase tracking-widest block mb-1">
            Student Portal
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            AutoViva Examination Workspace
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Attend live AI oral examinations with real-time speech transcription and instant evaluation feedback
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#0F766E]" /> Student Access Granted
          </span>
        </div>
      </div>

      {/* Main Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Active Examination Card */}
        <div className="p-8 bg-white rounded-3xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all space-y-4">
          <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-[#0F766E] mb-2">
            <Mic className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Computer Networks & DBMS Viva</h3>
            <p className="text-xs text-slate-500 mt-1">
              Active oral viva session ready for attendance. Exam features viva questions grounded in syllabus knowledge base with live Whisper speech transcription.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/student/viva"
              className="w-full py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs text-center rounded-2xl transition-all shadow-md shadow-[#0F766E]/20 flex items-center justify-center gap-2"
            >
              🎙️ Join Live Oral Viva Session <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Faculty Published Vivas Card */}
        <div className="p-8 bg-white rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="w-10 h-10 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center text-[#0F766E] mb-2">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Faculty Published Examinations ({publishedVivas.length})</h3>
            <p className="text-xs text-slate-500 mt-1">
              Published vivas created by faculty with syllabus document embeddings.
            </p>
          </div>

          {publishedVivas.length === 0 ? (
            <div className="p-4 bg-[#F8FAFC] rounded-2xl border border-slate-200 text-xs text-slate-500 italic text-center">
              New faculty published sessions will appear here dynamically.
            </div>
          ) : (
            <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
              {publishedVivas.map((v) => (
                <div key={v.viva_id} className="p-3.5 bg-[#F8FAFC] border border-slate-200/80 rounded-2xl text-xs space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-900">{v.subject} ({v.course_code})</span>
                    <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded">PUBLISHED</span>
                  </div>
                  <p className="text-slate-600 text-[11px]">Topic: {v.topic} • {v.question_count} Questions • {v.duration_minutes} Mins</p>
                  <Link
                    to="/student/viva"
                    className="block w-full py-2 bg-[#0F766E] hover:bg-[#0D645D] text-white text-center text-xs font-bold rounded-xl shadow-xs"
                  >
                    Take Viva Exam →
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
