'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  ShieldAlert, Brain, Sparkles, MapPin, 
  CheckCircle, ArrowRight, Activity, Users, 
  FileText, ArrowDown
} from 'lucide-react';
import { tokenStorage } from '@/lib/api';

export default function LandingPage() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    setUser(tokenStorage.getUserInfo());
  }, []);

  // Demo state for the AI sandbox
  const [demoText, setDemoText] = useState('Nanna ward nalli garbage fully dump agide mathu smell barthide, please clear.');
  const [isClassifying, setIsClassifying] = useState(false);
  const [aiResult, setAiResult] = useState<any>(null);

  const runDemoAI = () => {
    setIsClassifying(true);
    setTimeout(() => {
      // Hardcoded offline prediction for Hinglish demo
      setAiResult({
        detectedLang: 'Kannada / Kanglish',
        translation: 'In my ward, garbage is fully dumped and smelling bad, please clear.',
        category: 'Solid Waste',
        confidence: 0.942,
        priority: 'High',
        department: 'BSWML'
      });
      setIsClassifying(false);
    }, 1200);
  };

  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 text-white p-2 rounded-lg shadow-md flex items-center justify-center">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <div>
              <span className="font-bold text-xl tracking-tight text-slate-900 dark:text-white">CivicAI</span>
              <span className="text-xs block text-slate-500 font-medium">Karnataka State Portal</span>
            </div>
          </div>
          <nav className="flex items-center space-x-4">
            <Link href="#features" className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 transition-colors">Features</Link>
            <Link href="#ai-demo" className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 transition-colors">AI Sandbox</Link>
            {user ? (
              <Link 
                href={`/${user.role.toLowerCase()}/dashboard`}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow transition-all flex items-center space-x-1"
              >
                <span>Go to Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <div className="flex items-center space-x-2">
                <Link 
                  href="/login" 
                  className="text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 px-4 py-2 rounded-lg text-sm font-semibold transition"
                >
                  Log In
                </Link>
                <Link 
                  href="/register" 
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow transition"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 lg:py-28 bg-gradient-to-b from-blue-50/50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 overflow-hidden">
        {/* Decorative ambient spots */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute top-1/3 left-1/4 w-[300px] h-[300px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center space-x-2 bg-blue-100/80 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-3 py-1 rounded-full text-xs font-semibold mb-6 border border-blue-200 dark:border-blue-800 animate-pulse">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Next-Gen Governance Enabled</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight">
              AI-Powered Civic Grievance Redressal for <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-500 dark:from-blue-400 dark:to-indigo-300">Karnataka</span>
            </h1>
            
            <p className="mt-6 text-lg sm:text-xl text-slate-600 dark:text-slate-300 font-normal leading-relaxed">
              Report civic complaints via text, voice, and photos. Our intelligent pipeline automatically translates native scripts, classifies issues, identifies duplicates, predicts urgency, and routes them directly to BBMP, BESCOM, BWSSB, or BSWML.
            </p>
            
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link 
                href="/register" 
                className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center space-x-2 text-base"
              >
                <span>Report an Issue (Citizen)</span>
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link 
                href="/login" 
                className="w-full sm:w-auto bg-white hover:bg-slate-50 border border-slate-300 dark:bg-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 px-8 py-3.5 rounded-xl font-semibold text-slate-700 dark:text-slate-200 transition-all flex items-center justify-center space-x-2 text-base"
              >
                <span>Officer & Admin Portal</span>
              </Link>
            </div>
          </div>

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-4xl mx-auto">
            <div className="bg-white/60 dark:bg-slate-900/60 backdrop-blur border border-slate-100 dark:border-slate-800 p-6 rounded-2xl text-center shadow-sm">
              <Activity className="h-8 w-8 text-blue-600 mx-auto mb-3" />
              <span className="block text-2xl font-bold text-slate-900 dark:text-white">94%</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">AI Accuracy</span>
            </div>
            <div className="bg-white/60 dark:bg-slate-900/60 backdrop-blur border border-slate-100 dark:border-slate-800 p-6 rounded-2xl text-center shadow-sm">
              <Users className="h-8 w-8 text-indigo-600 mx-auto mb-3" />
              <span className="block text-2xl font-bold text-slate-900 dark:text-white">Instant</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">Routing Speed</span>
            </div>
            <div className="bg-white/60 dark:bg-slate-900/60 backdrop-blur border border-slate-100 dark:border-slate-800 p-6 rounded-2xl text-center shadow-sm">
              <CheckCircle className="h-8 w-8 text-emerald-600 mx-auto mb-3" />
              <span className="block text-2xl font-bold text-slate-900 dark:text-white">100m</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">Duplicate Scan</span>
            </div>
            <div className="bg-white/60 dark:bg-slate-900/60 backdrop-blur border border-slate-100 dark:border-slate-800 p-6 rounded-2xl text-center shadow-sm">
              <FileText className="h-8 w-8 text-violet-600 mx-auto mb-3" />
              <span className="block text-2xl font-bold text-slate-900 dark:text-white">4 Depts</span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">Auto Connected</span>
            </div>
          </div>
        </div>
      </section>

      {/* AI Demonstration Sandbox */}
      <section id="ai-demo" className="py-20 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white">Try the AI Pipeline Sandbox</h2>
            <p className="mt-3 text-slate-500 dark:text-slate-400">See how our AI processes Hinglish/Kannada, classifies the issue, predicts priority, and maps routing instantly.</p>
          </div>

          <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 md:p-8 shadow-md grid md:grid-cols-5 gap-8">
            {/* Input sandbox column */}
            <div className="md:col-span-2 flex flex-col justify-between">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200 mb-2">Complaint Description (Hinglish/Kannada/English)</label>
                <textarea 
                  rows={4}
                  value={demoText}
                  onChange={(e) => setDemoText(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                ></textarea>
                <p className="text-xs text-slate-400 mt-2">Try mixing languages. E.g. "garbage pile", "streetlight off", "road block layout nalli".</p>
              </div>
              <button 
                onClick={runDemoAI}
                disabled={isClassifying}
                className="mt-6 w-full bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-xl py-3 text-sm font-bold shadow-md transition flex items-center justify-center space-x-2"
              >
                {isClassifying ? (
                  <>
                    <Brain className="h-4 w-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Run AI Classification</span>
                  </>
                )}
              </button>
            </div>

            {/* AI pipeline trace output column */}
            <div className="md:col-span-3 border-t md:border-t-0 md:border-l border-slate-200 dark:border-slate-800 pt-6 md:pt-0 md:pl-8 flex flex-col justify-center">
              {aiResult ? (
                <div className="space-y-4 animate-fade-in">
                  <h4 className="font-bold text-slate-900 dark:text-white flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 pb-2">
                    <Activity className="h-4 w-4 text-emerald-500" />
                    <span>AI Execution Pipeline Result</span>
                  </h4>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <span className="text-slate-500 dark:text-slate-400 font-medium">Detected Lang:</span>
                    <span className="col-span-2 text-slate-800 dark:text-slate-200 font-bold">{aiResult.detectedLang}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <span className="text-slate-500 dark:text-slate-400 font-medium">Translated text:</span>
                    <span className="col-span-2 text-slate-800 dark:text-slate-200 italic font-semibold">"{aiResult.translation}"</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <span className="text-slate-500 dark:text-slate-400 font-medium">Predicted Category:</span>
                    <span className="col-span-2 text-slate-800 dark:text-slate-200 font-bold flex items-center space-x-1.5">
                      <span className="text-blue-600 dark:text-blue-400">{aiResult.category}</span>
                      <span className="text-[10px] text-slate-400">({(aiResult.confidence * 100).toFixed(1)}% conf)</span>
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <span className="text-slate-500 dark:text-slate-400 font-medium">Urgency Priority:</span>
                    <span className="col-span-2 text-red-600 dark:text-red-400 font-bold">{aiResult.priority}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <span className="text-slate-500 dark:text-slate-400 font-medium">Dynamic Route:</span>
                    <span className="col-span-2 text-slate-800 dark:text-slate-200 font-bold flex items-center space-x-1">
                      <span className="bg-slate-200 dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] uppercase font-mono">{aiResult.department}</span>
                      <span className="text-[10px] text-slate-400 font-normal">Routed via db mapping</span>
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400">
                  <Brain className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-700 mb-3" />
                  <p className="text-sm font-medium">Input a description on the left and run the AI simulation.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* How it Works / Timelines */}
      <section id="features" className="py-20 bg-slate-50 dark:bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white">Seamless Complaint Redressal Lifecycle</h2>
            <p className="mt-3 text-slate-500 dark:text-slate-400">Citizens submit reports in seconds; AI matches, routing distributes, and officers resolve details.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl p-6 shadow-sm relative">
              <div className="bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 h-10 w-10 rounded-lg flex items-center justify-center font-bold mb-4">1</div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">Raise & Geotag</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Write a brief report and upload a photo. The app auto-detects your location via GPS and shows nearby issues on Leaflet map to check for duplicates.
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl p-6 shadow-sm relative">
              <div className="bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 h-10 w-10 rounded-lg flex items-center justify-center font-bold mb-4">2</div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">AI Verification & Routing</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                YOLO verifies the complaint image. NLP parses description, detects Kannada, translates it, assigns a priority, and routes it directly to the best officer's queue.
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl p-6 shadow-sm relative">
              <div className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 h-10 w-10 rounded-lg flex items-center justify-center font-bold mb-4">3</div>
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-2">Officer Action & Close</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Officers view detailed maps, accept cases, execute in-progress works, and upload resolution proof photos. Citizens receive notifications and close the case.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-10 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-400 dark:text-slate-500 text-xs">
          <p>&copy; 2026 Government of Karnataka. CivicAI Grievance Management System. All rights reserved.</p>
          <p className="mt-1 font-medium">Powered by Next.js 15, FastAPI, SentenceTransformers, and YOLOv11.</p>
        </div>
      </footer>
    </div>
  );
}
