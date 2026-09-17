import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, ShieldCheck, UserCheck, Lock, Mail, User, BookOpen, CheckCircle2, AlertCircle, ArrowRight, Loader2, GraduationCap, Briefcase
} from 'lucide-react';
import { getApiUrl } from '../services/api';

export default function Login() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('login'); // 'login' | 'register'

  // Form Fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('student');

  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // Helper to format FastAPI Pydantic & Backend errors into human-readable messages
  const formatErrorMsg = (detail, fallbackMsg) => {
    if (!detail) return fallbackMsg;
    if (typeof detail === 'string') return detail;

    if (Array.isArray(detail)) {
      return detail.map(err => {
        if (typeof err === 'string') return err;
        
        // Parse Pydantic location field name (e.g. ["body", "confirm_password"])
        let fieldName = '';
        if (err.loc && Array.isArray(err.loc)) {
          const rawField = err.loc[err.loc.length - 1];
          if (rawField && rawField !== 'body') {
            fieldName = String(rawField).replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
          }
        }

        const msgText = err.msg || 'Invalid input';
        if (msgText.toLowerCase() === 'field required') {
          return fieldName ? `${fieldName} is required` : 'Required field is missing';
        }
        return fieldName ? `${fieldName}: ${msgText}` : msgText;
      }).join('. ');
    }

    if (typeof detail === 'object') {
      return detail.msg || JSON.stringify(detail);
    }

    return String(detail);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setToast(null);

    const payload = {
      email: email.trim(),
      password
    };

    console.log("[AutoViva Login Request Payload]:", payload);

    try {
      const res = await fetch(getApiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => null);

      if (res.ok && data && data.access_token) {
        localStorage.setItem('autoviva_token', data.access_token);
        localStorage.setItem('autoviva_user', JSON.stringify(data.user));

        setToast({ type: 'success', text: `Authenticated successfully! Welcome, ${data.user.name}.` });

        setTimeout(() => {
          if (data.user.role === 'faculty') {
            navigate('/faculty/dashboard');
          } else {
            navigate('/student/dashboard');
          }
        }, 400);
      } else {
        const msg = formatErrorMsg(data?.detail, 'Authentication failed. Please check credentials.');
        setToast({ type: 'error', text: msg });
      }
    } catch (err) {
      console.error('Login request error:', err);
      setToast({ type: 'error', text: 'Server connection error. Please ensure backend is running.' });
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setToast(null);

    if (password !== confirmPassword) {
      setToast({ type: 'error', text: 'Password and Confirm Password do not match.' });
      setLoading(false);
      return;
    }

    const payload = {
      name: name.trim(),
      email: email.trim(),
      password: password,
      confirm_password: confirmPassword,
      role: role
    };

    console.log("[AutoViva Register Request Payload]:", payload);

    try {
      const res = await fetch(getApiUrl('/api/auth/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => null);

      if (res.ok && data && data.access_token) {
        localStorage.setItem('autoviva_token', data.access_token);
        localStorage.setItem('autoviva_user', JSON.stringify(data.user));

        setToast({ type: 'success', text: 'Account created successfully in MongoDB! Redirecting...' });

        setTimeout(() => {
          if (data.user.role === 'faculty') {
            navigate('/faculty/dashboard');
          } else {
            navigate('/student/dashboard');
          }
        }, 400);
      } else {
        const msg = formatErrorMsg(data?.detail, 'Registration failed. Please check missing fields.');
        setToast({ type: 'error', text: msg });
      }
    } catch (err) {
      console.error('Register request error:', err);
      setToast({ type: 'error', text: 'Server connection error. Please ensure backend is running.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-6 bg-[#F8FAFC]">
      <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200/80 shadow-sm p-8 space-y-6">
        
        {/* Logo & Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-[#0F766E] flex items-center justify-center text-white font-black text-xl mx-auto shadow-md shadow-[#0F766E]/20">
            A
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            AutoViva
          </h1>
          <p className="text-xs text-slate-500 font-medium">
            AI-Powered Oral Examination & Knowledge Evaluation Platform
          </p>
        </div>

        {/* Tab Selector: Sign In vs Create Account */}
        <div className="grid grid-cols-2 gap-2 p-1.5 bg-slate-100 rounded-2xl border border-slate-200/70 text-xs font-bold">
          <button
            type="button"
            onClick={() => { setActiveTab('login'); setToast(null); }}
            className={`py-2.5 rounded-xl transition-all ${
              activeTab === 'login'
                ? 'bg-white text-[#0F766E] shadow-xs border border-slate-200/80'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('register'); setToast(null); }}
            className={`py-2.5 rounded-xl transition-all ${
              activeTab === 'register'
                ? 'bg-white text-[#0F766E] shadow-xs border border-slate-200/80'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Safe Inline Toast Notification */}
        {toast && (
          <div className={`p-3.5 rounded-2xl text-xs font-semibold flex items-center gap-2 ${
            toast.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}>
            {toast.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />}
            <span>{String(toast.text)}</span>
          </div>
        )}

        {/* SIGN IN FORM */}
        {activeTab === 'login' ? (
          <form onSubmit={handleLogin} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Academic Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@university.edu or faculty@university.edu"
                className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-[#0F766E] focus:bg-white transition-all"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-2.5 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-[#0F766E] focus:bg-white transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Authenticating...
                </>
              ) : (
                <>
                  Sign In <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        ) : (
          /* CREATE ACCOUNT FORM */
          <form onSubmit={handleRegister} className="space-y-3.5 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Alex Mercer"
                className="w-full px-4 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-[#0F766E] focus:bg-white transition-all"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Academic Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="alex@university.edu"
                className="w-full px-4 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-[#0F766E] focus:bg-white transition-all"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-[#0F766E] focus:bg-white transition-all"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Confirm Password</label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 bg-[#F8FAFC] border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-[#0F766E] focus:bg-white transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Account Role</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setRole('student')}
                  className={`py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    role === 'student'
                      ? 'bg-[#0F766E] text-white border-[#0F766E]'
                      : 'bg-[#F8FAFC] border-slate-200 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <GraduationCap className="w-3.5 h-3.5" /> Student
                </button>
                <button
                  type="button"
                  onClick={() => setRole('faculty')}
                  className={`py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    role === 'faculty'
                      ? 'bg-[#0F766E] text-white border-[#0F766E]'
                      : 'bg-[#F8FAFC] border-slate-200 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <Briefcase className="w-3.5 h-3.5" /> Faculty
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs rounded-xl shadow-md shadow-[#0F766E]/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Creating Account...
                </>
              ) : (
                <>
                  Create Account <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}

      </div>
    </div>
  );
}
