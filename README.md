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

* **PostgreSQL**: Installed and running on `localhost:5432`.
* **Python**: Version 3.8+ (recommended 3.10+).
* **Node.js**: Node.js (v18+) and `npm`.

---

## 💻 Quick Start Guide

### 1. Backend Setup (FastAPI)

1. Open your PostgreSQL client and create the database:
   ```sql
   CREATE DATABASE civic_karnataka;
   ```
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
