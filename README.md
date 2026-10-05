# CivicAI Karnataka – Smart Civic Grievance Redressal System

An AI-powered multimodal civic grievance management platform built specifically for the State of Karnataka (Bengaluru). The system enables citizens to report complaints via text, native scripts (Kannada / Hinglish / English), voice, and geotagged imagery. It uses computer vision (Ultralytics YOLOv8), OpenCV quality diagnostics, multimodal hard-gate evidence verification, NLP multilingual embeddings, geospatial duplicate detection, and dynamic routing to assign tickets to the correct state civic authority and track resolution through SLA enforcement.

---

## 🏛️ Connected Civic Authorities (4 Departments)

The platform is wired to four core municipal and utility agencies:

| Authority | Code | Domain & Scope |
|---|---|---|
| **Bruhat Bengaluru Mahanagara Palike** | `BBMP` | Roads, potholes, pavements, streetlighting, stormwater drains |
| **Bangalore Electricity Supply Company** | `BESCOM` | Power outages, dangerous exposed wiring, sparking transformers |
| **Bangalore Water Supply and Sewerage Board** | `BWSSB` | Broken water mains, water leakage, sewage overflow, contaminated supply |
| **Bengaluru Solid Waste Management Limited** | `BSWML` | Garbage blackspots, overflowing bins, uncollected waste, illegal waste burning |

---

## 🚀 Key System Features

* **Multilingual NLP Pipeline & Kanglish Boundary Precision**: Automatic detection of Kannada, Kanglish, Hinglish, and English with automated English translation and zero-shot grievance classification. Uses strict word boundaries to preserve genuine English containing Indian location names (e.g. "MG Road", "Indiranagar", "Koramangala") without false transliteration.
* **Deterministic Department Routing**: Rule-based precedence routing grievances accurately to the responsible Karnataka authority (potholes and road damage to BBMP `Potholes & Damaged Roads`, garbage and litter to BSWML, water and sewage to BWSSB, high-voltage power to BESCOM).
* **YOLOv8 & OpenCV Vision Analysis**: Real-time object detection and OpenCV quality diagnostics (evaluating blurriness via Laplacian variance, exposure levels, and resolution).
* **4-Gate Evidence Verification Engine**: Multi-gate validation preventing fraudulent submissions:
  1. *Geo*: Live device GPS cross-referenced against EXIF GPS coordinates ($\le 500\text{m}$ match, $\ge 5000\text{m}$ severe mismatch) with device accuracy radius.
  2. *Timestamp Freshness*: Rejects future timestamps ($> 10\text{m}$) and flags stale photos ($> 72\text{h}$).
  3. *Semantic Agreement*: SentenceTransformers cosine matching ensuring photo matches reported category. Cross-category mismatches (e.g. pothole complaint with garbage photo) strictly locked to `REJECTED`.
  4. *Duplicate Image Detection*: 64-bit difference perceptual hashing (`dHash`) with Hamming distance $\le 4$ detecting recycled photos across complaints.
  * *Standardized Verification Badges*: Displays user-facing badges (*"Image matches complaint"* vs *"Image does not match complaint"*).
* **Multimodal Duplicate Detection Guard**: 100m radius duplicate scan with cosine text similarity. Evaluates visual evidence *before* duplicate clustering, rejecting complaints with mismatched images (`MISMATCH`) from linking to active tickets.
* **Dynamic SLA Enforcement & Duration Tracking**: Priority-driven timers (Low: 72h, Medium: 48h, High: 24h, Critical: 12h) displaying explicit duration strings, live remaining time countdowns, dynamic red breach warning pills, and resolution compliance (*"Met SLA"* vs *"Breached SLA"*).
* **Bilingual Officer Operations**: Field officers view dual clearly-labeled sections: *"Original Complaint"* (verbatim citizen text + native audio player) and *"English Translation"* (normalized operational triage), with separate inspection of *"Citizen Evidence (Original)"* vs *"Officer Repair Verification (Completed)"*.
* **Citizen Proof Verification & Instant UI Sync**: Citizens inspect officer resolution proof photos to approve closure (with 1–5 star ratings) or trigger automated re-dispatch, with immediate local state synchronization hiding the verification prompt once completed.
* **High-Performance Citizen Dashboard**: Decoupled complaint loading from nearby geo-queries combined with backend SQLAlchemy eager loading (`joinedload` / `selectinload`), eliminating N+1 queries.
* **Security & Session Persistence**: Interactive password visibility toggles (`Eye`/`EyeOff`) and dual-storage fallback (`tokenStorage.ensureSession`) preventing logout drops on page refreshes.
* **Phase 16 Predictive Analytics**: Random Forest machine learning models trained on historical Janahita datasets for 14-day grievance intake forecasting and SLA breach risk scoring.

