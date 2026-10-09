# CivicAI Karnataka – Frontend Portal

The web frontend for the **CivicAI Karnataka Smart Civic Grievance Redressal System**, built with [Next.js 16](https://nextjs.org) (App Router), React 19, Tailwind CSS, and Leaflet GIS mapping.

---

## 🚀 Key Portal Features

* **Citizen Portal (`/citizen/dashboard`)**:
  - Multilingual reporting (Kannada, English, Hinglish, Voice Audio Note).
  - Geolocation pin placement and live GPS coordinate capture.
  - Mandatory photographic evidence upload with client-side format/dimension validation.
  - Multi-factor duplicate prevention and display of *"Reported by X people"*.
  - Citizen resolution proof inspection and 1-click closure (1–5 star rating) or reopen feedback loop.
  - Evidence trust badge display (`VERIFIED`, `PARTIALLY_VERIFIED`, `MANUAL_REVIEW`, `SUSPICIOUS`, `REJECTED`).
* **Officer Portal (`/officer/dashboard`)**:
  - Dual bilingual grievance cards: *"Original Complaint"* (native script + audio player) and *"English Translation"*.
  - Separated media inspection: *"Citizen Evidence (Original)"* vs *"Officer Repair Verification (Completed)"*.
  - Mandatory post-fix photographic proof and descriptive remediation logs verified by `verify_resolution_evidence`.
  - Dynamic SLA timer countdowns, duration badges, and breach warnings.
* **Administrator Portal (`/admin/dashboard`)**:
  - City-wide GIS heatmaps and spatial ward cluster analysis.
  - Phase 16 ML early warning analytics (SLA breach probability and 14-day grievance forecasts).
  - Cross-department performance metrics across BBMP, BESCOM, BWSSB, and BSWML.

---

## 🛠️ Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to access the portal.

### 3. Production Build
```bash
npm run build
npm start
```

---

## 🔗 Backend API Connection
The frontend connects to the FastAPI backend running at `http://127.0.0.1:8000`. Ensure the backend server is running:
```powershell
uvicorn backend.app.main:app --reload
```
Interactive API docs are available at `http://127.0.0.1:8000/docs`.
