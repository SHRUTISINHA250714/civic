'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { 
  ShieldAlert, LogOut, MapPin, Image as ImageIcon, 
  Loader2, Info, CheckCircle2, Clock, 
  ClipboardCheck, User, Wrench, Calendar, ArrowRight
} from 'lucide-react';
import { api, tokenStorage } from '@/lib/api';
import { toast } from 'sonner';

// Dynamically import Leaflet Map Component to bypass SSR reference errors
const MapComponent = dynamic(() => import('@/components/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-100 dark:bg-slate-800 animate-pulse flex items-center justify-center text-slate-400 font-semibold rounded-xl">
      Loading Leaflet Map Engine...
    </div>
  )
});

export default function OfficerDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  
  // Dashboard stats
  const [stats, setStats] = useState<any>({
    total_assigned: 0,
    pending: 0,
    accepted: 0,
    in_progress: 0,
    resolved: 0,
    closed: 0
  });
  
  const [complaints, setComplaints] = useState<any[]>([]);
  const [filteredComplaints, setFilteredComplaints] = useState<any[]>([]);
  const [selectedComplaint, setSelectedComplaint] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'in_progress' | 'completed'>('all');
  
  // Resolution form states
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolutionRemarks, setResolutionRemarks] = useState('');
  const [resolutionImage, setResolutionImage] = useState<File | null>(null);
  const [isResolving, setIsResolving] = useState(false);
  
  // Action state loader
  const [isTransitioning, setIsTransitioning] = useState(false);

  function applyFilter(data: any[], tab: string) {
    if (tab === 'all') {
      setFilteredComplaints(data);
    } else if (tab === 'pending') {
      setFilteredComplaints(data.filter((c: any) => c.status === 'Registered'));
    } else if (tab === 'in_progress') {
      setFilteredComplaints(data.filter((c: any) => c.status === 'Accepted' || c.status === 'In Progress'));
    } else if (tab === 'reopened') {
      setFilteredComplaints(data.filter((c: any) => c.status === 'Reopened'));
    } else if (tab === 'completed') {
      setFilteredComplaints(data.filter((c: any) => c.status === 'Resolved' || c.status === 'Closed'));
    }
  }

  async function loadDashboardData() {
    try {
      const statsData = await api.getDashboardStats("officer");
      setStats(statsData);
      
      const complaintsData = await api.getComplaints();
      setComplaints(complaintsData);
      applyFilter(complaintsData, activeTab);
    } catch (err: any) {
      console.error(err);
    }
  }

  // Load user session
  useEffect(() => {
    const userInfo = tokenStorage.getUserInfo();
    if (!userInfo || userInfo.role !== "Officer") {
      toast.error("Unauthorized access. Redirecting...");
      router.push("/login");
    } else {
      setUser(userInfo);
      loadDashboardData();
    }
  }, []);

  const handleTabChange = (tab: 'all' | 'pending' | 'in_progress' | 'completed') => {
    setActiveTab(tab);
    applyFilter(complaints, tab);
  };

  const handleLogout = () => {
    tokenStorage.clearToken();
    toast.success("Logged out successfully");
    router.push("/login");
  };

  const handleTransitionStatus = async (id: number, nextStatus: string) => {
    setIsTransitioning(true);
    const remarks = `Officer ${user?.name} marked complaint status as '${nextStatus}'.`;
    try {
      const res = await api.updateComplaintStatus(id, nextStatus, remarks);
      toast.success(`Complaint status transitioned to '${nextStatus}' successfully!`);
      setSelectedComplaint(res);
      loadDashboardData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update complaint status.");
    } finally {
      setIsTransitioning(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setResolutionImage(e.target.files[0]);
    }
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolutionRemarks) {
      toast.error("Please enter resolution remarks.");
      return;
    }
    if (!resolutionImage) {
      toast.error("Please upload a resolution proof photo.");
      return;
    }

    setIsResolving(true);
    const formData = new FormData();
    formData.append("remarks", resolutionRemarks);
    formData.append("file", resolutionImage);

    try {
      const res = await api.resolveComplaint(selectedComplaint.id, formData);
      toast.success(`Grievance #${selectedComplaint.id} has been marked as Resolved!`);
      
      setIsResolveModalOpen(false);
      setResolutionRemarks('');
      setResolutionImage(null);
      setSelectedComplaint(res);
      loadDashboardData();
    } catch (err: any) {
      toast.error(err.message || "Failed to resolve complaint.");
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans">
      {/* Navbar */}
      <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 md:px-8 flex items-center justify-between z-10">
        <Link href="/" className="flex items-center space-x-2">
          <div className="bg-blue-600 text-white p-1.5 rounded-lg">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg text-slate-900 dark:text-white">CivicAI Officer Queue</span>
        </Link>
        <div className="flex items-center space-x-4">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Gov. Officer: {user?.name}</span>
          <button 
            onClick={handleLogout}
            className="flex items-center space-x-1 text-xs font-bold text-red-600 hover:text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20 px-3 py-1.5 rounded-lg cursor-pointer transition"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Metrics Row */}
      <section className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 p-4 md:p-6 max-w-7xl mx-auto w-full">
        <div className="bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">Total</span>
          <span className="text-xl font-bold text-slate-900 dark:text-white mt-1 block">{stats.total_assigned}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">Pending</span>
          <span className="text-xl font-bold text-blue-600 mt-1 block">{stats.pending}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">Accepted</span>
          <span className="text-xl font-bold text-orange-500 mt-1 block">{stats.accepted}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">In Progress</span>
          <span className="text-xl font-bold text-purple-600 mt-1 block">{stats.in_progress}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">Resolved</span>
          <span className="text-xl font-bold text-emerald-600 mt-1 block">{stats.resolved}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-3 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-slate-500 font-semibold block uppercase">Closed</span>
          <span className="text-xl font-bold text-slate-500 mt-1 block">{stats.closed}</span>
        </div>
        <div className="bg-amber-50 dark:bg-amber-950/20 p-3 border border-amber-200 dark:border-amber-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-amber-600 font-semibold block uppercase">SLA Warning</span>
          <span className="text-xl font-bold text-amber-600 mt-1 block">{stats.sla_warning || 0}</span>
        </div>
        <div className="bg-red-50 dark:bg-red-950/20 p-3 border border-red-200 dark:border-red-800 rounded-xl shadow-sm">
          <span className="text-[10px] text-red-600 font-semibold block uppercase">SLA Breached</span>
          <span className="text-xl font-bold text-red-600 mt-1 block">{stats.sla_breached || 0}</span>
        </div>
      </section>

      {/* Main Grid content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-6 pb-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left Side: Tasks list & Tabs */}
        <div className="lg:col-span-2 flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Assigned Grievance Queue</h3>
          </div>

          {/* Filtering tabs */}
          <div className="flex space-x-1 bg-slate-200 dark:bg-slate-800/80 p-1 rounded-xl text-xs font-bold text-slate-600 dark:text-slate-400">
            {(['all','pending','in_progress','reopened','completed'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => handleTabChange(tab as any)}
                className={`flex-1 py-1.5 text-center rounded-lg transition-all cursor-pointer capitalize ${
                  activeTab === tab ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-white shadow-sm' : ''
                } ${tab === 'reopened' && (stats.reopened || 0) > 0 ? 'text-rose-600' : ''}`}
              >
                {tab === 'in_progress' ? 'Active' : tab === 'reopened' ? `🔁 Reopened${(stats.reopened||0)>0?' ('+stats.reopened+')':''}` : tab.charAt(0).toUpperCase()+tab.slice(1)}
              </button>
            ))}
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex-1 max-h-[550px] overflow-y-auto p-4 space-y-3 shadow-sm">
            {filteredComplaints.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Clock className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-700 mb-2" />
                <p className="text-xs font-semibold">No assigned complaints matching filter.</p>
              </div>
            ) : (
              filteredComplaints.map((c: any) => (
                <div 
                  key={c.id}
                  onClick={() => setSelectedComplaint(c)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                    selectedComplaint?.id === c.id 
                      ? 'border-blue-500 bg-blue-50/20 dark:bg-blue-900/10' 
                      : c.status === 'Reopened'
                        ? 'border-rose-200 dark:border-rose-800 bg-rose-50/30 dark:bg-rose-950/10 hover:border-rose-400'
                        : 'border-slate-100 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold text-slate-400">ID: #{c.id}</span>
                    <div className="flex items-center gap-1">
                      {/* SLA urgency badge */}
                      {c.sla_status === 'Breached' && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400">🚨 SLA</span>
                      )}
                      {c.sla_status === 'Warning' && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">⚠️ SLA</span>
                      )}
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        c.status === 'Resolved' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300' :
                        c.status === 'Closed' ? 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300' :
                        c.status === 'In Progress' ? 'bg-purple-100 text-purple-800 dark:bg-purple-950/30 dark:text-purple-300' :
                        c.status === 'Accepted' ? 'bg-orange-100 text-orange-800 dark:bg-orange-950/30 dark:text-orange-300' :
                        c.status === 'Reopened' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950/30 dark:text-rose-300' :
                        'bg-blue-100 text-blue-800 dark:bg-blue-950/30 dark:text-blue-300'
                      }`}>
                        {c.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white">{c.category_name}</h4>
                    <span className={`text-[10px] font-bold ${
                      c.priority === 'Critical' ? 'text-red-600' :
                      c.priority === 'High' ? 'text-amber-600' :
                      c.priority === 'Medium' ? 'text-blue-600' : 'text-slate-500'
                    }`}>{c.priority}</span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-1">{c.description}</p>
                  
                  {/* Reopen feedback indicator */}
                  {c.status === 'Reopened' && c.citizen_feedback_remarks && (
                    <div className="mt-1.5 bg-rose-50 dark:bg-rose-950/20 rounded px-2 py-1 text-[10px] text-rose-700 dark:text-rose-400 font-semibold">
                      🔁 Citizen: "{c.citizen_feedback_remarks}"
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between mt-2 text-[10px] text-slate-400 font-semibold border-t border-slate-100 dark:border-slate-800/50 pt-1.5">
                    <span>{c.citizen_name}</span>
                    <span>{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Side: Detailed Task inspector & Map router */}
        <div className="lg:col-span-3 flex flex-col space-y-4">
          <h3 className="font-bold text-lg text-slate-900 dark:text-white">Task Details & Navigation Location</h3>
          
          {selectedComplaint ? (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-6 flex-1 flex flex-col">
              <div className="grid md:grid-cols-2 gap-6 shrink-0">
                {/* Text details column */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-850 pb-2">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Complaint category</span>
                      <h4 className="font-extrabold text-lg text-slate-900 dark:text-white">{selectedComplaint.category_name}</h4>
                    </div>
                    <span className="text-[10px] font-mono bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded uppercase font-bold text-slate-500">ID: #{selectedComplaint.id}</span>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 block uppercase">Location Address</span>
                    <span className="text-xs text-slate-800 dark:text-slate-200 font-bold block mt-0.5">
                      {selectedComplaint.location_address || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 block uppercase">Translated complaint description</span>
                    <p className="text-xs text-slate-700 dark:text-slate-350 italic font-semibold mt-1 bg-slate-50 dark:bg-slate-850 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800/40">
                      "{selectedComplaint.description}"
                    </p>
                  </div>
                  {selectedComplaint.original_description && (
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Original Citizen Text</span>
                      <p className="text-xs text-slate-500 dark:text-slate-450 mt-0.5">
                        "{selectedComplaint.original_description}"
                      </p>
                    </div>
                  )}
                </div>

                {/* Media columns */}
                <div className="space-y-4">
                  <span className="text-[10px] font-bold text-slate-400 block uppercase mb-1">Attached Media</span>
                  {selectedComplaint.images && selectedComplaint.images.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                      {selectedComplaint.images.map((img: any) => (
                        <div key={img.id} className="relative aspect-square bg-slate-100 dark:bg-slate-800 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
                          <img 
                            src={`http://127.0.0.1:8000${img.image_url}`} 
                            alt={img.image_type}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute bottom-0 inset-x-0 bg-slate-900/60 p-1 text-[8px] text-white text-center font-bold">
                            {img.image_type} ({img.is_verified ? "Verified" : "Unverified"})
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="h-28 bg-slate-50 dark:bg-slate-850 rounded-lg border border-dashed border-slate-200 dark:border-slate-800 flex items-center justify-center text-xs text-slate-400">
                      No initial photo attached
                    </div>
                  )}
                </div>
              </div>

              {/* Leaflet Map coordinates centering */}
              <div className="flex-1 min-h-[220px] relative rounded-xl overflow-hidden border border-slate-100 dark:border-slate-800 shrink-0 md:shrink flex flex-col">
                <MapComponent 
                  center={[selectedComplaint.location_latitude, selectedComplaint.location_longitude]} 
                  zoom={15} 
                  markers={[{
                    id: selectedComplaint.id,
                    latitude: selectedComplaint.location_latitude,
                    longitude: selectedComplaint.location_longitude,
                    title: selectedComplaint.description,
                    status: selectedComplaint.status,
                    category: selectedComplaint.category_name
                  }]}
                  interactive={false}
                />
              </div>

              {/* Status Action Buttons */}
              <div className="border-t border-slate-100 dark:border-slate-850 pt-4 flex items-center justify-between shrink-0">
                <div className="flex items-center space-x-1.5">
                  <span className="text-xs font-semibold text-slate-500">Current Status:</span>
                  <span className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded font-bold uppercase tracking-wide text-blue-600">{selectedComplaint.status}</span>
                </div>
                
                <div className="flex space-x-2">
                  {selectedComplaint.status === "Registered" && (
                    <button 
                      onClick={() => handleTransitionStatus(selectedComplaint.id, "Accepted")}
                      disabled={isTransitioning}
                      className="bg-orange-500 hover:bg-orange-600 text-white rounded-lg px-4 py-2 text-xs font-bold shadow transition cursor-pointer flex items-center space-x-1"
                    >
                      {isTransitioning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ClipboardCheck className="h-4 w-4" />}
                      <span>Accept Grievance</span>
                    </button>
                  )}
                  {selectedComplaint.status === "Accepted" && (
                    <button 
                      onClick={() => handleTransitionStatus(selectedComplaint.id, "In Progress")}
                      disabled={isTransitioning}
                      className="bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-xs font-bold shadow transition cursor-pointer flex items-center space-x-1"
                    >
                      {isTransitioning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Wrench className="h-4 w-4" />}
                      <span>Start Action Work</span>
                    </button>
                  )}
                  {(selectedComplaint.status === "In Progress" || selectedComplaint.status === "Reopened") && (
                    <button 
                      onClick={() => setIsResolveModalOpen(true)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-4 py-2 text-xs font-bold shadow transition cursor-pointer flex items-center space-x-1"
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      <span>{selectedComplaint.status === 'Reopened' ? 'Re-Submit Resolution' : 'Mark as Resolved'}</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-12 rounded-xl flex-1 flex flex-col items-center justify-center text-slate-400 shadow-sm">
              <ClipboardCheck className="h-14 w-14 text-slate-350 dark:text-slate-700 mb-3" />
              <p className="text-sm font-semibold">Select a complaint from the queue list to inspect details.</p>
            </div>
          )}
        </div>
      </main>

      {/* Floating Action Modal: Upload Resolution Proof */}
      {isResolveModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden animate-slide-up">
            <div className="bg-slate-900 dark:bg-slate-950 px-6 py-4 flex items-center justify-between text-white">
              <h3 className="font-bold text-base">Submit Resolution proof</h3>
              <button onClick={() => setIsResolveModalOpen(false)} className="text-slate-400 hover:text-white text-sm cursor-pointer">Close</button>
            </div>
            
            <form onSubmit={handleResolveSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Resolution Remarks <span className="text-red-500">*</span></label>
                <textarea
                  rows={3}
                  required
                  value={resolutionRemarks}
                  onChange={(e) => setResolutionRemarks(e.target.value)}
                  placeholder="Describe the action taken to resolve this grievance (e.g. cleared the garbage dump, potholes filled with wet mix concrete...)"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                ></textarea>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Resolution Proof Image <span className="text-red-500">*</span></label>
                <div className="relative rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm flex items-center space-x-2">
                  <ImageIcon className="h-4.5 w-4.5 text-slate-400" />
                  <input 
                    type="file" 
                    accept="image/*" 
                    required
                    onChange={handleFileChange}
                    className="text-xs file:hidden text-slate-500 dark:text-slate-400 w-full cursor-pointer"
                  />
                  {resolutionImage && <span className="text-[10px] text-emerald-600 font-bold block truncate max-w-[80px]">Proof Loaded</span>}
                </div>
                <p className="text-[10px] text-slate-400 mt-1 font-semibold">Verification will fail if the proof is an indoor screen/device snapshot.</p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-950 px-6 py-4 -mx-6 -mb-6 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-2">
                <button 
                  type="button"
                  onClick={() => setIsResolveModalOpen(false)}
                  className="bg-white hover:bg-slate-50 border border-slate-200 dark:bg-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 rounded-xl px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  disabled={isResolving}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl px-5 py-2 text-xs font-bold shadow transition flex items-center space-x-1.5 cursor-pointer"
                >
                  {isResolving ? (
                    <Loader2 className="h-4.5 w-4.5 animate-spin" />
                  ) : (
                    <>
                      <span>Submit Verification</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
