const API_BASE = "http://127.0.0.1:8000/api/v1";

// Token storage helpers
export const tokenStorage = {
  setToken: (token: string) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("civic_token", token);
    }
  },
  getToken: () => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("civic_token");
    }
    return null;
  },
  clearToken: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("civic_token");
      localStorage.removeItem("civic_user");
    }
  },
  setUserInfo: (user: any) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("civic_user", JSON.stringify(user));
    }
  },
  getUserInfo: () => {
    if (typeof window !== "undefined") {
      const user = localStorage.getItem("civic_user");
      return user ? JSON.parse(user) : null;
    }
    return null;
  }
};

// Generic fetch wrapper with auth header
async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const token = tokenStorage.getToken();
  
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  const config = {
    ...options,
    headers
  };
  
  const response = await fetch(`${API_BASE}${endpoint}`, config);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Something went wrong");
  }
  
  return response.json();
}

export const api = {
  // Auth APIs
  register: async (data: any) => {
    return apiFetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  },
  
  login: async (form: FormData) => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      body: form // URL encoded / form data for OAuth2 request
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Authentication failed");
    }
    
    const data = await response.json();
    tokenStorage.setToken(data.access_token);
    tokenStorage.setUserInfo({
      id: data.user_id,
      name: data.name,
      email: data.email,
      role: data.role
    });
    return data;
  },
  
  getMe: async () => {
    return apiFetch("/auth/me");
  },
  
  updateProfile: async (data: any) => {
    return apiFetch("/auth/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  },

  // Complaints APIs
  checkDuplicate: async (formData: FormData) => {
    return apiFetch("/complaints/check-duplicate", {
      method: "POST",
      body: formData
    });
  },
  
  raiseComplaint: async (formData: FormData) => {
    return apiFetch("/complaints", {
      method: "POST",
      body: formData
    });
  },
  
  getComplaints: async (params?: { status?: string; category_id?: number; priority?: string }) => {
    let url = "/complaints";
    const query = [];
    if (params?.status) query.push(`status_filter=${params.status}`);
    if (params?.category_id) query.push(`category_id=${params.category_id}`);
    if (params?.priority) query.push(`priority=${params.priority}`);
    if (query.length > 0) url += `?${query.join("&")}`;
    return apiFetch(url);
  },
  
  getNearbyComplaints: async (lat: number, lon: number, radius = 1000) => {
    return apiFetch(`/complaints/nearby?latitude=${lat}&longitude=${lon}&radius_meters=${radius}`);
  },
  
  getComplaintById: async (id: number) => {
    return apiFetch(`/complaints/${id}`);
  },
  
  updateComplaintStatus: async (id: number, status: string, remarks?: string) => {
    return apiFetch(`/complaints/${id}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, remarks })
    });
  },
  
  resolveComplaint: async (id: number, formData: FormData) => {
    return apiFetch(`/complaints/${id}/resolve`, {
      method: "POST",
      body: formData
    });
  },

  /** Citizen verifies or rejects an officer's resolution */
  verifyResolution: async (id: number, data: {
    approve: boolean;
    feedback_rating?: number;
    feedback_remarks?: string;
  }) => {
    return apiFetch(`/complaints/${id}/verify-resolution`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  },

  /** Get the multimodal evidence trust breakdown for a complaint */
  getComplaintEvidence: async (id: number) => {
    return apiFetch(`/complaints/${id}/evidence`);
  },

  // Dashboard stats
  getDashboardStats: async (role: "citizen" | "officer" | "admin") => {
    return apiFetch(`/dashboard/${role}`);
  },

  /** Admin: manually trigger SLA status update across all active complaints */
  runSlaCheck: async () => {
    return apiFetch("/dashboard/admin/run-sla-check", { method: "POST" });
  },

  // Admin APIs
  getAdminDepartments: async () => {
    return apiFetch("/admin-control/departments");
  },
  
  getAdminCategories: async () => {
    return apiFetch("/admin-control/categories");
  },
  
  updateRoutingRule: async (id: number, data: { department_id: number; default_priority?: string }) => {
    return apiFetch(`/admin-control/categories/${id}/routing`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  },
  
  getAdminOfficers: async () => {
    return apiFetch("/admin-control/officers");
  },
  
  getAdminCitizens: async () => {
    return apiFetch("/admin-control/citizens");
  },
  
  updateOfficerStatus: async (id: number, status: string) => {
    return apiFetch(`/admin-control/officers/${id}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
  },
  
  updateCitizenStatus: async (id: number, status: string) => {
    return apiFetch(`/admin-control/citizens/${id}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
  },

  // Notifications APIs
  getNotifications: async () => {
    return apiFetch("/notifications");
  },
  
  markNotificationRead: async (id: number) => {
    return apiFetch(`/notifications/${id}/read`, { method: "PUT" });
  },
  
  markAllNotificationsRead: async () => {
    return apiFetch("/notifications/read-all", { method: "PUT" });
  },

  // Predictive Analytics APIs (Phase 16)
  getPredictiveOverview: async () => {
    return apiFetch("/predictive/overview");
  },

  estimateResolutionRisk: async (data: {
    category: string;
    ward?: string;
    priority?: string;
    department?: string;
  }) => {
    return apiFetch("/predictive/estimate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
  },

  getHotspotForecasts: async () => {
    return apiFetch("/predictive/hotspots");
  },

  getTimeSeriesForecast: async (days: number = 14) => {
    return apiFetch(`/predictive/forecast?days=${days}`);
  },

  trainPredictiveModels: async (maxSamples: number = 100000) => {
    return apiFetch(`/predictive/train?max_samples=${maxSamples}`, {
      method: "POST"
    });
  }
};
export default api;
