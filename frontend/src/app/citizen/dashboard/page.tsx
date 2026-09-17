'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import {
  ShieldAlert, LogOut, Plus, MapPin,
  Image as ImageIcon, Loader2, Info, CheckCircle2,
  Clock, AlertTriangle, MessageSquare, Globe, Navigation,
  ArrowRight, Mic, MicOff, Star, ThumbsUp, ThumbsDown,
  Shield, TriangleAlert, RefreshCw, Volume2, Sparkles
} from 'lucide-react';
import { api, tokenStorage } from '@/lib/api';
import { toast } from 'sonner';

const MapComponent = dynamic(() => import('@/components/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-100 dark:bg-slate-800 animate-pulse flex items-center justify-center text-slate-400 font-semibold rounded-xl">
      Loading Map Engine...
    </div>
  )
});

// ── Helper: SLA progress bar ────────────────────────────────────────────────
function SLABar({ slaSummary }: { slaSummary: any }) {
  if (!slaSummary) return null;
  const pct = Math.min(slaSummary.pct_elapsed, 100);
  const color =
    slaSummary.sla_status === 'Breached' ? 'bg-red-500' :
    slaSummary.sla_status === 'Warning'  ? 'bg-amber-500' :
    'bg-emerald-500';
  const label =
    slaSummary.sla_status === 'Breached' ? '🚨 SLA Breached' :
    slaSummary.sla_status === 'Warning'  ? '⚠️ SLA Warning' : '✅ On Track';
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 mb-1">
        <span>{label}</span>
        <span>{pct.toFixed(0)}% elapsed</span>
      </div>
      <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Helper: Evidence Trust badge ────────────────────────────────────────────
function TrustBadge({ level, score }: { level: string; score: number }) {
  const cfg: Record<string, { cls: string; icon: string }> = {
    High:       { cls: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300', icon: '✅' },
    Medium:     { cls: 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300',             icon: '🔵' },
    Low:        { cls: 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300',         icon: '⚠️' },
    Suspicious: { cls: 'bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300',                icon: '🚩' },
  };
  const { cls, icon } = cfg[level] || cfg.Medium;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-bold ${cls}`}>
      {icon} Trust: {level} ({score}%)
    </span>
  );
}

// ── Star rating picker ──────────────────────────────────────────────────────
function StarPicker({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex space-x-1">
      {[1, 2, 3, 4, 5].map(n => (
        <button key={n} onClick={() => onChange(n)} type="button">
          <Star className={`h-5 w-5 ${n <= value ? 'text-amber-400 fill-amber-400' : 'text-slate-300'}`} />
        </button>
      ))}
    </div>
  );
}

// ── Status colour mapping ───────────────────────────────────────────────────
function statusClass(status: string) {
  const m: Record<string, string> = {
    'Resolved':   'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300',
    'Closed':     'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    'In Progress':'bg-purple-100 text-purple-800 dark:bg-purple-950/30 dark:text-purple-300',
    'Reopened':   'bg-rose-100 text-rose-800 dark:bg-rose-950/30 dark:text-rose-300',
    'Registered': 'bg-blue-100 text-blue-800 dark:bg-blue-950/30 dark:text-blue-300',
    'Accepted':   'bg-cyan-100 text-cyan-800 dark:bg-cyan-950/30 dark:text-cyan-300',
  };
  return m[status] || 'bg-blue-100 text-blue-800';
}

export default function CitizenDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  const [stats, setStats] = useState<any>({
    total_complaints: 0, active_complaints: 0,
    resolved_complaints: 0, closed_complaints: 0,
    pending_complaints: 0, reopened_complaints: 0,
  });
  const [complaints, setComplaints] = useState<any[]>([]);
  const [nearbyComplaints, setNearbyComplaints] = useState<any[]>([]);
  const [selectedComplaint, setSelectedComplaint] = useState<any>(null);

  // Form
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('English');
  const [latitude, setLatitude] = useState(12.971598);
  const [longitude, setLongitude] = useState(77.594562);
  const [address, setAddress] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);

  // Department & Category Selection from User End
  const [departments, setDepartments] = useState<any[]>([]);
  const [selectedDeptCode, setSelectedDeptCode] = useState<string>('auto');
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('auto');
  const [aiPreview, setAiPreview] = useState<any>(null);
  const [isAiPreviewLoading, setIsAiPreviewLoading] = useState<boolean>(false);
  const previewTimeoutRef = useRef<any>(null);

  // Voice recording
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);

  // Duplicate
  const [isDuplicateChecking, setIsDuplicateChecking] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Citizen verification modal
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [verifyComplaint, setVerifyComplaint] = useState<any>(null);
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackRemarks, setFeedbackRemarks] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

  async function loadDashboardData() {
    try {
      const [statsData, complaintsData, nearby, deptsData] = await Promise.all([
        api.getDashboardStats('citizen'),
        api.getComplaints(),
        api.getNearbyComplaints(12.971598, 77.594562, 5000),
        api.getDepartmentsAndCategories().catch(() => []),
      ]);
      setStats(statsData);
      setComplaints(complaintsData);
      setNearbyComplaints(nearby);
      if (deptsData && Array.isArray(deptsData)) {
        setDepartments(deptsData);
      }
    } catch (err) { console.error(err); }
  }

  useEffect(() => {
    const userInfo = tokenStorage.getUserInfo();
    if (!userInfo || userInfo.role !== 'Citizen') {
      toast.error('Unauthorized access. Redirecting...');
      router.push('/login');
    } else {
      setUser(userInfo);
      loadDashboardData();
    }
  }, []);

  const handleDescriptionChange = (val: string) => {
    setDescription(val);
    if (previewTimeoutRef.current) clearTimeout(previewTimeoutRef.current);
    if (val.trim().length >= 3) {
      setIsAiPreviewLoading(true);
      previewTimeoutRef.current = setTimeout(async () => {
        try {
          const preview = await api.previewAI(val);
          setAiPreview(preview);
        } catch (e) {
          console.error("AI preview error", e);
        } finally {
          setIsAiPreviewLoading(false);
        }
      }, 350);
    } else {
      setAiPreview(null);
    }
  };

  const handleLogout = () => {
    tokenStorage.clearToken();
    toast.success('Logged out successfully');
    router.push('/login');
  };

  const handleAutoLocate = () => {
    if (!navigator.geolocation) { toast.error('Geolocation not supported'); return; }
    const id = toast.loading('Detecting GPS location...');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude);
        setLongitude(pos.coords.longitude);
        setAddress(`GPS: (${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)})`);
        toast.dismiss(id);
        toast.success('Location locked!');
      },
      () => { toast.dismiss(id); toast.error('GPS failed. Pin location on map.'); }
    );
  };

  // ── Voice recording helpers ─────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      audioChunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const f = new File([blob], `voice_${Date.now()}.webm`, { type: 'audio/webm' });
        setAudioFile(f);
        stream.getTracks().forEach(t => t.stop());
        toast.success('Voice note recorded!');
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => setRecordingSeconds(s => s + 1), 1000);
    } catch { toast.error('Microphone access denied.'); }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    clearInterval(timerRef.current);
    setIsRecording(false);
  };

  const runDuplicateCheck = async () => {
    if (!description || description.length < 10) return;
    setIsDuplicateChecking(true);
    try {
      const fd = new FormData();
      fd.append('latitude', latitude.toString());
      fd.append('longitude', longitude.toString());
      fd.append('description', description);
      fd.append('category_name', 'Others');
      const res = await api.checkDuplicate(fd);
      setDuplicateWarning(res.is_duplicate ? res : null);
    } catch { /* silent */ }
    finally { setIsDuplicateChecking(false); }
  };

  const handleSubmitGrievance = async (duplicateOfId?: number) => {
    if (!description && !audioFile) {
      toast.error('Please enter a description or record a voice note.');
      return;
    }
    setIsSubmitting(true);
    const tid = toast.loading(duplicateOfId ? 'Joining issue...' : 'Running AI pipeline & routing...');
    try {
      const fd = new FormData();
      fd.append('description', description || 'Voice complaint');
      fd.append('language', audioFile ? 'Voice' : language);
      fd.append('location_latitude', latitude.toString());
      fd.append('location_longitude', longitude.toString());
      fd.append('location_address', address || 'Bengaluru, Karnataka');
      
      // Pass category override if selected by citizen, or confirmed from AI preview
      if (selectedCategoryId !== 'auto') {
        fd.append('category_id', selectedCategoryId);
      } else if (aiPreview?.predicted_category_id) {
        fd.append('category_id', aiPreview.predicted_category_id.toString());
      }

      if (duplicateOfId) fd.append('duplicate_of_id', duplicateOfId.toString());
      if (imageFile) fd.append('file', imageFile);
      if (audioFile) fd.append('audio_file', audioFile);

      const res = await api.raiseComplaint(fd);
      toast.dismiss(tid);

      if (duplicateOfId) {
        toast.success(`Joined complaint #${duplicateOfId}!`);
      } else {
        const trust = res.evidence_check;
        toast.success(
          `Complaint #${res.id} filed! Routed to ${res.department_name} (${res.priority} priority)` +
          (trust ? ` | Trust: ${trust.trust_level}` : '')
        );
      }

      setDescription(''); setImageFile(null); setAudioFile(null);
      setAiPreview(null); setSelectedDeptCode('auto'); setSelectedCategoryId('auto');
      setDuplicateWarning(null); setIsFormOpen(false);
      loadDashboardData();
    } catch (err: any) {
      toast.dismiss(tid);
      toast.error(err.message || 'Failed to register complaint.');
    } finally { setIsSubmitting(false); }
  };

  // ── Citizen verify / reopen ──────────────────────────────────────────────
  const openVerifyModal = (c: any) => {
    setVerifyComplaint(c);
    setFeedbackRating(5);
    setFeedbackRemarks('');
    setIsVerifyModalOpen(true);
  };

  const handleVerifyResolution = async (approve: boolean) => {
    if (!verifyComplaint) return;
    setIsVerifying(true);
    try {
      await api.verifyResolution(verifyComplaint.id, {
        approve,
        feedback_rating: feedbackRating,
        feedback_remarks: feedbackRemarks,
      });
      toast.success(approve ? 'Complaint closed! Thank you.' : 'Complaint reopened. Officer will re-address it.');
      setIsVerifyModalOpen(false);
      setSelectedComplaint(null);
      loadDashboardData();
    } catch (err: any) {
      toast.error(err.message || 'Action failed.');
    } finally { setIsVerifying(false); }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans">
      {/* Navbar */}
      <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 md:px-8 flex items-center justify-between z-10 sticky top-0">
        <Link href="/" className="flex items-center space-x-2">
          <div className="bg-blue-600 text-white p-1.5 rounded-lg">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg text-slate-900 dark:text-white">CivicAI Citizen Portal</span>
        </Link>
        <div className="flex items-center space-x-4">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 hidden sm:block">
            Welcome, {user?.name}
          </span>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-1 text-xs font-bold text-red-600 hover:text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20 px-3 py-1.5 rounded-lg cursor-pointer transition"
          >
            <LogOut className="h-3.5 w-3.5" /><span>Logout</span>
          </button>
        </div>
      </header>

      {/* Stats Bar */}
      <section className="grid grid-cols-3 md:grid-cols-6 gap-3 p-4 md:p-6 max-w-7xl mx-auto w-full">
        {[
          { label: 'Total',    val: stats.total_complaints,    color: 'text-slate-900 dark:text-white' },
          { label: 'Active',   val: stats.active_complaints,   color: 'text-blue-600' },
          { label: 'Resolved', val: stats.resolved_complaints, color: 'text-emerald-600' },
          { label: 'Closed',   val: stats.closed_complaints,   color: 'text-slate-500' },
          { label: 'Pending',  val: stats.pending_complaints,  color: 'text-amber-600' },
          { label: 'Reopened', val: stats.reopened_complaints || 0, color: 'text-rose-600' },
        ].map(({ label, val, color }) => (
          <div key={label} className="bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <span className="text-[10px] text-slate-500 font-semibold uppercase block">{label}</span>
            <span className={`text-xl font-bold mt-1 block ${color}`}>{val}</span>
          </div>
        ))}
      </section>

      {/* Main Grid */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-6 pb-8 grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* ── Left: Complaints List ─────────────────────────────────────────── */}
        <div className="lg:col-span-2 flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">My Grievances</h3>
            <button
              onClick={() => setIsFormOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-1.5 text-xs font-bold shadow flex items-center space-x-1 cursor-pointer transition"
            >
              <Plus className="h-4 w-4" /><span>Report Issue</span>
            </button>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex-1 max-h-[640px] overflow-y-auto p-3 space-y-2">
            {complaints.length === 0 ? (
              <div className="text-center py-16 text-slate-400">
                <Clock className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-700 mb-2" />
                <p className="text-xs font-semibold">No complaints reported yet.</p>
              </div>
            ) : (
              complaints.map((c) => (
                <div
                  key={c.id}
                  onClick={() => setSelectedComplaint(c)}
                  className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                    selectedComplaint?.id === c.id
                      ? 'border-blue-500 bg-blue-50/30 dark:bg-blue-900/10'
                      : 'border-slate-100 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold text-slate-400">#{c.id}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${statusClass(c.status)}`}>
                      {c.status}
                    </span>
                  </div>
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white">{c.category_name}</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-0.5">{c.description}</p>
                  {c.audio_url && (
                    <span className="inline-flex items-center gap-1 mt-1 text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold">
                      <Volume2 className="h-3 w-3" /> Voice Note
                    </span>
                  )}

                  {/* SLA bar on card */}
                  {c.sla_summary && c.status !== 'Closed' && (
                    <SLABar slaSummary={c.sla_summary} />
                  )}

                  {/* Evidence trust badge */}
                  {c.evidence_check && (
                    <div className="mt-1.5">
                      <TrustBadge level={c.evidence_check.trust_level} score={Math.round(c.evidence_check.trust_score)} />
                    </div>
                  )}

                  {/* Pending verification banner */}
                  {c.status === 'Resolved' && c.citizen_verified === null && (
                    <div className="mt-2 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg px-2 py-1 flex items-center justify-between">
                      <span className="text-[10px] font-bold text-amber-700 dark:text-amber-400">⏳ Awaiting your verification</span>
                      <button
                        onClick={(e) => { e.stopPropagation(); openVerifyModal(c); }}
                        className="text-[10px] bg-amber-600 hover:bg-amber-700 text-white px-2 py-0.5 rounded font-bold transition"
                      >
                        Verify
                      </button>
                    </div>
                  )}

                  <div className="flex items-center justify-between mt-2 text-[10px] text-slate-400 font-semibold border-t border-slate-100 dark:border-slate-800/50 pt-1.5">
                    <span className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">{c.department_name}</span>
                    <span>{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* ── Right: Map + Details ──────────────────────────────────────────── */}
        <div className="lg:col-span-3 flex flex-col space-y-4">
          {/* Map */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden h-64">
            <MapComponent
              center={[latitude, longitude]}
              zoom={13}
              onLocationSelect={(lat, lng) => {
                setLatitude(lat);
                setLongitude(lng);
                setAddress(`Pin: (${lat.toFixed(5)}, ${lng.toFixed(5)})`);
              }}
              markers={nearbyComplaints.map((c) => ({
                id: c.id,
                latitude: c.location_latitude,
                longitude: c.location_longitude,
                title: c.category_name,
                status: c.status,
                category: c.category_name,
              }))}
              interactive={true}
            />
          </div>

          {/* Selected complaint detail */}
          {selectedComplaint ? (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 flex-1 overflow-y-auto space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs text-slate-400 font-bold">Complaint #{selectedComplaint.id}</span>
                  <h3 className="font-bold text-lg text-slate-900 dark:text-white mt-0.5">{selectedComplaint.category_name}</h3>
                  <p className="text-xs text-slate-500 mt-1">{selectedComplaint.description}</p>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-bold ${statusClass(selectedComplaint.status)}`}>
                  {selectedComplaint.status}
                </span>
              </div>

              {/* SLA summary */}
              {selectedComplaint.sla_summary && selectedComplaint.status !== 'Closed' && (
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-3 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5 flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" /> SLA Status
                  </p>
                  <SLABar slaSummary={selectedComplaint.sla_summary} />
                  {selectedComplaint.sla_summary.hours_remaining !== null && (
                    <p className="text-[10px] text-slate-500 mt-1">
                      {selectedComplaint.sla_summary.hours_remaining > 0
                        ? `${selectedComplaint.sla_summary.hours_remaining.toFixed(1)}h remaining`
                        : `Overdue by ${Math.abs(selectedComplaint.sla_summary.hours_remaining).toFixed(1)}h`}
                    </p>
                  )}
                </div>
              )}

              {/* Evidence Trust */}
              {selectedComplaint.evidence_check && (
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-3 border border-slate-100 dark:border-slate-700">
                  <p className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5 flex items-center gap-1">
                    <Shield className="h-3.5 w-3.5" /> Evidence Trust Score
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
                      {Math.round(selectedComplaint.evidence_check.trust_score)}%
                    </div>
                    <TrustBadge level={selectedComplaint.evidence_check.trust_level} score={Math.round(selectedComplaint.evidence_check.trust_score)} />
                  </div>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1.5 leading-relaxed">
                    {selectedComplaint.evidence_check.verification_details}
                  </p>
                </div>
              )}

              {/* AI Prediction */}
              {selectedComplaint.ai_prediction && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 rounded-xl p-3 border border-blue-100 dark:border-blue-800">
                  <p className="text-xs font-bold text-blue-700 dark:text-blue-300 mb-2">⚡ AI Analysis</p>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <p className="text-[10px] text-slate-500">Category</p>
                      <p className="text-xs font-bold text-slate-800 dark:text-white">{selectedComplaint.ai_prediction.predicted_category_name}</p>
                      <p className="text-[10px] text-blue-600">{(selectedComplaint.ai_prediction.category_confidence * 100).toFixed(0)}%</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500">Priority</p>
                      <p className="text-xs font-bold text-slate-800 dark:text-white">{selectedComplaint.ai_prediction.predicted_priority}</p>
                      <p className="text-[10px] text-blue-600">{(selectedComplaint.ai_prediction.priority_confidence * 100).toFixed(0)}%</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500">Input Mode</p>
                      <p className="text-xs font-bold text-slate-800 dark:text-white">
                        {selectedComplaint.ai_prediction.transcription_used ? '🎤 Voice' : '📝 Text'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Reopen info */}
              {selectedComplaint.reopen_count > 0 && (
                <div className="flex items-center gap-2 text-xs text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 rounded-lg px-3 py-2 border border-rose-200 dark:border-rose-800">
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Reopened {selectedComplaint.reopen_count} time(s) — Officer is re-addressing the issue.</span>
                </div>
              )}

              {/* Audio playback */}
              {selectedComplaint.audio_url && (
                <div className="flex items-center gap-2 bg-indigo-50 dark:bg-indigo-950/20 rounded-lg px-3 py-2 border border-indigo-200 dark:border-indigo-800">
                  <Volume2 className="h-4 w-4 text-indigo-600" />
                  <audio controls className="flex-1 h-8" src={`http://127.0.0.1:8000${selectedComplaint.audio_url}`} />
                </div>
              )}

              {/* Status history */}
              {selectedComplaint.status_history?.length > 0 && (
                <div>
                  <p className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-2">Timeline</p>
                  <div className="space-y-1.5">
                    {selectedComplaint.status_history.map((h: any) => (
                      <div key={h.id} className="flex items-start gap-2 text-[10px]">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1 shrink-0" />
                        <div>
                          <span className="font-bold text-slate-700 dark:text-slate-200">{h.status}</span>
                          <span className="text-slate-400 ml-1">— {h.changed_by_name}</span>
                          <p className="text-slate-500">{h.remarks}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Citizen verification action */}
              {selectedComplaint.status === 'Resolved' && selectedComplaint.citizen_verified === null && (
                <div className="border-t border-slate-100 dark:border-slate-800 pt-3">
                  <p className="text-xs font-bold text-slate-700 dark:text-slate-200 mb-2">
                    ✅ Officer has marked this Resolved. Was the issue fixed?
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => openVerifyModal(selectedComplaint)}
                      className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-2 rounded-lg transition"
                    >
                      <ThumbsUp className="h-4 w-4" /> Verify & Respond
                    </button>
                  </div>
                </div>
              )}

              {/* Feedback shown if already verified */}
              {selectedComplaint.citizen_verified !== null && selectedComplaint.status === 'Closed' && (
                <div className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 rounded-lg px-3 py-2 text-xs text-emerald-700 dark:text-emerald-300 font-semibold">
                  ✅ You approved this resolution. Rated {selectedComplaint.citizen_feedback_rating}/5 stars.
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 flex-1 flex flex-col items-center justify-center text-slate-400">
              <Info className="h-8 w-8 mb-2 text-slate-300 dark:text-slate-700" />
              <p className="text-sm font-semibold">Select a complaint to view details</p>
              <p className="text-xs mt-1">Or pin a location on the map above</p>
            </div>
          )}
        </div>
      </main>

      {/* ── File New Grievance Modal ──────────────────────────────────────── */}
      {isFormOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-extrabold text-xl text-slate-900 dark:text-white">Report a Civic Issue</h2>
              <button onClick={() => setIsFormOpen(false)} className="text-slate-400 hover:text-slate-600 text-xl font-bold">✕</button>
            </div>
            <div className="space-y-4">
              {/* Description Input */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-bold text-slate-600 dark:text-slate-300">
                    Issue Description * (Kannada / English / Kanglish)
                  </label>
                  {isAiPreviewLoading && (
                    <span className="flex items-center gap-1 text-[11px] text-blue-600 font-semibold animate-pulse">
                      <Loader2 className="h-3 w-3 animate-spin" /> Translating & Analyzing...
                    </span>
                  )}
                </div>
                <textarea
                  value={description}
                  onChange={(e) => handleDescriptionChange(e.target.value)}
                  onBlur={runDuplicateCheck}
                  placeholder="ಉದಾಹರಣೆ: 'ರಸ್ತೆಯಲ್ಲಿ ದೊಡ್ಡ ಗುಂಡಿ ಬಿದ್ದಿದೆ' or 'Garbage not collected for 3 days' or 'gundi biddide'..."
                  className="w-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>

              {/* Live AI Translation & Routing Preview Card */}
              {aiPreview && description.trim().length >= 3 && (
                <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 dark:from-blue-950/40 dark:via-indigo-950/40 dark:to-purple-950/40 border border-blue-200 dark:border-blue-800 rounded-xl p-3.5 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-900 dark:text-blue-300">
                      <Sparkles className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                      Language: <span className="underline">{aiPreview.detected_language === 'kn' ? 'Kannada (ಕನ್ನಡ)' : aiPreview.detected_language === 'kn-en' ? 'Kanglish' : 'English'}</span>
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                        {((aiPreview.confidence || 0.85) * 100).toFixed(0)}% AI Confidence
                      </span>
                      {aiPreview.predicted_priority && (
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          aiPreview.predicted_priority === 'Critical' ? 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400' :
                          aiPreview.predicted_priority === 'High' ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400' :
                          'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        }`}>
                          {aiPreview.predicted_priority} Priority
                        </span>
                      )}
                    </div>
                  </div>

                  {aiPreview.detected_language !== 'en' && aiPreview.translated_text && (
                    <div className="text-xs text-slate-700 dark:text-slate-300 bg-white/80 dark:bg-slate-900/80 p-2 rounded-lg border border-blue-100 dark:border-blue-900/50">
                      <p className="text-[10px] text-slate-500 font-bold mb-0.5">🔤 English Translation:</p>
                      <p className="italic">"{aiPreview.translated_text}"</p>
                    </div>
                  )}

                  {/* 4-Tier Jurisdiction Routing Breadcrumbs */}
                  <div className="bg-white/90 dark:bg-slate-900/90 rounded-lg p-2.5 border border-slate-200 dark:border-slate-800">
                    <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                      🏛️ Department Routing Hierarchy
                    </p>
                    <div className="flex flex-wrap items-center gap-1.5 text-xs font-semibold">
                      <span className="px-2 py-0.5 rounded bg-blue-600 text-white text-[11px] font-bold">
                        {aiPreview.agency || aiPreview.predicted_department}
                      </span>
                      <span className="text-slate-400">➔</span>
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-[11px]">
                        {aiPreview.category || 'Civic'}
                      </span>
                      {aiPreview.subcategory && (
                        <>
                          <span className="text-slate-400">➔</span>
                          <span className="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-[11px] font-bold">
                            {aiPreview.subcategory}
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Evidence Requirements & Action */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-blue-100 dark:border-blue-900/50">
                    <div className="flex items-center gap-1.5">
                      {aiPreview.requires_image && (
                        <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                          📷 Image Required
                        </span>
                      )}
                      {aiPreview.requires_gps && (
                        <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
                          📍 GPS Required
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Voice Recording */}
              <div className="border border-dashed border-indigo-200 dark:border-indigo-800 rounded-xl p-3 bg-indigo-50/50 dark:bg-indigo-950/20">
                <p className="text-xs font-bold text-indigo-700 dark:text-indigo-300 mb-2">🎤 Voice Complaint (Optional)</p>
                {!isRecording && !audioFile && (
                  <button
                    onClick={startRecording}
                    type="button"
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition"
                  >
                    <Mic className="h-3.5 w-3.5" /> Start Recording
                  </button>
                )}
                {isRecording && (
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-xs font-bold text-red-600">Recording... {recordingSeconds}s</span>
                    <button onClick={stopRecording} className="ml-auto bg-red-600 hover:bg-red-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1 transition">
                      <MicOff className="h-3.5 w-3.5" /> Stop
                    </button>
                  </div>
                )}
                {audioFile && !isRecording && (
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400">{audioFile.name}</span>
                    <button onClick={() => setAudioFile(null)} className="ml-auto text-xs text-rose-500 hover:text-rose-700 font-bold">Remove</button>
                  </div>
                )}
              </div>

              {/* Language */}
              <div>
                <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Kannada">ಕನ್ನಡ (Kannada)</option>
                  <option value="English">English</option>
                  <option value="Hinglish">Kanglish / Hinglish</option>
                </select>
              </div>

              {/* Location */}
              <div>
                <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Location</label>
                <div className="flex gap-2">
                  <input
                    readOnly
                    value={address || `(${latitude.toFixed(4)}, ${longitude.toFixed(4)})`}
                    className="flex-1 border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl px-3 py-2 text-xs"
                  />
                  <button onClick={handleAutoLocate} type="button" className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-xl text-xs font-bold flex items-center gap-1 transition">
                    <Navigation className="h-3.5 w-3.5" /> GPS
                  </button>
                </div>
              </div>

              {/* Image */}
              <div>
                <label className="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Evidence Photo (Optional)</label>
                <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-blue-400 dark:hover:border-blue-600 transition bg-slate-50 dark:bg-slate-800/50">
                  {imageFile ? (
                    <div className="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400 font-semibold">
                      <CheckCircle2 className="h-4 w-4" /> {imageFile.name}
                    </div>
                  ) : (
                    <>
                      <ImageIcon className="h-6 w-6 text-slate-400 mb-1" />
                      <span className="text-xs text-slate-500">Click to upload photo</span>
                    </>
                  )}
                  <input type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && setImageFile(e.target.files[0])} />
                </label>
              </div>

              {/* Duplicate Warning */}
              {isDuplicateChecking && (
                <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-2">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500" /> Checking for similar reports nearby...
                </div>
              )}
              {duplicateWarning?.is_duplicate && (
                <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-xl p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <span className="text-xs font-bold text-amber-800 dark:text-amber-300">Similar Report Found Nearby!</span>
                  </div>
                  <p className="text-xs text-amber-700 dark:text-amber-400 mb-3">{duplicateWarning.message}</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSubmitGrievance(duplicateWarning.duplicate_of_id)}
                      disabled={isSubmitting}
                      className="flex-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold py-2 rounded-lg flex items-center justify-center gap-1 transition"
                    >
                      <ArrowRight className="h-3.5 w-3.5" /> Join Existing (#{duplicateWarning.duplicate_of_id})
                    </button>
                    <button
                      onClick={() => handleSubmitGrievance()}
                      disabled={isSubmitting}
                      className="flex-1 border border-amber-300 dark:border-amber-700 text-amber-800 dark:text-amber-300 text-xs font-bold py-2 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/20 transition"
                    >
                      File as New
                    </button>
                  </div>
                </div>
              )}

              {!duplicateWarning?.is_duplicate && (
                <button
                  onClick={() => handleSubmitGrievance()}
                  disabled={isSubmitting || (!description && !audioFile)}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white font-bold py-3 rounded-xl text-sm flex items-center justify-center gap-2 transition"
                >
                  {isSubmitting ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Processing & Routing...</>
                  ) : (
                    <><MessageSquare className="h-4 w-4" /> Submit Complaint</>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Citizen Verify / Reopen Modal ─────────────────────────────────── */}
      {isVerifyModalOpen && verifyComplaint && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-md p-6 border border-slate-200 dark:border-slate-800">
            <h2 className="font-extrabold text-xl text-slate-900 dark:text-white mb-1">Verify Resolution</h2>
            <p className="text-xs text-slate-500 mb-4">Complaint #{verifyComplaint.id} — {verifyComplaint.category_name}</p>

            {/* Resolution images */}
            {verifyComplaint.images?.filter((i: any) => i.image_type === 'Resolution').length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Resolution Evidence Photos:</p>
                <div className="flex gap-2 overflow-x-auto">
                  {verifyComplaint.images.filter((i: any) => i.image_type === 'Resolution').map((img: any) => (
                    <img
                      key={img.id}
                      src={`http://127.0.0.1:8000${img.image_url}`}
                      alt="Resolution"
                      className="h-28 w-auto object-cover rounded-lg border border-slate-200 dark:border-slate-700"
                    />
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-600 dark:text-slate-300 block mb-1.5">Rate the resolution</label>
                <StarPicker value={feedbackRating} onChange={setFeedbackRating} />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-600 dark:text-slate-300 block mb-1">Remarks (Optional)</label>
                <textarea
                  value={feedbackRemarks}
                  onChange={(e) => setFeedbackRemarks(e.target.value)}
                  placeholder="Was the issue properly resolved? Any concerns?"
                  className="w-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => handleVerifyResolution(true)}
                  disabled={isVerifying}
                  className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-xl text-sm transition"
                >
                  <ThumbsUp className="h-4 w-4" /> Approve & Close
                </button>
                <button
                  onClick={() => handleVerifyResolution(false)}
                  disabled={isVerifying}
                  className="flex-1 flex items-center justify-center gap-2 bg-rose-600 hover:bg-rose-700 text-white font-bold py-2.5 rounded-xl text-sm transition"
                >
                  <ThumbsDown className="h-4 w-4" /> Reject & Reopen
                </button>
              </div>
              <button onClick={() => setIsVerifyModalOpen(false)} className="w-full text-xs text-slate-400 hover:text-slate-600 py-1 transition">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
