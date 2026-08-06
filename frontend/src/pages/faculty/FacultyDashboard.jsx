import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Sparkles, FileCheck, ArrowRight, PlusCircle } from 'lucide-react';

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

      {/* Feature Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* CREATE VIVA PIPELINE CARD (PRIMARY WORKFLOW) */}
        <div className="p-8 bg-white rounded-3xl border-2 border-[#0F766E] shadow-sm hover:shadow-md transition-all space-y-4 relative overflow-hidden">
          <div className="w-10 h-10 rounded-2xl bg-[#0F766E] text-white flex items-center justify-center mb-2 shadow-sm shadow-[#0F766E]/20">
            <PlusCircle className="w-5 h-5" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded text-[10px] font-bold uppercase tracking-wider block w-fit mb-1">
              PRIMARY WORKFLOW
            </span>
            <h3 className="text-base font-bold text-slate-900">Create Faculty Viva Pipeline</h3>
            <p className="text-xs text-slate-500 mt-1">
              Configure viva parameters, upload syllabus PDF/PPT/DOCX documents to Knowledge Base, review grounded questions, and publish to students.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/faculty/viva/create"
              className="w-full py-3.5 bg-[#0F766E] hover:bg-[#0D645D] text-white font-bold text-xs text-center rounded-2xl transition-all shadow-md shadow-[#0F766E]/20 flex items-center justify-center gap-2"
            >
              Start Viva Creation Pipeline <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* AI QUESTION GENERATOR CARD */}
        <div className="p-8 bg-white rounded-3xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all space-y-4">
          <div className="w-10 h-10 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center text-[#0F766E] mb-2">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Standalone Question Generator</h3>
            <p className="text-xs text-slate-500 mt-1">
              Generate syllabus-grounded oral viva questions with automated retrieval confidence gates and quality safeguards.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/faculty/questions"
              className="w-full py-3.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 font-bold text-xs text-center rounded-2xl transition-all flex items-center justify-center gap-2"
            >
              Open Question Generator <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* EVALUATION REVIEW CARD */}
        <div className="p-8 bg-white rounded-3xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all space-y-4">
          <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-700 mb-2">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Faculty Review & Override Queue</h3>
            <p className="text-xs text-slate-500 mt-1">
              Review AI preliminary scores, inspect verbatim evidence quotes, override criterion marks, and publish official results.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/faculty/evaluations"
              className="w-full py-3.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-800 font-bold text-xs text-center rounded-2xl transition-all flex items-center justify-center gap-2"
            >
              Open Evaluation Review <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
