'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { 
  ShieldAlert, LogOut, Plus, MapPin, 
  Image as ImageIcon, Loader2, Info, CheckCircle2, 
  Clock, AlertTriangle, MessageSquare, Globe, Navigation, ArrowRight
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

export default function CitizenDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  
  // Dashboard states
  const [stats, setStats] = useState<any>({
    total_complaints: 0,
    active_complaints: 0,
    resolved_complaints: 0,
    closed_complaints: 0,
    pending_complaints: 0
  });
  const [complaints, setComplaints] = useState<any[]>([]);
  const [nearbyComplaints, setNearbyComplaints] = useState<any[]>([]);
  const [selectedComplaint, setSelectedComplaint] = useState<any>(null);
  
  // Form states
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('English');
  const [latitude, setLatitude] = useState(12.971598); // Bangalore default
  const [longitude, setLongitude] = useState(77.594562);
  const [address, setAddress] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  
  // AI Sandbox & Duplicate check states
  const [isDuplicateChecking, setIsDuplicateChecking] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load user session
  useEffect(() => {
    const userInfo = tokenStorage.getUserInfo();
    if (!userInfo || userInfo.role !== "Citizen") {
      toast.error("Unauthorized access. Redirecting...");
      router.push("/login");
    } else {
      setUser(userInfo);
      loadDashboardData();
    }
  }, []);

  const loadDashboardData = async () => {
    try {
      const statsData = await api.getDashboardStats("citizen");
      setStats(statsData);
      
      const complaintsData = await api.getComplaints();
      setComplaints(complaintsData);

      // Load nearby active complaints to display on map
      const nearby = await api.getNearbyComplaints(latitude, longitude, 5000); // 5km
      setNearbyComplaints(nearby);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleLogout = () => {
    tokenStorage.clearToken();
    toast.success("Logged out successfully");
    router.push("/login");
  };

  // Auto-detect location
  const handleAutoLocate = () => {
    if (!navigator.geolocation) {
      toast.error("Geolocation is not supported by your browser");
      return;
    }
    toast.loading("Detecting your GPS location...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude);
        setLongitude(pos.coords.longitude);
        setAddress(`GPS Located: (${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)})`);
        toast.dismiss();
        toast.success("Location locked successfully!");
      },
      (err) => {
        toast.dismiss();
        toast.error("Failed to detect location. Please pin manually on map.");
      }
    );
  };

  // Trigger duplicate check on coordinates/description change
  const runDuplicateCheck = async () => {
    if (!description || description.length < 10) return;
    setIsDuplicateChecking(true);
    try {
      const formData = new FormData();
      formData.append("latitude", latitude.toString());
      formData.append("longitude", longitude.toString());
      formData.append("description", description);
      formData.append("category_name", "Others"); // placeholder, backend maps category

      const res = await api.checkDuplicate(formData);
      if (res.is_duplicate) {
        setDuplicateWarning(res);
      } else {
        setDuplicateWarning(null);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsDuplicateChecking(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setImageFile(e.target.files[0]);
    }
  };

  const handleSubmitGrievance = async (duplicateOfId?: number) => {
    if (!description) {
      toast.error("Please enter a description of the issue.");
      return;
    }

    setIsSubmitting(true);
    const toastId = toast.loading(duplicateOfId ? "Joining issue..." : "Executing AI verification and routing pipeline...");
    try {
      const formData = new FormData();
      formData.append("description", description);
      formData.append("language", language);
      formData.append("location_latitude", latitude.toString());
      formData.append("location_longitude", longitude.toString());
      formData.append("location_address", address || "Bengaluru, Karnataka");
      if (duplicateOfId) {
        formData.append("duplicate_of_id", duplicateOfId.toString());
      }
      if (imageFile) {
        formData.append("file", imageFile);
      }

      const res = await api.raiseComplaint(formData);
      toast.dismiss(toastId);

      if (duplicateOfId) {
        toast.success(`Joined existing complaint #${duplicateOfId} successfully!`);
      } else {
        toast.success(`Complaint #${res.id} registered! Routed to ${res.department_name} (Priority: ${res.priority})`);
      }

      // Reset form
      setDescription('');
      setImageFile(null);
      setDuplicateWarning(null);
      setIsFormOpen(false);
      loadDashboardData();
    } catch (err: any) {
      toast.dismiss(toastId);
      toast.error(err.message || "Failed to register complaint.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseComplaint = async (id: number) => {
    try {
      await api.updateComplaintStatus(id, "Closed", "Citizen marked as satisfied and closed.");
      toast.success("Complaint closed successfully.");
      setSelectedComplaint(null);
      loadDashboardData();
    } catch (err: any) {
      toast.error(err.message || "Failed to close complaint.");
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
          <span className="font-bold text-lg text-slate-900 dark:text-white">CivicAI Citizen Portal</span>
        </Link>
        <div className="flex items-center space-x-4">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">Welcome, {user?.name}</span>
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
      <section className="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 md:p-6 max-w-7xl mx-auto w-full">
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Total Grievances</span>
          <span className="text-2xl font-bold text-slate-900 dark:text-white mt-1 block">{stats.total_complaints}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Active Complaints</span>
          <span className="text-2xl font-bold text-blue-600 mt-1 block">{stats.active_complaints}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Resolved Issues</span>
          <span className="text-2xl font-bold text-emerald-600 mt-1 block">{stats.resolved_complaints}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Closed Cases</span>
          <span className="text-2xl font-bold text-slate-500 mt-1 block">{stats.closed_complaints}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm col-span-2 md:col-span-1">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Pending Action</span>
          <span className="text-2xl font-bold text-amber-600 mt-1 block">{stats.pending_complaints}</span>
        </div>
      </section>

      {/* Main Grid Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-6 pb-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left Side: Complaints List */}
        <div className="lg:col-span-2 flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Grievance History</h3>
            <button 
              onClick={() => setIsFormOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-1.5 text-xs font-bold shadow flex items-center space-x-1 cursor-pointer"
            >
              <Plus className="h-4 w-4" />
              <span>Report Grievance</span>
            </button>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex-1 max-h-[600px] overflow-y-auto p-4 space-y-3">
            {complaints.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Clock className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-700 mb-2" />
                <p className="text-xs font-semibold">No complaints reported yet.</p>
              </div>
            ) : (
              complaints.map((c) => (
                <div 
                  key={c.id}
                  onClick={() => setSelectedComplaint(c)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                    selectedComplaint?.id === c.id 
                      ? 'border-blue-500 bg-blue-50/20 dark:bg-blue-900/10' 
                      : 'border-slate-100 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold text-slate-400">ID: #{c.id}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                      c.status === 'Resolved' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300' :
                      c.status === 'Closed' ? 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300' :
                      c.status === 'In Progress' ? 'bg-purple-100 text-purple-800 dark:bg-purple-950/30 dark:text-purple-300' :
                      'bg-blue-100 text-blue-800 dark:bg-blue-950/30 dark:text-blue-300'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white">{c.category_name}</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-1">{c.description}</p>
                  
                  <div className="flex items-center justify-between mt-3 text-[10px] text-slate-400 font-semibold border-t border-slate-100 dark:border-slate-800/50 pt-2">
                    <span>Route: <span className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">{c.department_name}</span></span>
                    <span>{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Side: Map & Interactive details */}
        <div className="lg:col-span-3 flex flex-col space-y-4">
          <h3 className="font-bold text-lg text-slate-900 dark:text-white">Active Grievance Map Area</h3>
          
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 rounded-xl flex-1 min-h-[400px] flex flex-col shadow-sm">
            <div className="flex-1 relative rounded-lg overflow-hidden border border-slate-100 dark:border-slate-800">
              <MapComponent 
                center={[latitude, longitude]} 
                zoom={14} 
                markers={nearbyComplaints.map(nc => ({
                  id: nc.id,
                  latitude: nc.location_latitude,
                  longitude: nc.location_longitude,
                  title: nc.description,
                  status: nc.status,
                  category: nc.category_name
                }))}
                onLocationSelect={(lat, lon) => {
                  setLatitude(lat);
                  setLongitude(lon);
                  setAddress(`Pinned Coordinates: (${lat.toFixed(5)}, ${lon.toFixed(5)})`);
                }}
                interactive={isFormOpen}
              />
            </div>
            
            {isFormOpen && (
              <p className="text-[10px] text-slate-400 mt-2 font-medium flex items-center space-x-1 justify-center">
                <Info className="h-3 w-3" />
                <span>Map is interactive. Click anywhere on the map above to select complaint location coordinates.</span>
              </p>
            )}
          </div>
        </div>
      </main>

      {/* Floating Action Modal: Report Grievance */}
      {isFormOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-xl w-full border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden animate-slide-up">
            <div className="bg-slate-900 dark:bg-slate-950 px-6 py-4 flex items-center justify-between text-white">
              <h3 className="font-bold text-lg">Report New Grievance</h3>
              <button 
                onClick={() => {
                  setIsFormOpen(false);
                  setDuplicateWarning(null);
                }} 
                className="text-slate-400 hover:text-white text-sm cursor-pointer"
              >
                Close
              </button>
            </div>
            
            <div className="p-6 space-y-4 max-h-[500px] overflow-y-auto">
              {/* Description */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Complaint Description <span className="text-red-500">*</span></label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  onBlur={runDuplicateCheck}
                  placeholder="Describe your civic issue (you can mix English, Kannada, and Hinglish. E.g., layout nalli garbage pile agide.)"
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                ></textarea>
              </div>

              {/* Language selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Input Language</label>
                  <select 
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                  >
                    <option value="English">English</option>
                    <option value="Kannada">ಕನ್ನಡ (Kannada)</option>
                    <option value="Hinglish">Hinglish / Kannada-English</option>
                  </select>
                </div>
                {/* Photo Upload */}
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Grievance Photo</label>
                  <div className="relative rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm flex items-center space-x-2">
                    <ImageIcon className="h-4.5 w-4.5 text-slate-400" />
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleFileChange}
                      className="text-xs file:hidden text-slate-500 dark:text-slate-400 w-full cursor-pointer"
                    />
                    {imageFile && <span className="text-[10px] text-emerald-600 font-bold block truncate max-w-[80px]">File Selected</span>}
                  </div>
                </div>
              </div>

              {/* Geotagging coordinates */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-bold text-slate-500 uppercase">Grievance Location Coordinates</label>
                  <button 
                    onClick={handleAutoLocate}
                    className="text-[10px] font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1 cursor-pointer"
                  >
                    <Navigation className="h-3 w-3" />
                    <span>Auto Detect GPS</span>
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-4 text-xs font-semibold">
                  <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-850">
                    <span className="text-[10px] text-slate-400 block font-normal">Latitude</span>
                    {latitude.toFixed(6)}
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-850">
                    <span className="text-[10px] text-slate-400 block font-normal">Longitude</span>
                    {longitude.toFixed(6)}
                  </div>
                </div>
              </div>

              {/* Duplicate check warning */}
              {isDuplicateChecking && (
                <div className="flex items-center space-x-2 text-xs text-blue-600 dark:text-blue-400 animate-pulse bg-blue-50/30 p-3 rounded-xl">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Scanning local grid for duplicate grievances...</span>
                </div>
              )}

              {duplicateWarning && (
                <div className="bg-amber-50 border border-amber-200 dark:bg-amber-950/20 dark:border-amber-900 rounded-xl p-4 space-y-3">
                  <div className="flex items-start space-x-2 text-amber-800 dark:text-amber-300">
                    <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold">Duplicate Grievance Detected Nearby!</h4>
                      <p className="text-[11px] mt-0.5">An issue of the same category has already been reported within 100 meters (Similarity: {(duplicateWarning.similarity_score * 100).toFixed(0)}%).</p>
                    </div>
                  </div>
                  <div className="flex space-x-2 pt-1.5 justify-end">
                    <button 
                      onClick={() => handleSubmitGrievance(duplicateWarning.duplicate_of_id)}
                      className="bg-amber-600 hover:bg-amber-700 text-white rounded-lg px-3 py-1.5 text-[10px] font-bold shadow cursor-pointer transition"
                    >
                      Join Existing Issue #{duplicateWarning.duplicate_of_id}
                    </button>
                    <button 
                      onClick={() => setDuplicateWarning(null)}
                      className="bg-white hover:bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-[10px] font-bold text-slate-600 dark:bg-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 cursor-pointer transition"
                    >
                      Ignore & Create New
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-slate-50 dark:bg-slate-950 px-6 py-4 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-2">
              <button 
                onClick={() => {
                  setIsFormOpen(false);
                  setDuplicateWarning(null);
                }}
                className="bg-white hover:bg-slate-50 border border-slate-200 dark:bg-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 rounded-xl px-4 py-2.5 text-xs font-semibold text-slate-700 dark:text-slate-300 transition cursor-pointer"
              >
                Cancel
              </button>
              <button 
                onClick={() => handleSubmitGrievance()}
                disabled={isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-5 py-2.5 text-xs font-bold shadow transition flex items-center space-x-1.5 cursor-pointer"
              >
                {isSubmitting ? (
                  <Loader2 className="h-4.5 w-4.5 animate-spin" />
                ) : (
                  <>
                    <span>Submit Grievance</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Action Modal: Complaint Detail Detail Overlay */}
      {selectedComplaint && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden animate-slide-up flex flex-col max-h-[600px]">
            <div className="bg-slate-900 dark:bg-slate-950 px-6 py-4 flex items-center justify-between text-white shrink-0">
              <div>
                <h3 className="font-bold text-base">Grievance Detail Trace</h3>
                <span className="text-[10px] text-slate-400">ID: #{selectedComplaint.id}</span>
              </div>
              <button 
                onClick={() => setSelectedComplaint(null)} 
                className="text-slate-400 hover:text-white text-sm cursor-pointer"
              >
                Close
              </button>
            </div>
            
            <div className="p-6 space-y-6 overflow-y-auto flex-1">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Text details column */}
                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 block uppercase">Category</span>
                    <span className="font-bold text-base text-slate-900 dark:text-white">{selectedComplaint.category_name}</span>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 block uppercase">Translated Description</span>
                    <span className="text-xs text-slate-700 dark:text-slate-300 font-medium block bg-slate-50 dark:bg-slate-850 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800/40">
                      "{selectedComplaint.description}"
                    </span>
                  </div>
                  {selectedComplaint.original_description && (
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Original Submitted Text</span>
                      <span className="text-xs text-slate-500 dark:text-slate-400 font-medium block">
                        "{selectedComplaint.original_description}"
                      </span>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-4 text-xs font-semibold">
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Department Routed</span>
                      <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[10px] uppercase font-mono mt-0.5 inline-block">{selectedComplaint.department_name}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Priority Level</span>
                      <span className={`text-[10px] font-bold mt-0.5 inline-block ${
                        selectedComplaint.priority === 'Critical' ? 'text-red-600' :
                        selectedComplaint.priority === 'High' ? 'text-amber-600' :
                        selectedComplaint.priority === 'Medium' ? 'text-blue-600' : 'text-slate-500'
                      }`}>{selectedComplaint.priority}</span>
                    </div>
                  </div>
                </div>

                {/* Media columns */}
                <div className="space-y-4">
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
                      No images attached
                    </div>
                  )}

                  {/* AI Metadata monitor */}
                  {selectedComplaint.ai_prediction && (
                    <div className="bg-blue-50/40 border border-blue-100 dark:bg-blue-950/20 dark:border-blue-900/40 p-3 rounded-lg text-xs space-y-1.5">
                      <h4 className="font-bold text-blue-800 dark:text-blue-300 flex items-center space-x-1 text-[10px] uppercase tracking-wide">
                        <Globe className="h-3.5 w-3.5" />
                        <span>AI Prediction Trace Log</span>
                      </h4>
                      <div className="grid grid-cols-2 text-[10px] text-slate-600 dark:text-slate-400 font-semibold">
                        <span>Classification Confidence:</span>
                        <span className="text-right text-slate-800 dark:text-slate-200">{(selectedComplaint.ai_prediction.category_confidence * 100).toFixed(1)}%</span>
                        <span>Priority Confidence:</span>
                        <span className="text-right text-slate-800 dark:text-slate-200">{(selectedComplaint.ai_prediction.priority_confidence * 100).toFixed(1)}%</span>
                        <span>Translation Pipeline:</span>
                        <span className="text-right text-slate-800 dark:text-slate-200">{selectedComplaint.ai_prediction.translation_time.toFixed(3)}s</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Status Timeline Progress */}
              <div className="border-t border-slate-100 dark:border-slate-800 pt-6">
                <span className="text-[10px] font-bold text-slate-400 block uppercase mb-4">Redressal Timeline Log</span>
                <div className="relative border-l border-slate-200 dark:border-slate-800 ml-2.5 space-y-4">
                  {selectedComplaint.status_history.map((hist: any) => (
                    <div key={hist.id} className="relative pl-6">
                      <span className="absolute -left-1.5 top-1.5 w-3 h-3 bg-blue-500 rounded-full border border-white dark:border-slate-900"></span>
                      <div className="flex items-center space-x-2 text-xs">
                        <span className="font-bold text-slate-900 dark:text-white">{hist.status}</span>
                        <span className="text-[10px] text-slate-400 font-medium">{new Date(hist.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-semibold">{hist.remarks}</p>
                      <span className="text-[9px] text-slate-400 font-medium block mt-0.5">Updated by: {hist.changed_by_name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-slate-50 dark:bg-slate-950 px-6 py-4 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-2 shrink-0">
              <button 
                onClick={() => setSelectedComplaint(null)}
                className="bg-white hover:bg-slate-50 border border-slate-200 dark:bg-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 rounded-xl px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 transition cursor-pointer"
              >
                Close Trace
              </button>
              
              {selectedComplaint.status === 'Resolved' && (
                <button 
                  onClick={() => handleCloseComplaint(selectedComplaint.id)}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl px-5 py-2 text-xs font-bold shadow transition cursor-pointer"
                >
                  Verify & Close Complaint
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
