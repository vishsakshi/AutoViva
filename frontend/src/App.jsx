import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { GraduationCap, Briefcase, LogOut } from 'lucide-react';
import Login from './pages/Login';
import FacultyDashboard from './pages/faculty/FacultyDashboard';
import EvaluationReview from './pages/faculty/EvaluationReview';
import CreateVivaSession from './pages/faculty/CreateVivaSession';
import StudentDashboard from './pages/student/StudentDashboard';
import LiveVivaSession from './pages/student/LiveVivaSession';

function HeaderNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const isFacultyActive = location.pathname.startsWith('/faculty');
  const isStudentActive = location.pathname.startsWith('/student');

  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('autoviva_user');
    if (storedUser) {
      try { setUser(JSON.parse(storedUser)); } catch (e) {}
    }
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem('autoviva_token');
    localStorage.removeItem('autoviva_user');
    setUser(null);
    navigate('/login');
  };

  // Hide header on login page
  if (location.pathname === '/login') return null;

  return (
    <header className="h-16 px-8 bg-white border-b border-slate-200 flex justify-between items-center sticky top-0 z-50 shadow-xs">
      {/* Brand Logo & Name (No Subtitle) */}
      <Link to="/login" className="flex items-center gap-2.5 group">
        <div className="w-9 h-9 rounded-xl bg-[#0F766E] flex items-center justify-center text-white font-black text-base shadow-sm shadow-[#0F766E]/20 group-hover:bg-[#0D645D] transition-colors">
          A
        </div>
        <span className="text-xl font-extrabold text-slate-900 tracking-tight">
          AutoViva
        </span>
      </Link>

      {/* Navigation & User Session */}
      <div className="flex items-center gap-4">
        {/* Distinct Navigation Cards */}
        <nav className="flex items-center gap-2 text-xs">
          <Link
            to="/student/dashboard"
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              isStudentActive
                ? 'bg-[#0F766E] text-white shadow-md shadow-[#0F766E]/20'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200/80 border border-slate-200/80'
            }`}
          >
            <GraduationCap className="w-4 h-4" /> Student Portal
          </Link>

          <Link
            to="/faculty/dashboard"
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              isFacultyActive
                ? 'bg-white border-2 border-[#0F766E] text-[#0F766E] shadow-xs'
                : 'bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200/80 border border-slate-200/80'
            }`}
          >
            <Briefcase className="w-4 h-4" /> Faculty Portal
          </Link>
        </nav>

        {user && (
          <div className="flex items-center gap-3 pl-2 border-l border-slate-200 text-xs">
            <span className="text-slate-600 font-medium">
              <span className="text-slate-900 font-semibold">{user.name}</span> ({user.role})
            </span>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

// Protected Route Wrapper
function ProtectedRoute({ children, allowedRole }) {
  const token = localStorage.getItem('autoviva_token');
  const storedUser = localStorage.getItem('autoviva_user');

  if (!token || !storedUser) {
    return <Navigate to="/login" replace />;
  }

  try {
    const u = JSON.parse(storedUser);
    if (allowedRole && u.role !== allowedRole) {
      return <Navigate to={u.role === 'faculty' ? '/faculty/dashboard' : '/student/dashboard'} replace />;
    }
  } catch (e) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#F8FAFC] text-slate-800 flex flex-col font-sans">
        <HeaderNav />

        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />

            {/* Protected Student Routes */}
            <Route path="/student/viva" element={
              <ProtectedRoute allowedRole="student">
                <LiveVivaSession />
              </ProtectedRoute>
            } />
            <Route path="/student/*" element={
              <ProtectedRoute allowedRole="student">
                <StudentDashboard />
              </ProtectedRoute>
            } />

            {/* Protected Faculty Routes */}
            <Route path="/faculty/viva/create" element={
              <ProtectedRoute allowedRole="faculty">
                <CreateVivaSession />
              </ProtectedRoute>
            } />
            <Route path="/faculty/evaluations" element={
              <ProtectedRoute allowedRole="faculty">
                <EvaluationReview />
              </ProtectedRoute>
            } />
            <Route path="/faculty/*" element={
              <ProtectedRoute allowedRole="faculty">
                <FacultyDashboard />
              </ProtectedRoute>
            } />

            <Route path="*" element={
              <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8">
                <h2 className="text-2xl font-bold text-slate-800 mb-2">404 - Page Not Found</h2>
                <p className="text-slate-500 text-xs mb-4">The requested page could not be located on AutoViva.</p>
                <Link to="/login" className="px-4 py-2 bg-[#0F766E] text-white text-xs font-bold rounded-xl hover:bg-[#0D645D] transition-colors">
                  Return to AutoViva Home
                </Link>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
