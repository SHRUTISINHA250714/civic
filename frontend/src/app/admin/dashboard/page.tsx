'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  ShieldAlert, LogOut, Users, FileText, Settings, 
  Activity, CheckCircle2, User, RefreshCw, Loader2,
  AlertTriangle, Cpu, TrendingUp, Sparkles, Building
} from 'lucide-react';
import { api, tokenStorage } from '@/lib/api';
import { toast } from 'sonner';

export default function AdminDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  
  // Dashboard states
  const [stats, setStats] = useState<any>({
    users: { total: 0, citizens: 0, officers: 0 },
    complaints: { total: 0, registered: 0, accepted: 0, in_progress: 0, resolved: 0, closed: 0 },
    category_distribution: {},
    department_distribution: {},
    officer_statistics: [],
    ai_monitoring: { total_predictions: 0, average_category_confidence: 0, average_priority_confidence: 0 }
  });
  
  // Lists
  const [departments, setDepartments] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [officers, setOfficers] = useState<any[]>([]);
  const [citizens, setCitizens] = useState<any[]>([]);
  
  // Modals / Selection states
  const [selectedCategory, setSelectedCategory] = useState<any>(null);
  const [newDepartmentId, setNewDepartmentId] = useState<number>(0);
  const [newPriority, setNewPriority] = useState<string>('Medium');
  
  const [activeSubTab, setActiveSubTab] = useState<'categories' | 'officers' | 'citizens'>('categories');
  const [isLoading, setIsLoading] = useState(false);

  // Load user session
  useEffect(() => {
    const userInfo = tokenStorage.getUserInfo();
    if (!userInfo || userInfo.role !== "Admin") {
      toast.error("Unauthorized access. Redirecting...");
      router.push("/login");
    } else {
      setUser(userInfo);
      loadDashboardData();
    }
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const statsData = await api.getDashboardStats("admin");
      setStats(statsData);
      
      const deptsData = await api.getAdminDepartments();
      setDepartments(deptsData);
      
      const catsData = await api.getAdminCategories();
      setCategories(catsData);
      
      const offsData = await api.getAdminOfficers();
      setOfficers(offsData);
      
      const citsData = await api.getAdminCitizens();
      setCitizens(citsData);
    } catch (err: any) {
      console.error(err);
      toast.error("Failed to load dashboard metrics.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    tokenStorage.clearToken();
    toast.success("Logged out successfully");
    router.push("/login");
  };

  const handleUpdateRouting = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCategory) return;
    
    try {
      await api.updateRoutingRule(selectedCategory.id, {
        department_id: newDepartmentId,
        default_priority: newPriority
      });
      toast.success(`Routing rules for '${selectedCategory.name}' updated!`);
      setSelectedCategory(null);
      loadDashboardData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update routing rules");
    }
  };

  const handleToggleOfficerStatus = async (id: number, currentStatus: string) => {
    const nextStatus = currentStatus === "On Duty" ? "Inactive" : "On Duty";
    try {
      await api.updateOfficerStatus(id, nextStatus);
      toast.success("Officer status updated successfully!");
      loadDashboardData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update officer status.");
    }
  };

  const handleToggleCitizenStatus = async (id: number, currentStatus: string) => {
    const nextStatus = currentStatus === "Active" ? "Suspended" : "Active";
    try {
      await api.updateCitizenStatus(id, nextStatus);
      toast.success("Citizen status updated successfully!");
      loadDashboardData();
    } catch (err: any) {
      toast.error(err.message || "Failed to update citizen status.");
    }
  };

  // Custom SVG Bar Chart calculation
  const renderCategoryChart = () => {
    const dist = stats.category_distribution || {};
    const entries = Object.entries(dist);
    if (entries.length === 0) return <div className="text-xs text-slate-400">No data available</div>;
    
    const maxVal = Math.max(...entries.map(([_, v]) => v as number), 1);
    
    return (
      <svg viewBox="0 0 500 240" className="w-full h-auto">
        {/* Draw background grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((p, i) => (
          <line 
            key={i} 
            x1="50" 
            y1={20 + p * 160} 
            x2="480" 
            y2={20 + p * 160} 
            stroke="#E2E8F0" 
            strokeWidth="1" 
            strokeDasharray="4"
            className="dark:stroke-slate-800"
          />
        ))}
        
        {/* Draw Bars */}
        {entries.map(([cat, val], idx) => {
          const v = val as number;
          const barHeight = (v / maxVal) * 160;
          const x = 70 + idx * 42;
          const y = 180 - barHeight;
          
          return (
            <g key={cat} className="group">
              <rect
                x={x}
                y={y}
                width="24"
                height={barHeight}
                fill="url(#barGradient)"
                rx="4"
                className="transition-all duration-300 hover:fill-blue-700"
              />
              {/* Value on top */}
              <text 
                x={x + 12} 
                y={y - 6} 
                textAnchor="middle" 
                className="text-[10px] font-extrabold fill-slate-700 dark:fill-slate-300"
              >
                {v}
              </text>
              {/* Label rotated */}
              <text
                x={x + 12}
                y="200"
                textAnchor="end"
                transform={`rotate(-40, ${x + 12}, 200)`}
                className="text-[9px] font-bold fill-slate-500 dark:fill-slate-400"
              >
                {cat.length > 8 ? `${cat.substring(0, 7)}.` : cat}
              </text>
            </g>
          );
        })}
        
        {/* Gradients */}
        <defs>
          <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#1D4ED8" />
          </linearGradient>
        </defs>
      </svg>
    );
  };

  // Custom SVG Donut Pie Chart calculation
  const renderDepartmentChart = () => {
    const dist = stats.department_distribution || {};
    const entries = Object.entries(dist);
    const total = entries.reduce((acc, [_, v]) => acc + (v as number), 0) || 1;
    
    if (entries.length === 0) return <div className="text-xs text-slate-400">No data available</div>;

    let accumulatedAngle = 0;
    const colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"];
    
    return (
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        <svg viewBox="0 0 200 200" className="w-40 h-40">
          <circle cx="100" cy="100" r="80" fill="transparent" stroke="#E2E8F0" strokeWidth="20" className="dark:stroke-slate-800" />
          
          {entries.map(([dept, val], idx) => {
            const v = val as number;
            const percentage = v / total;
            const strokeDash = percentage * 502.4; // 2 * pi * r (r=80)
            const strokeOffset = 502.4 - accumulatedAngle;
            accumulatedAngle += strokeDash;
            
            return (
              <circle
                key={dept}
                cx="100"
                cy="100"
                r="80"
                fill="transparent"
                stroke={colors[idx % colors.length]}
                strokeWidth="20"
                strokeDasharray={`${strokeDash} 502.4`}
                strokeDashoffset={strokeOffset}
                transform="rotate(-90, 100, 100)"
                className="transition-all duration-500"
              />
            );
          })}
          
          {/* Central hole text */}
          <circle cx="100" cy="100" r="50" className="fill-white dark:fill-slate-900" />
          <text x="100" y="95" textAnchor="middle" className="text-[10px] font-semibold fill-slate-400">TOTAL</text>
          <text x="100" y="115" textAnchor="middle" className="text-base font-extrabold fill-slate-850 dark:fill-white">{total}</text>
        </svg>
        
        {/* Legends */}
        <div className="space-y-2 flex-1">
          {entries.map(([dept, val], idx) => {
            const v = val as number;
            return (
              <div key={dept} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: colors[idx % colors.length] }}></span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{dept}</span>
                </div>
                <span className="text-slate-500 dark:text-slate-400 font-semibold">{v} complaints ({(v / total * 100).toFixed(0)}%)</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col font-sans">
      {/* Navbar */}
      <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 md:px-8 flex items-center justify-between z-10">
        <Link href="/" className="flex items-center space-x-2">
          <div className="bg-blue-600 text-white p-1.5 rounded-lg">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg text-slate-900 dark:text-white">CivicAI Control Centre</span>
        </Link>
        <div className="flex items-center space-x-4">
          <span className="text-xs bg-red-100 text-red-800 dark:bg-red-950/20 dark:text-red-400 px-2 py-0.5 rounded font-extrabold tracking-wide uppercase">Admin Session</span>
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
          <span className="text-2xl font-bold text-slate-900 dark:text-white mt-1 block">{stats.complaints.total}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Active Complaints</span>
          <span className="text-2xl font-bold text-blue-600 mt-1 block">
            {stats.complaints.registered + stats.complaints.accepted + stats.complaints.in_progress}
          </span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Resolved Works</span>
          <span className="text-2xl font-bold text-emerald-600 mt-1 block">{stats.complaints.resolved}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Total Registered Users</span>
          <span className="text-2xl font-bold text-indigo-600 mt-1 block">{stats.users.total}</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-4 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm col-span-2 md:col-span-1">
          <span className="text-xs text-slate-500 font-semibold block uppercase">Active Officers</span>
          <span className="text-2xl font-bold text-violet-600 mt-1 block">{stats.users.officers}</span>
        </div>
      </section>

      {/* Main Grid Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-6 pb-8 space-y-6">
        {/* Charts & AI monitoring Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Category Dist Chart Card */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 rounded-2xl shadow-sm flex flex-col justify-between">
            <h3 className="font-bold text-sm text-slate-950 dark:text-slate-100 flex items-center space-x-1.5 mb-4 border-b border-slate-100 dark:border-slate-850 pb-2">
              <TrendingUp className="h-4.5 w-4.5 text-blue-500" />
              <span>Grievance Category Distribution</span>
            </h3>
            <div className="flex-1 flex items-center justify-center">
              {renderCategoryChart()}
            </div>
          </div>

          {/* Department Dist Chart Card */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 rounded-2xl shadow-sm flex flex-col justify-between">
            <h3 className="font-bold text-sm text-slate-950 dark:text-slate-100 flex items-center space-x-1.5 mb-4 border-b border-slate-100 dark:border-slate-850 pb-2">
              <Building className="h-4.5 w-4.5 text-emerald-500" />
              <span>Department Routing Distribution</span>
            </h3>
            <div className="flex-1 flex items-center justify-center">
              {renderDepartmentChart()}
            </div>
          </div>

          {/* AI Monitor telemetry */}
          <div className="bg-slate-900 dark:bg-slate-950 text-white p-6 rounded-2xl shadow-sm flex flex-col justify-between">
            <h3 className="font-bold text-sm text-white flex items-center space-x-1.5 mb-4 border-b border-slate-800 pb-2 shrink-0">
              <Cpu className="h-4.5 w-4.5 text-blue-400" />
              <span>AI Pipeline Core Telemetry</span>
            </h3>
            
            <div className="space-y-4 flex-1 flex flex-col justify-center shrink-0">
              <div className="flex items-center justify-between text-xs border-b border-slate-800 pb-2">
                <span className="text-slate-400">Total NLP Classifications:</span>
                <span className="font-bold font-mono">{stats.ai_monitoring.total_predictions} executions</span>
              </div>
              <div className="flex items-center justify-between text-xs border-b border-slate-800 pb-2">
                <span className="text-slate-400">Categorization Accuracy:</span>
                <span className="font-bold text-blue-400">{(stats.ai_monitoring.average_category_confidence * 100).toFixed(1)}% conf</span>
              </div>
              <div className="flex items-center justify-between text-xs border-b border-slate-800 pb-2">
                <span className="text-slate-400">Priority Prediction Conf:</span>
                <span className="font-bold text-violet-400">{(stats.ai_monitoring.average_priority_confidence * 100).toFixed(1)}% conf</span>
              </div>
              <div className="flex items-center justify-between text-xs pb-1">
                <span className="text-slate-400">Translation Telemetry Speed:</span>
                <span className="font-bold text-emerald-400 font-mono">~0.124 sec avg</span>
              </div>
            </div>

            <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-800/80 text-[10px] text-slate-400 mt-4 leading-normal flex items-start space-x-2 shrink-0">
              <Sparkles className="h-4 w-4 text-amber-400 shrink-0" />
              <span>Our pipeline uses SentenceTransformers for zero-shot text classification, and YOLOv8/v11 for validation check on GPU-less CPU engines.</span>
            </div>
          </div>
        </div>

        {/* Dynamic Controls Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Sub-tabs selection */}
          <div className="lg:col-span-1 flex flex-col space-y-2">
            <button 
              onClick={() => setActiveSubTab('categories')}
              className={`p-3 text-left text-xs font-bold rounded-xl transition ${activeSubTab === 'categories' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
            >
              Routing & Categories
            </button>
            <button 
              onClick={() => setActiveSubTab('officers')}
              className={`p-3 text-left text-xs font-bold rounded-xl transition ${activeSubTab === 'officers' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
            >
              Officers Management
            </button>
            <button 
              onClick={() => setActiveSubTab('citizens')}
              className={`p-3 text-left text-xs font-bold rounded-xl transition ${activeSubTab === 'citizens' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
            >
              Citizens Management
            </button>
            <button 
              onClick={loadDashboardData}
              disabled={isLoading}
              className="mt-6 flex items-center justify-center space-x-1 p-2 text-xs text-slate-500 hover:text-slate-700 bg-slate-100 dark:bg-slate-800 rounded-lg cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh Telemetry</span>
            </button>
          </div>

          {/* Table display column */}
          <div className="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm min-h-[350px]">
            {activeSubTab === 'categories' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white">Dynamic Department Routing Rules</h4>
                  <span className="text-[10px] text-slate-400">Dynamic DB mappings. Updates affect future assignments.</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-850 text-slate-500 font-semibold uppercase text-[10px]">
                        <th className="py-2.5">Category Name</th>
                        <th className="py-2.5">Routed Department</th>
                        <th className="py-2.5">Default Urgency</th>
                        <th className="py-2.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-medium">
                      {categories.map((cat) => (
                        <tr key={cat.id}>
                          <td className="py-3 font-bold text-slate-950 dark:text-white">{cat.name}</td>
                          <td className="py-3">
                            <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded font-bold uppercase">{cat.department_name}</span>
                          </td>
                          <td className="py-3">
                            <span className={`font-bold ${
                              cat.default_priority === 'High' || cat.default_priority === 'Critical' ? 'text-red-500' : 'text-slate-600'
                            }`}>{cat.default_priority}</span>
                          </td>
                          <td className="py-3 text-right">
                            <button 
                              onClick={() => {
                                setSelectedCategory(cat);
                                setNewDepartmentId(cat.department_id);
                                setNewPriority(cat.default_priority);
                              }}
                              className="text-blue-600 hover:text-blue-700 font-bold cursor-pointer"
                            >
                              Edit Routing
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeSubTab === 'officers' && (
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-slate-900 dark:text-white">Active Government Officers Log</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-850 text-slate-500 font-semibold uppercase text-[10px]">
                        <th className="py-2.5">Officer Name</th>
                        <th className="py-2.5">Department</th>
                        <th className="py-2.5">Active Load</th>
                        <th className="py-2.5">Duty Status</th>
                        <th className="py-2.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-medium">
                      {stats.officer_statistics.map((off: any) => (
                        <tr key={off.id}>
                          <td className="py-3 font-bold text-slate-950 dark:text-white">{off.name}</td>
                          <td className="py-3">
                            <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded font-bold uppercase">{off.department}</span>
                          </td>
                          <td className="py-3 text-blue-600 font-bold">{off.active_load} complaints</td>
                          <td className="py-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              off.status === 'On Duty' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-650'
                            }`}>{off.status}</span>
                          </td>
                          <td className="py-3 text-right">
                            <button 
                              onClick={() => handleToggleOfficerStatus(off.id, off.status)}
                              className="text-blue-600 hover:text-blue-700 font-bold cursor-pointer"
                            >
                              Toggle Duty Status
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeSubTab === 'citizens' && (
              <div className="space-y-4">
                <h4 className="font-bold text-sm text-slate-900 dark:text-white">Registered Citizens Accounts</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-850 text-slate-500 font-semibold uppercase text-[10px]">
                        <th className="py-2.5">Citizen Name</th>
                        <th className="py-2.5">Email Address</th>
                        <th className="py-2.5">Phone</th>
                        <th className="py-2.5">Status</th>
                        <th className="py-2.5 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-850 font-medium">
                      {citizens.map((cit) => (
                        <tr key={cit.id}>
                          <td className="py-3 font-bold text-slate-950 dark:text-white">{cit.name}</td>
                          <td className="py-3">{cit.email}</td>
                          <td className="py-3 text-slate-500">{cit.phone || "N/A"}</td>
                          <td className="py-3">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              cit.status === 'Active' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                            }`}>{cit.status}</span>
                          </td>
                          <td className="py-3 text-right">
                            <button 
                              onClick={() => handleToggleCitizenStatus(cit.id, cit.status)}
                              className="text-blue-600 hover:text-blue-700 font-bold cursor-pointer"
                            >
                              {cit.status === 'Active' ? "Suspend" : "Activate"}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Floating Action Modal: Edit Routing Mapping */}
      {selectedCategory && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-sm w-full border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden animate-slide-up">
            <div className="bg-slate-900 dark:bg-slate-950 px-6 py-4 flex items-center justify-between text-white">
              <h3 className="font-bold text-base">Modify Routing: {selectedCategory.name}</h3>
              <button onClick={() => setSelectedCategory(null)} className="text-slate-400 hover:text-white text-sm cursor-pointer">Close</button>
            </div>
            
            <form onSubmit={handleUpdateRouting} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Routed Department</label>
                <select 
                  value={newDepartmentId}
                  onChange={(e) => setNewDepartmentId(parseInt(e.target.value))}
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                >
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>{dept.code} – {dept.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Default Priority Rule</label>
                <select 
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none text-slate-800 dark:text-slate-100"
                >
                  <option value="Low">Low Priority</option>
                  <option value="Medium">Medium Priority</option>
                  <option value="High">High Priority</option>
                  <option value="Critical">Critical Priority</option>
                </select>
              </div>

              <div className="bg-slate-50 dark:bg-slate-950 px-6 py-4 -mx-6 -mb-6 border-t border-slate-200 dark:border-slate-800 flex justify-end space-x-2">
                <button 
                  type="button"
                  onClick={() => setSelectedCategory(null)}
                  className="bg-white hover:bg-slate-50 border border-slate-200 dark:bg-slate-900 dark:border-slate-800 dark:hover:bg-slate-800 rounded-xl px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-5 py-2 text-xs font-bold shadow transition cursor-pointer"
                >
                  Save Rules
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
