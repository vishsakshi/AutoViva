import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, FileCheck, ArrowRight, PlusCircle } from 'lucide-react';

export default function FacultyDashboard() {
  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center pb-6 border-b border-slate-200/80">
        <div>
          <span className="text-xs font-bold text-[#0F766E] uppercase tracking-widest block mb-1">
            Faculty Portal
          </span>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            AutoViva Faculty Control Center
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Create viva sessions, upload syllabus documents to Knowledge Base, and review AI evaluation outputs
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#0F766E]" /> Faculty Signature Authority
          </span>
        </div>
      </div>

      {/* Clean 2-Card Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* CARD 1: CREATE FACULTY VIVA PIPELINE (PRIMARY WORKFLOW - 50% WIDTH) */}
        <div className="p-8 bg-white rounded-3xl border-2 border-[#0F766E] shadow-sm hover:shadow-md transition-all space-y-5 relative overflow-hidden flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <div className="w-12 h-12 rounded-2xl bg-[#0F766E] text-white flex items-center justify-center shadow-md shadow-[#0F766E]/20">
                <PlusCircle className="w-6 h-6" />
              </div>
              <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-extrabold uppercase tracking-wider">
                PRIMARY WORKFLOW
              </span>
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">Create Faculty Viva Pipeline</h3>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                Configure viva metadata parameters, upload syllabus PDF/PPT/DOCX documents to Knowledge Base, automatically extract grounded questions, review evaluation rubrics, and publish the official viva session.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <Link
              to="/faculty/viva/create"
              className="w-full py-4 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs text-center rounded-2xl transition-all shadow-md shadow-[#0F766E]/20 flex items-center justify-center gap-2"
            >
              Start Viva Creation Pipeline <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* CARD 2: FACULTY REVIEW & OVERRIDE QUEUE (SECONDARY ACTION - 50% WIDTH) */}
        <div className="p-8 bg-white rounded-3xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-700">
              <FileCheck className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-lg font-bold text-slate-900">Faculty Review & Override Queue</h3>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                Review AI preliminary evaluation scores, inspect verbatim student evidence quotes, override criterion marks, provide custom feedback, and publish official academic results.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <Link
              to="/faculty/evaluations"
              className="w-full py-4 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 font-bold text-xs text-center rounded-2xl transition-all flex items-center justify-center gap-2"
            >
              Open Evaluation Review Queue <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
