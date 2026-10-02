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

* **Multilingual NLP Pipeline**: Automatic detection of Kannada, Kanglish, Hinglish, and English with automated English translation and zero-shot grievance classification.
* **YOLOv8 & OpenCV Vision Analysis**: Real-time object detection and OpenCV quality diagnostics (evaluating blurriness via Laplacian variance, exposure levels, and resolution).
* **4-Gate Evidence Verification Engine**: Multi-gate validation preventing fraudulent submissions:
  1. *Geo*: Live device GPS cross-referenced against EXIF GPS coordinates ($\le 500\text{m}$ match, $\ge 5000\text{m}$ severe mismatch) with device accuracy radius.
  2. *Timestamp Freshness*: Rejects future timestamps ($> 10\text{m}$) and flags stale photos ($> 72\text{h}$).
  3. *Semantic Agreement*: SentenceTransformers cosine matching ensuring photo matches reported category. Cross-category mismatches (e.g. pothole complaint with garbage photo) strictly locked to `REJECTED`.
  4. *Duplicate Image Detection*: 64-bit difference perceptual hashing (`dHash`) with Hamming distance $\le 4$ detecting recycled photos across complaints.
  * *Decisions*: `VERIFIED`, `PARTIALLY_VERIFIED`, `MANUAL_REVIEW`, `SUSPICIOUS`, `REJECTED`.
* **Geospatial Duplicate Detection**: 100m radius duplicate scan with cosine text similarity to group duplicate complaints and prevent ticket flooding.
* **Dynamic SLA Enforcement**: Priority-driven timers (Low: 72h, Medium: 48h, High: 24h, Critical: 12h) with auto-escalation upon breach.
* **Citizen Proof Verification**: Citizens inspect officer resolution proof photos to approve closure (with 1–5 star ratings) or trigger automated re-dispatch.
* **Phase 16 Predictive Analytics**: Random Forest machine learning models trained on historical Janahita datasets for 14-day grievance intake forecasting and SLA breach risk scoring.

---

## 🔄 Recent Updates & Changelog
*(As of September 2026 — Infrastructure & AI Pipeline Enhancements)*

### 1. Database Migration to Neon (Cloud PostgreSQL)
- Migrated from local PostgreSQL to Neon serverless cloud PostgreSQL via `DATABASE_URL` environment configuration.
- Implemented SSL enforcement (`sslmode=require`), production connection pooling (`pool_pre_ping`, `pool_size`, `max_overflow`, `pool_recycle`), and 3-attempt startup retry logic to gracefully handle Neon free-tier cold starts.
- Updated project execution instructions to use Neon cloud database connections as default/recommended, retaining local PostgreSQL as a developer fallback option.

### 2. Duplicate Detection Fix — Translated Text Embedding
- Fixed a bug in `backend/app/services/duplicate.py` where duplicate detection was generating embeddings from raw, untranslated complaint text instead of translated English text.
- Duplicate detection now reliably computes embeddings on translated English descriptions across all complaints regardless of submission language or script, with fallback handling for missing translations.

### 3. Language Detection Fix — Kanglish/Hinglish Translation Bypass
- Fixed an issue in `backend/app/services/ai.py` where `langdetect` misclassified Romanized Kanglish/Hinglish text (Kannada/Hindi written in Latin script) as English, silently skipping translation.
- Enforced translation unless text is verified high-confidence English (`langdetect` confidence > 0.95) with zero Indic/Kanglish/Hinglish marker words or Kannada script, ensuring all mixed-language complaints are translated before classification and duplicate checking.

### 4. Translation Fix — Multi-Word Kannada Phrase Matching
- Resolved a bug in the Tier 2 local dictionary translation fallback (used when online translation is unavailable or rate-limited) where multi-word Kannada dictionary entries (e.g., "ಬೀದಿ ದೀಪ" / streetlight) failed to match due to single-word tokenization.
- The fallback normalizer now matches multi-word phrases against full text first (longest phrases first) before single-word lookup, preventing misclassifications during fallback operation.

### 5. Officer Dashboard — Translated-Only Text Display
- Fixed an issue where the Officer Dashboard and officer-facing API endpoints exposed raw, untranslated Kannada, Hinglish, or Kanglish text to field officers.
- Officers now view strictly translated English descriptions across all complaint queues (with fallback indicators for missing translations), while citizens continue to see their original submitted text.

### 6. Category Routing Data Consistency Fix
- Resolved data drift between hardcoded category definitions in `backend/app/services/ai.py` (`CATEGORY_HIERARCHY`) and the database-seeded `complaint_categories` table.
- Added missing `"Lakes & Water Bodies"` (BBMP, High priority) and updated `"Distribution Feeder & Cable Fault"` to `"Streetlight Power Supply Fault"` (BESCOM, Medium priority) in-place to preserve foreign key references, confirming 1:1 parity (47 categories) across code and database.

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
* **Automated Evidence Hard Gates Test Suite (11 Scenarios)**:
  ```powershell
  python -m backend.test_evidence_gates
  ```
* **Automated End-to-End Test Suite (Phase 1–17)**:
  ```powershell
  python backend/test_e2e.py
  ```


Ensure your `DATABASE_URL` environment variable is set in `.env` (Neon cloud PostgreSQL or local `localhost:5432`).

1️⃣ Terminal 1: Backend API (FastAPI)
# 1. Navigate to the root directory
cd /Users/raksh/Ishu/civic

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Seed the database with default departments, wards, and test users (Run this first time)
python -m backend.app.seed

# 4. Start the FastAPI development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload




2️⃣ Terminal 2: Frontend Web Portal (Next.js)
# 1. Navigate to the frontend directory
cd /Users/raksh/Ishu/civic/frontend

# 2. Install dependencies (only needed once or after updating packages)
npm install

# 3. Start the Next.js development server
npm run dev




Running Automated Test Suites
cd /Users/raksh/Ishu/civic
source venv/bin/activate

# Run full 17-Phase End-to-End Workflow Verification Suite
python backend/test_e2e.py

# Run Phase 10 Duplicate Prevention & Impact Tracking Suite
python backend/test_phase10_duplicate_ux.py