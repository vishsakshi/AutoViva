import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, AlertCircle } from 'lucide-react';

export default function HealthCheck() {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health').catch(() => fetch('http://localhost:8000/api/health'));
        if (res.ok) {
          setStatus('online');
        } else {
          setStatus('offline');
        }
      } catch (err) {
        setStatus('offline');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-2 px-3 py-1 bg-white border border-slate-200 rounded-full shadow-xs text-xs">
      <span className="relative flex h-2 w-2">
        {status === 'online' ? (
          <>
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </>
        ) : (
          <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
        )}
      </span>
      <span className="font-semibold text-slate-700">
        {status === 'online' ? 'AutoViva API Online' : 'Connecting to AutoViva Core...'}
      </span>
    </div>
  );
}