---

## 🔄 Recent Updates & Changelog

### October 2026 — 11 Platform Fixes & Operational Enhancements
1. **Password Visibility Toggle**: Interactive `Eye` / `EyeOff` icons on password and confirm-password fields in `/login` and `/register`.
2. **Citizen Dashboard Performance Optimization**: Decoupled primary complaint fetching from secondary nearby geolocation scans, powered by SQLAlchemy eager loading (`joinedload` on category, department, officer, user and `selectinload` on images).
3. **Deterministic Department Routing**: Rule-based priority guard mapping potholes & road damage (including MG Road complaints) strictly to BBMP `Potholes & Damaged Roads`, and garbage/waste strictly to BSWML.
4. **Kanglish vs. Genuine English Detection Fix**: Token word-boundary matching (`\b[a-zA-Z]+\b`) preserving genuine English text with Indian location entities as `en` without false Indic transliteration.
5. **Dual-Storage Session Persistence on Refresh**: Integrated `tokenStorage.ensureSession(expectedRole)` with `localStorage` + `sessionStorage` fallback, preventing premature logouts on browser refresh.
6. **Comprehensive SLA Duration, Remaining Time & Resolution Status**: Computed `sla_duration_str` (e.g. "12h (Critical)"), live `time_remaining_str`, resolution status (*"Met SLA"* vs *"Breached SLA"*), and dynamic breach warning badges.
7. **Multimodal Duplicate Detection Guard**: Evaluates image evidence *before* duplicate clustering, rejecting complaints with mismatched images (`image_semantic_status == "MISMATCH"`) from linking to existing tickets.
8. **Officer Dashboard Dual Translation Display**: Replaced single text display with dual, clearly-labeled cards for *"Original Complaint"* and *"English Translation"*.
9. **Standardized Image-Complaint Verification Badges**: Exposed `image_verification_result` (*"Image matches complaint"* vs *"Image does not match complaint"*) across complaint cards and audit panels.
10. **Officer Repair Verification Image Separation**: Distinct categorization and UI display of *"Citizen Evidence (Original)"* vs *"Officer Repair Verification (Completed)"*.
11. **Citizen Resolution Verification UI Synchronization**: Instant local state update upon submitting resolution approval/rejection, hiding the "Verify Resolution" action button once completed.

### Infrastructure & Architectural Baseline
* **Database Migration to Neon (Cloud PostgreSQL)**: Serverless cloud PostgreSQL with SSL enforcement (`sslmode=require`), connection pooling (`pool_pre_ping`, `pool_recycle`), and 3-attempt startup retry backoff.
* **Translated-Text Embedding for Spatial Duplicate Detection**: Generated SentenceTransformer embeddings strictly on translated English text across Kannada, Kanglish, Hinglish, and English submissions.
* **Longest-First Multi-Word Kannada Phrase Matching**: Offline local dictionary evaluates multi-word phrases first before token lookup.
* **1:1 Taxonomy & Database Category Parity**: Synchronized all 47 standardized categories between database seeder and AI taxonomy.
* **Compulsory Photographic Evidence & Address Context**: Mandatory image upload enforcement at frontend validation and backend API entry, paired with typed street address / landmark input.

---

