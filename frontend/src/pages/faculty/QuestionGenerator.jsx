import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, CheckCircle2, XCircle, ArrowLeft, BookOpen, Layers, ShieldCheck, RefreshCw } from 'lucide-react';

export default function QuestionGenerator() {
  const [subject, setSubject] = useState('Computer Networks');
  const [topic, setTopic] = useState('IP Addressing & NAT');
  const [difficulty, setDifficulty] = useState('medium');
  const [count, setCount] = useState(3);
  const [loading, setLoading] = useState(false);
  const [drafts, setDrafts] = useState([]);
  const [bank, setBank] = useState([]);
  const [message, setMessage] = useState(null);

  const fetchDrafts = async () => {
    try {
      const res = await fetch('/api/questions/drafts').catch(() => fetch('http://localhost:8000/api/questions/drafts'));
      if (res.ok) {
        const data = await res.json();
        setDrafts(data.drafts || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchBank = async () => {
    try {
      const res = await fetch('/api/questions/bank').catch(() => fetch('http://localhost:8000/api/questions/bank'));
      if (res.ok) {
        const data = await res.json();
        setBank(data.questions || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDrafts();
    fetchBank();
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch('/api/questions/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject,
          topic,
          difficulty,
          question_count: parseInt(count, 10)
        })
      });

      if (res.ok) {
        const data = await res.json();
        setMessage({ type: 'success', text: `Generated ${data.generated_count} questions for review (${data.rejected_count} duplicates/invalid rejected).` });
        fetchDrafts();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Generation failed.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error connecting to backend server.' });
    } finally {
      setLoading(false);
    }
  };

  const handleReviewAction = async (questionId, action) => {
    try {
      const res = await fetch('/api/questions/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_id: questionId,
          action: action
        })
      });

      if (res.ok) {
        fetchDrafts();
        fetchBank();
      }
    } catch (e) {
      console.error(e);
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
            AutoViva Question Generator
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Syllabus-grounded question generation engine with retrieval confidence gate & 3 quality safeguards
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
        
        {/* Left Form (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 space-y-5 h-fit">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Sparkles className="w-4 h-4 text-blue-600" /> Generator Controls
          </h3>

          <form onSubmit={handleGenerate} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Academic Subject</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 font-medium"
              >
                <option value="Computer Networks">Computer Networks</option>
                <option value="DBMS">DBMS</option>
                <option value="Operating Systems">Operating Systems</option>
                <option value="OOP & Java">OOP & Java</option>
                <option value="NLP & AI">NLP & AI</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Topic</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 font-medium"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 font-medium"
              >
                <option value="easy font-medium">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Question Count</label>
              <input
                type="number"
                min="1"
                max="10"
                value={count}
                onChange={(e) => setCount(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:border-blue-500 font-medium"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md shadow-blue-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {loading ? 'Generating...' : 'Generate Questions'}
            </button>
          </form>
        </div>

        {/* Right Drafts & Approved Queues (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Faculty Review Queue */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-amber-600" /> Pending Faculty Approval Queue ({drafts.length})
              </h3>
            </div>

            {drafts.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-4 text-center">No draft questions currently pending faculty review.</p>
            ) : (
              <div className="space-y-4">
                {drafts.map((q) => (
                  <div key={q.question_id} className="p-4 bg-[#F8FAFC] border border-slate-200/80 rounded-2xl space-y-3 text-xs">
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-slate-900 font-mono">{q.question_id}</span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleReviewAction(q.question_id, 'APPROVE')}
                          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg flex items-center gap-1"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                        </button>
                        <button
                          onClick={() => handleReviewAction(q.question_id, 'REJECT')}
                          className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-lg flex items-center gap-1"
                        >
                          <XCircle className="w-3.5 h-3.5" /> Reject
                        </button>
                      </div>
                    </div>
                    <p className="text-slate-800 font-bold text-xs">{q.question_text}</p>
                    <p className="text-slate-500 text-[11px]">Ideal Answer: {q.ideal_answer}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Approved Question Bank */}
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Approved Active Question Bank ({bank.length})
            </h3>
            {bank.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-4 text-center">No approved questions in active bank yet.</p>
            ) : (
              <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                {bank.map((q) => (
                  <div key={q.question_id} className="p-3.5 bg-[#F8FAFC] border border-slate-200/80 rounded-2xl text-xs space-y-1">
                    <div className="flex justify-between font-mono text-[10px] text-slate-500">
                      <span>{q.subject} • {q.topic}</span>
                      <span className="text-emerald-600 font-bold">APPROVED</span>
                    </div>
                    <p className="font-semibold text-slate-900">{q.question_text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
