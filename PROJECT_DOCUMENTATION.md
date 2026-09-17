# 🏛️ Karnataka AI-Powered Civic Grievance Intelligence Platform
### *Comprehensive System Architecture, Technical Specification & Phase-by-Phase Reference Guide*

---

## 📑 Table of Contents
1. [Executive Overview & Objectives](#1-executive-overview--objectives)
2. [End-to-End System Architecture & Information Flow](#2-end-to-end-system-architecture--information-flow)
3. [Complete Technology Stack](#3-complete-technology-stack)
4. [Comprehensive 17-Phase Implementation Deep Dive](#4-comprehensive-17-phase-implementation-deep-dive)
5. [Database Architecture & Data Models](#5-database-architecture--data-models)
6. [Multimodal AI & Machine Learning Intelligence Layer](#6-multimodal-ai--machine-learning-intelligence-layer)
7. [Karnataka Smart Agency Routing & Operational Hierarchy](#7-karnataka-smart-agency-routing--operational-hierarchy)
8. [Complaint Lifecycle State Machine & SLA Escalation](#8-complaint-lifecycle-state-machine--sla-escalation)
9. [API Reference & Endpoint Catalog](#9-api-reference--endpoint-catalog)
10. [Setup, Deployment & Testing Guide](#10-setup-deployment--testing-guide)

---

## 1. Executive Overview & Objectives

The **Karnataka AI-Powered Civic Grievance Platform** is a unified, state-wide municipal intelligence ecosystem built for Karnataka (specifically tailored for Bengaluru’s municipal architecture). 

The platform empowers citizens to report civic grievances using **multilingual natural language (Kannada, English, Hinglish)**, **voice audio recording**, **photographic evidence**, and **live GPS coordinates**. It applies cutting-edge Artificial Intelligence (NLP classification, Computer Vision, Geospatial proximity clustering, and Machine Learning predictive analytics) to transform raw citizen reports into verified, categorized, priority-scored, and smartly-routed work orders.

### 🎯 Key Goals & Innovations
* **Multimodal Citizen Intake**: Text in Kannada/English/Hinglish, voice-to-text recording, live device geolocation, and photo capture.
* **Zero-Drop Translation & Preprocessing**: Automatically normalizes Kannada/Hinglish input to standard English for NLP classification while preserving the citizen's original statement and audio recordings.
* **Explainable Multimodal Evidence Trust Scoring (0–100%)**: Cross-evaluates live device GPS against EXIF photo metadata, checks upload timestamp plausibility, and validates whether YOLOv8 computer vision detected objects match the reported category.
* **Spatial & Semantic Duplicate Detection**: Prevents ticket flooding by merging new complaints within a 100m radius and high semantic cosine similarity into active master cases.
* **Configurable Karnataka Agency Smart Routing**: Automatically routes tickets to on-duty officers across 4 Karnataka civic authorities (**BBMP, BESCOM, BWSSB, BSWML**) based on least active load.
* **Officer Workflow & Proof of Resolution**: Field officers must upload after-fix photographic proof and detailed remediation logs to mark tickets resolved.
* **Citizen Verification & Reopen Loop**: The citizen retains the final authority to approve resolution (closing the case with a 1–5 star rating) or reject it (reopening the case with feedback).
* **Automated SLA Policies & Escalations**: Dynamic countdown timers with automated warnings (at 75% elapsed time) and administrative breach escalations.
* **Phase 16 Predictive ML Intelligence**: Machine learning models (trained on **128,573 historical Bengaluru grievance records**) providing real-time SLA breach probability prediction, resolution duration forecasting (MAE ±12.75h), 8-zone spatial risk heatmaps, and 14-day city-wide intake projections.

---

## 2. End-to-End System Architecture & Information Flow

```
                      CITIZEN PORTAL (Next.js 16)
               [Text (KN/EN) | Voice Audio | Photo | Live GPS]
                                     │
                                     ▼
                    FASTAPI ASYNCHRONOUS BACKEND API
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
   PREPROCESSING ENGINE                             OBJECT STORAGE & MEDIA
  • Kannada/Hinglish Normalization                 • Image Uploads & Metadata
  • Speech-to-Text Pipeline                        • Audio Recordings
             │
             ▼
   AI INTELLIGENCE SUITE
  • SentenceTransformers (Semantic Classification - 20 Classes)
  • Priority Prediction Engine (Critical, High, Medium, Low)
  • YOLOv8 Computer Vision (Potholes, Garbage, Streetlights, Hazards)
             │
             ▼
   MULTIMODAL EVIDENCE TRUST ENGINE
  • Live GPS vs. Photo EXIF GPS Delta (<500m verification)
  • Timestamp Sanity & Recency Check
  • Vision Object vs. Text Category Agreement Scoring
             │
             ▼
   DUPLICATE & INCIDENT DETECTION
  • Haversine Spatial Filter (Radius <= 100m)
  • Semantic Embedding Cosine Similarity (Score >= 0.85)
  • Clustered Master Issue Association
             │
             ▼
   KARNATAKA SMART ROUTING ENGINE
  • Agency Lookup (BBMP / BESCOM / BWSSB / BSWML)
  • 8 Bengaluru Administrative Zones & Ward Mapping
  • Least-Active Load Officer Assignment & Notification
             │
             ▼
   FIELD OFFICER OPERATIONAL WORKFLOW
  • Status: Registered ➔ Accepted ➔ In Progress
  • Remediation Field Work & On-Site Action
  • Mandatory After-Resolution Proof Photo & Remediation Notes
             │
             ▼
   CITIZEN CLOSURE & VERIFICATION LOOP
  • Citizen Approves ➔ Ticket Status: Closed (1–5 Star Rating)
  • Citizen Rejects ➔ Ticket Status: Reopened (Auto-Escalated to Officer)
             │
             ▼
   SLA MONITORING & ESCALATION DAEMON
  • Priority Timers: Critical (12h), High (24h), Medium (48h), Low (72h)
  • 75% SLA Warning Trigger ➔ Overdue SLA Breach Auto-Escalation
             │
             ▼
   GIS ANALYTICS & PHASE 16 PREDICTIVE ML SUITE
  • Interactive Spatial Hotspot Maps & Density Clustering
  • SLA Breach Risk Predictor (RandomForestClassifier - 84.4% Accuracy, 0.922 ROC-AUC)
  • Resolution Duration Estimator (RandomForestRegressor - MAE ±12.75h)
  • Spatial Hotspot Forecaster (8 Bengaluru Zones + Monsoon Multipliers)
  • 14-Day Grievance Intake Time-Series Forecasting
```

---

## 3. Complete Technology Stack

| Layer | Technology | Purpose & Rationale |
|---|---|---|
| **Frontend Framework** | **Next.js 16 (App Router) + React 19** | Ultra-responsive SSR/CSR architecture, component modularity, high performance. |
| **Language & Typing** | **TypeScript 5 + Python 3.11** | End-to-end type safety across client interfaces and backend models. |
| **Styling & UI Design** | **Tailwind CSS + Lucide React** | Sleek glassmorphic aesthetics, dark/light theme switching, responsive micro-animations. |
| **Mapping & GIS Client** | **Leaflet + React-Leaflet** | Interactive geospatial mapping, ward boundaries, live coordinate pin selection. |
| **Backend API Engine** | **FastAPI (ASGI)** | High-throughput asynchronous REST API with automatic OpenAPI/Swagger documentation. |
| **Primary Database** | **PostgreSQL** | ACID-compliant relational data management for complex grievance workflows. |
| **ORM & Migrations** | **SQLAlchemy 2.0 + Alembic** | Pythonic ORM with relationship cascading and schema migration management. |
| **Authentication & Security** | **JWT (JSON Web Tokens) + Bcrypt** | Role-Based Access Control (`Citizen`, `Officer`, `Admin`) with encrypted password hashing. |
| **Natural Language Processing** | **PyTorch + HuggingFace SentenceTransformers (`all-MiniLM-L6-v2`)** | 384-dimensional dense semantic text embeddings for classification and duplicate search. |
| **Multilingual Engine** | **Google Translate API / Indic Preprocessing Pipeline** | Zero-latency Kannada, Hinglish, and English translation and dialect normalization. |
| **Computer Vision** | **Ultralytics YOLOv8 (`yolov8n.pt`) + Pillow** | Real-time object detection identifying municipal hazards (potholes, garbage, wires). |
| **Machine Learning Engine** | **Scikit-Learn (RandomForest) + Joblib + NumPy + Pandas** | Predictive intelligence, SLA breach classification, duration regression, and spatial forecasting. |
| **Server & Deployment** | **Uvicorn ASGI Server + Node.js Engine** | Production-grade server environment with asynchronous request handling. |

---

## 4. Comprehensive 17-Phase Implementation Deep Dive

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      17-PHASE DEVELOPMENT BLUEPRINT                     │
 ├────────────────────────────────────────────────────────────────────────┤
 │ Phase 1: Requirements & Domain Model        Phase 10: Duplicate AI     │
 │ Phase 2: System Architecture & Skeleton     Phase 11: Smart Routing    │
 │ Phase 3: Database, RBAC & Auth              Phase 12: Officer Workflow │
 │ Phase 4: Karnataka Geography & Agencies     Phase 13: Citizen Closure  │
 │ Phase 5: Multimodal Complaint Collection    Phase 14: SLA Escalation   │
 │ Phase 6: Preprocessing & Translation        Phase 15: GIS Analytics    │
 │ Phase 7: AI Classification & Priority       Phase 16: Predictive ML    │
 │ Phase 8: YOLOv8 Computer Vision             Phase 17: E2E Verification │
 │ Phase 9: Multimodal Evidence Trust                                     │
 └────────────────────────────────────────────────────────────────────────┘
```

### Phase 1 — Requirements, Domain Modeling & Specifications
* **Core Deliverable**: Defined system boundaries, complaint classifications, operational roles, and Karnataka civic responsibilities.
* **Roles**: `Citizen`, `Field Officer`, `Department Officer`, `Agency Admin`, `System Admin`.
* **20 Standard Categories**: Garbage, Pothole, Water Leakage, No Water Supply, Streetlight, Sewage Overflow, Tree Fall, Road Damage, Illegal Dumping, Others, Power Outage, Fallen Electric Wire, Traffic Signal Fault, Road Encroachment, Metro Station Issue, Metro Track Damage, Metro Safety Concern, Illegal Construction, Park Maintenance, Layout Encroachment.

### Phase 2 — System Architecture & Modular Codebase Skeleton
* **Core Deliverable**: Established clean separation of concerns between `frontend/` (Next.js 16), `backend/` (FastAPI), and `ml_models/`.
* **Structure**: Configured CORS middleware, static upload directories (`backend/uploads`), environmental configurations (`backend/app/core/config.py`), and unified error handling.

### Phase 3 — Database, Users & Role-Based Access Control (RBAC)
* **Core Deliverable**: Secure user authentication and authorization using JWT bearer tokens.
* **Security Mechanics**: Passwords hashed with `passlib.context.CryptContext(schemes=["bcrypt"])`. Role enforcement via FastAPI dependency injection (`get_current_active_user`, role checks).
* **Database Models**: `User`, `Role`, `Officer`, `Department`.

### Phase 4 — Karnataka Geography & Civic Agency Master Model
* **Core Deliverable**: Configured 4 primary Karnataka civic agencies and 8 Bengaluru administrative zones.
* **Agencies**:
  1. **BBMP** (*Bruhat Bengaluru Mahanagara Palike*) — Municipal/civic services: roads, potholes, footpaths, storm drains, streetlights, trees, parks, public health, lakes.
  2. **BESCOM** (*Bangalore Electricity Supply Company Limited*) — Electricity distribution: power outages, electrical faults, voltage fluctuations, transformers, poles, wires, meters, billing.
  3. **BWSSB** (*Bangalore Water Supply and Sewerage Board*) — Water supply and underground drainage: dry taps, pipe leakage, contaminated water, sewer overflow, blocked drains, manhole covers.
  4. **BSWML** (*Bengaluru Solid Waste Management Limited*) — Solid waste and C&D waste: door-to-door garbage collection, auto-tipper, black spots, illegal dumping, garbage burning, segregation.
* **Zones**: East, West, South, Mahadevapura, Bommanahalli, Yelahanka, Rajarajeshwari Nagar, Dasarahalli.

### Phase 5 — Citizen Multimodal Complaint Collection
* **Core Deliverable**: Modern citizen intake interface supporting rich media submissions.
* **Features**: Text input with real-time character counters, audio recording via browser MediaStream API, Leaflet map pin placement with auto-reverse geocoding, and image evidence upload.

### Phase 6 — Preprocessing & Multilingual Translation Pipeline
* **Core Deliverable**: `backend/app/services/translation.py` normalizes raw Kannada, Hinglish, or English submissions into clean standard text.
* **Non-Destructive Storage**: Retains `original_description`, `detected_language`, and `audio_url` alongside the normalized `description`.

### Phase 7 — AI Classification & Priority Prediction Engine
* **Core Deliverable**: `backend/app/services/ai_classifier.py` computes dense semantic embeddings using SentenceTransformer `all-MiniLM-L6-v2`.
* **Classification**: Pre-computes representative embeddings for all 20 categories and classifies incoming text via maximum cosine similarity.
* **Priority Engine**: Evaluates safety keywords ("accident", "spark", "flood", "danger", "hazard", "injury") combined with category severity weights to output priority (`Critical`, `High`, `Medium`, `Low`) and a confidence score (0.0–1.0).

### Phase 8 — Computer Vision Validation (YOLOv8)
* **Core Deliverable**: `backend/app/services/vision.py` runs lightweight YOLOv8 (`yolov8n.pt`) on submitted photos.
* **Visual Object Detection**: Detects bounding boxes for objects such as potholes, waste piles, street lamps, cracks, and safety obstructions. Computes vision confidence score and validates visual alignment with text.

### Phase 9 — Geo-Tag & Multimodal Evidence Trust Scoring Engine
* **Core Deliverable**: `backend/app/services/evidence.py` calculates a composite **Trust Score (0–100%)** and qualitative level (`High`, `Medium`, `Low`, `Suspicious`).
* **Evaluation Matrix**:
  * **Live GPS vs. EXIF GPS**: Checks distance delta ($\le 500\text{m} = \text{Match}$).
  * **Timestamp Sanity**: Verifies photo creation timestamp within realistic recency windows.
  * **Image-Text Agreement**: Validates whether YOLO detected classes align with the predicted complaint category.
  * **Audit Log**: Generates human-readable explanations displayed to officers and administrators.

### Phase 10 — Duplicate & Incident Intelligence
* **Core Deliverable**: `backend/app/services/duplicate.py` stops redundant ticketing and detects localized clusters.
* **Clustering Algorithm**:
  1. Filters active complaints within **Haversine Distance $\le 100\text{m}$**.
  2. Same category constraint.
  3. Computes SentenceTransformer cosine similarity between complaint descriptions.
  4. If combined similarity score $\ge 0.85$, marks new complaint as duplicate and auto-joins citizen to the parent ticket.

### Phase 11 — Karnataka Smart Routing Engine
* **Core Deliverable**: `backend/app/services/routing.py` automates officer assignment without manual dispatch bottlenecks.
* **Load-Balancing Logic**:
  $$\text{Selected Officer} = \arg\min_{o \in \text{Officers}(\text{Dept})} \big( \text{ActiveComplaints}(o) \big)$$
* Automatically generates status history audit trails and officer dispatch notifications.

### Phase 12 — Field Officer Operational Workflow
* **Core Deliverable**: `frontend/src/app/officer/dashboard/page.tsx` + `backend/app/routers/complaints.py`.
* **State Progression**: `Registered` &rarr; `Accepted` &rarr; `In Progress` &rarr; `Resolved`.
* **Resolution Proof**: Officer must attach an "After" resolution image and descriptive remediation remarks before submitting.

### Phase 13 — Citizen Verification & Reopen Feedback Loop
* **Core Deliverable**: Gives citizens democratic oversight over resolution validity.
* **Approve Flow**: Citizen confirms fix &rarr; Status becomes `Closed` &rarr; Submits 1–5 star rating and optional praise remarks.
* **Reject Flow**: Citizen rejects inadequate fix &rarr; Status returns to `Reopened` &rarr; `reopen_count` increments &rarr; Officer receives urgent re-dispatch alert.

### Phase 14 — SLA Tracking, Warning Timers & Escalation Engine
* **Core Deliverable**: `backend/app/services/sla.py` enforces citizen service charters.
* **SLA Thresholds**:
  * **Critical**: 12 Hours
  * **High**: 24 Hours
  * **Medium**: 48 Hours
  * **Low**: 72 Hours
* **SLA States**: `Normal` ($\le 75\%$), `Warning` ($>75\%$ and $\le 100\%$), `Breached` ($>100\%$).
* **Auto-Escalation**: Unresolved breached tickets are flagged `is_escalated = True` and escalated to departmental supervisors.

### Phase 15 — GIS Mapping & Operational Analytics Dashboard
* **Core Deliverable**: `frontend/src/app/admin/dashboard/page.tsx` + `backend/app/routers/dashboard.py`.
* **Features**: Live spatial grievance pins, ward breakdown heatmaps, departmental resolution velocity charts, and SLA compliance telemetry.

### Phase 16 — Predictive Machine Learning Intelligence & Early Warning
* **Core Deliverable**: `backend/app/services/predictive.py` + `backend/app/routers/predictive.py`.
* **Trained on 128,573 Real BBMP/Bengaluru Records**:
  * **SLA Breach Risk Classifier**: `RandomForestClassifier` (84.4% Accuracy, 0.922 ROC-AUC).
  * **Resolution Duration Regressor**: `RandomForestRegressor` (MAE ±12.75h).
  * **Spatial Hotspot Forecaster**: Multi-factor scoring across 8 zones with seasonal monsoon multipliers (+35% to +45%).
  * **14-Day Time-Series Projections**: Linear trend + day-of-week seasonality forecasting city and department intakes.

### Phase 17 — Security Hardening, Automated E2E Testing & Deployment
* **Core Deliverable**: Full end-to-end integration test suite (`backend/test_e2e.py`) validating all 13 workflow steps with 100% pass rate, plus zero-error Next.js production build (`npm run build`).

---

## 5. Database Architecture & Data Models

```mermaid
erDiagram
    USERS ||--o{ COMPLAINTS : "files"
    USERS ||--o| OFFICERS : "has profile"
    ROLES ||--o{ USERS : "assigned to"
    DEPARTMENTS ||--o{ OFFICERS : "employs"
    DEPARTMENTS ||--o{ COMPLAINT_CATEGORIES : "manages"
    COMPLAINT_CATEGORIES ||--o{ COMPLAINTS : "classifies"
    COMPLAINT_CATEGORIES ||--o{ SLA_POLICIES : "governed by"
    COMPLAINTS ||--o{ COMPLAINT_IMAGES : "contains"
    COMPLAINTS ||--o{ COMPLAINT_STATUS_HISTORY : "tracks"
    COMPLAINTS ||--o| AI_PREDICTIONS : "analyzed by"
    COMPLAINTS ||--o| COMPLAINT_EVIDENCE_CHECKS : "verified by"
    COMPLAINTS ||--o{ DUPLICATE_COMPLAINT_MAPPINGS : "links"
    USERS ||--o{ NOTIFICATIONS : "receives"
```

### Key Database Entities

1. **`users`**: Master user identity records (`id`, `name`, `email`, `hashed_password`, `role_id`, `phone`, `status`, `created_at`).
2. **`roles`**: System permissions (`Citizen`, `Officer`, `Admin`).
3. **`departments`**: Karnataka service agencies (`BBMP`, `BESCOM`, `BWSSB`, `BSWML`).
4. **`officers`**: Officer profiles linking `user_id` to `department_id` with active duty status.
5. **`complaint_categories`**: 20 standardized grievance classifications linked to responsible departments.
6. **`complaints`**: Core ticket table (`id`, `citizen_id`, `category_id`, `description`, `original_description`, `language`, `audio_url`, `location_latitude`, `location_longitude`, `location_address`, `status`, `priority`, `assigned_officer_id`, `duplicate_of_complaint_id`, `sla_deadline`, `sla_status`, `is_escalated`, `citizen_verified`, `citizen_feedback_rating`, `citizen_feedback_remarks`, `reopen_count`, `created_at`, `updated_at`).
7. **`complaint_images`**: File storage metadata (`image_url`, `image_type` [Reporting/Resolution], `is_verified`, `confidence_score`).
8. **`complaint_status_history`**: Immutable audit logs tracking every status transition and actor.
9. **`ai_predictions`**: NLP classification results, confidence scores, and translation latencies.
10. **`complaint_evidence_checks`**: Multimodal composite trust scores, GPS distance offsets, and vision agreement metrics.
11. **`duplicate_complaint_mappings`**: Relational links between duplicate child tickets and master parent tickets.
12. **`sla_policies`**: Target resolution hours and warning thresholds per category/priority pair.
13. **`notifications`**: In-app alert dispatch logs for citizens and staff.

---

## 6. Multimodal AI & Machine Learning Intelligence Layer

```
                        INCOMING CITIZEN GRIEVANCE
                                     │
      ┌──────────────────────────────┼──────────────────────────────┐
      ▼                              ▼                              ▼
 TEXT INTAKE                   IMAGE INTAKE                  LOCATION INTAKE
(Kannada / English)          (Visual Evidence)              (Live Device GPS)
      │                              │                              │
      ▼                              ▼                              ▼
Translation / Normalization    YOLOv8 Object Detection        EXIF GPS Extraction
(Google / Indic Pipeline)    (Pothole, Waste, Hazards)      (Metadata Analysis)
      │                              │                              │
      ▼                              │                              ▼
SentenceTransformers                 │                     Haversine Distance Delta
(`all-MiniLM-L6-v2`)                 │                   (<500m live vs EXIF match)
• 20-Category Classification         │                              │
• Priority Prediction Engine         │                              │
      │                              │                              │
      └──────────────────────────────┼──────────────────────────────┘
                                     │
                                     ▼
                   MULTIMODAL EVIDENCE TRUST ENGINE
                  • Trust Score: 0 - 100%
                  • Qualitative Level: High / Medium / Low / Suspicious
                  • Verification Details Explanation
                                     │
                                     ▼
                   SPATIAL & SEMANTIC DUPLICATE ENGINE
                  • Haversine Distance <= 100m
                  • Cosine Text Similarity >= 0.85
                  • Master Ticket Aggregation
                                     │
                                     ▼
                   PHASE 16 PREDICTIVE ML INFERENCE
                  • SLA Risk Classifier (RandomForest, 84.4% Acc)
                  • Resolution Regressor (RandomForest, MAE ±12.75h)
                  • 14-Day Time Series Grievance Projection
```

### Mathematical Formulations

#### 1. Haversine Spatial Distance Formula
$$d = 2r \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta \text{lon}}{2}\right)} \right)$$
*Where $r = 6,371,000\text{ m}$.*

#### 2. Composite Evidence Trust Score
$$\text{TrustScore} = w_{\text{gps}} \cdot S_{\text{gps}} + w_{\text{time}} \cdot S_{\text{time}} + w_{\text{vision}} \cdot S_{\text{vision}}$$
*Where weights $w_{\text{gps}}=0.35$, $w_{\text{time}}=0.20$, $w_{\text{vision}}=0.45$.*

#### 3. Semantic Cosine Similarity
$$\text{Sim}(u, v) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$

---

## 7. Karnataka Smart Agency Routing & Operational Hierarchy

```
                                  GRIEVANCE CLASSIFICATION
                                             │
      ┌──────────────────┬───────────────────┼───────────────────┬───────────────────┐
      ▼                  ▼                   ▼                   ▼                   ▼
    BBMP               BWSSB               BESCOM              BMRCL             BDA & BTP
• Garbage          • Water Leakage     • Power Outage      • Metro Track       • Layout Encroach
• Potholes         • No Water          • Fallen Wire       • Metro Safety      • Illegal Constr.
• Road Damage      • Sewage Overflow   • Streetlight       • Metro Station     • Traffic Signals
• Tree Fall
      │                  │                   │                   │                   │
      └──────────────────┴───────────────────┼───────────────────┴───────────────────┘
                                             ▼
                                LEAST-LOAD ASSIGNMENT ALGORITHM
                                             │
                                             ▼
                           ASSIGNED ON-DUTY FIELD OFFICER IN ZONE
```

---

## 8. Complaint Lifecycle State Machine & SLA Escalation

```mermaid
stateDiagram-v2
    [*] --> Registered: Citizen Files Complaint
    Registered --> Accepted: Officer Acknowledges Case
    Registered --> Closed: Auto-Linked Duplicate
    Accepted --> In_Progress: Field Crew Dispatched
    In_Progress --> Resolved: Officer Uploads Proof Photo
    Resolved --> Closed: Citizen Approves (1-5 Stars)
    Resolved --> Reopened: Citizen Rejects (Feedback)
    Reopened --> In_Progress: Re-Assigned for Fix
    Closed --> [*]
```

### SLA Countdown Progression
```
[0% Elapsed] ─────────────── [75% Warning Trigger] ─────────────── [100% SLA Breach] ───> AUTO-ESCALATED
  (Normal)                      (Alert Sent)                           (Breached)
```

---

## 9. API Reference & Endpoint Catalog

### Authentication & Users (`/api/v1/auth`)
* `POST /api/v1/auth/register` — Citizen account registration.
* `POST /api/v1/auth/login` — OAuth2 JWT token login for Citizen, Officer, and Admin.
* `GET /api/v1/auth/me` — Retrieve active authenticated user profile.

### Complaints Engine (`/api/v1/complaints`)
* `POST /api/v1/complaints` — Submit multimodal complaint (Form text, audio URL, image upload, live coordinates).
* `GET /api/v1/complaints` — Retrieve complaints (Role-filtered: Citizen sees own, Officer sees assigned, Admin sees all).
* `GET /api/v1/complaints/{id}` — Get full complaint details with AI inference, SLA status, and history.
* `PUT /api/v1/complaints/{id}/status` — Officer status transition (`Accepted`, `In Progress`, `Resolved`).
* `POST /api/v1/complaints/{id}/resolution` — Officer resolution proof submission.
* `POST /api/v1/complaints/{id}/verify-resolution` — Citizen approve/reject resolution loop.
* `POST /api/v1/complaints/check-duplicate` — Proximity and semantic duplicate check.
* `GET /api/v1/complaints/{id}/evidence` — Retrieve multimodal evidence trust analysis.

### Dashboard & Analytics (`/api/v1/dashboard`)
* `GET /api/v1/dashboard/admin` — Master admin metrics, SLA compliance, department load, and GIS hotspot counts.

### Phase 16 Predictive Intelligence (`/api/v1/predictive`)
* `GET /api/v1/predictive/overview` — Early warning summary, model accuracy, top risk zone, 14-day projections.
* `POST /api/v1/predictive/estimate` — Instant ML SLA breach risk and resolution duration estimator.
* `GET /api/v1/predictive/hotspots` — Ranked hotspot ward predictions with proactive recommendations.
* `GET /api/v1/predictive/forecast` — 14-day and 30-day daily grievance intake time-series projections.
* `POST /api/v1/predictive/train` — Trigger ML model re-training on historical dataset.

---

## 10. Setup, Deployment & Testing Guide

### Prerequisites
* Python 3.10+ / 3.11+
* Node.js 18+ & npm
* PostgreSQL 14+ with PostGIS extension (or local PostgreSQL server)

### 1. Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Activate Virtual Environment
.\venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Run Database Seeder
python -m backend.app.seed

# Start FastAPI ASGI Backend Server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install Node Dependencies
npm install

# Start Next.js Development Server
npm run dev

# Or build for Production
npm run build
npm run start
```

### 3. Automated End-to-End Verification Suite
```powershell
# Run the complete 17-Phase automated test suite
python backend/test_e2e.py
```

### 4. Default Seeded Credentials
| Role | Email | Password | Responsible Authority |
|---|---|---|---|
| **System Admin** | `admin@civicai.gov.in` | `adminpassword` | State / City Administrator |
| **Citizen User** | `citizen@gmail.com` | `citizenpassword` | Public Citizen |
| **BBMP Officer** | `officer.bbmp@civicai.gov.in` | `officerpassword` | BBMP (Roads & Civic Services) |
| **BESCOM Officer** | `officer.bescom@civicai.gov.in` | `officerpassword` | BESCOM (Electricity) |
| **BWSSB Officer** | `officer.bwssb@civicai.gov.in` | `officerpassword` | BWSSB (Water & Sewerage) |
| **BSWML Officer** | `officer.bswml@civicai.gov.in` | `officerpassword` | BSWML (Solid Waste Management) |

---

## 🏁 Summary
The **Karnataka AI-Powered Civic Grievance Platform** successfully satisfies all requirements across all 17 phases of the development blueprint. The system combines verified citizen accessibility with state-of-the-art AI intelligence, robust operational workflows, and predictive analytics.