## 🔑 Default Test Accounts & Credentials

All default test accounts are seeded via `python -m backend.app.seed`:

| Role | Name | Email | Password | Primary Dashboard |
|---|---|---|---|---|
| 👑 **System Administrator** | Karnataka Admin | `admin@civicai.gov.in` | `adminpassword` | [`/admin/dashboard`](http://localhost:3000/admin/dashboard) |
| 👤 **Citizen User** | Rahul Sharma | `citizen@gmail.com` | `citizenpassword` | [`/citizen/dashboard`](http://localhost:3000/citizen/dashboard) |
| 🚧 **BBMP Officer** | Rajesh Kumar | `officer.bbmp@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| ⚡ **BESCOM Officer** | Manjunath Swamy | `officer.bescom@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| 🚰 **BWSSB Officer** | Anil Gowda | `officer.bwssb@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| 🗑️ **BSWML Officer** | Sunitha Murthy | `officer.bswml@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |

---

## 🛠️ Prerequisites

* **PostgreSQL**: Neon serverless cloud PostgreSQL database (recommended) or local PostgreSQL instance (v12+) running on `localhost:5432`.
* **Python**: Version 3.8+ (recommended 3.10+).
* **Node.js**: Node.js (v18+) and `npm`.

---

## 💻 Quick Start Guide

### 1. Backend Setup (FastAPI)

1. Configure your database connection string in `.env` (pointing to Neon serverless cloud PostgreSQL or local Postgres):
   ```env
   DATABASE_URL=postgresql://<user>:<password>@<neon-hostname>/civic_karnataka?sslmode=require
   ```
   *(Note: If using local PostgreSQL as developer fallback: `postgresql://user:password@localhost:5432/civic_karnataka` after running `CREATE DATABASE civic_karnataka;`)*
2. Open a terminal in the root project folder:
   ```powershell
   # Create and activate virtual environment (Windows PowerShell)
   python -m venv venv
   .\venv\Scripts\activate

   # Install dependencies
   pip install -r backend/requirements.txt

   # Seed database with the 4 Karnataka departments, wards, and officers
   python -m backend.app.seed

   # Start FastAPI dev server
   uvicorn backend.app.main:app --reload
   ```
3. Backend API runs at **`http://127.0.0.1:8000`**.
4. Interactive Swagger API Docs: **`http://127.0.0.1:8000/docs`**.

### 2. Frontend Setup (Next.js 16 + Turbopack)

1. Open a second terminal and navigate to `frontend`:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
2. Frontend portal runs at **`http://localhost:3000`**.

---

## 🧪 Testing & Verification

* **Interactive Manual Testing Guide**: Full 8-track walkthrough in [TESTING_GUIDE.md](file:///c:/Users/Lenovo/Desktop/CIVIC/TESTING_GUIDE.md).
* **Complete System Documentation & Architecture**: [PROJECT_DOCUMENTATION.md](file:///c:/Users/Lenovo/Desktop/CIVIC/PROJECT_DOCUMENTATION.md).
* **17-Phase Implementation Blueprint**: [phases.md](file:///c:/Users/Lenovo/Desktop/CIVIC/phases.md).
* **11-Fix Comprehensive Verification Suite**:
  ```powershell
  python backend/test_civic_fixes_verification.py
  ```
* **Automated Evidence Hard Gates Test Suite (11 Scenarios)**:
  ```powershell
  python -m backend.test_evidence_gates
  ```
* **Automated End-to-End Test Suite (Phase 1–17)**:
  ```powershell
  python backend/test_e2e.py
  ```
* **Multilingual & Kanglish Duplicate Detection Tests**:
  ```powershell
  python backend/test_kanglish_duplicate.py
  python backend/test_multilingual_duplicate.py
  ```
* **Phase 10 Duplicate Prevention & Impact Tracking Suite**:
  ```powershell
  python backend/test_phase10_duplicate_ux.py
  ```
* **Frontend Production Build Verification**:
  ```powershell
  cd frontend
  npm run build
  ```