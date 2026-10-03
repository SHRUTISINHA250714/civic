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
| **Primary Database** | **Neon Serverless Cloud PostgreSQL** | Serverless cloud PostgreSQL with SSL enforcement (`sslmode=require`), connection pooling (`pool_pre_ping=True`, `pool_recycle=300`, `pool_size=10`, `max_overflow=20`), and 3-attempt cold-start startup retry logic. Local PostgreSQL retained as developer fallback. |
| **ORM & Migrations** | **SQLAlchemy 2.0 + Alembic** | Pythonic ORM with relationship cascading and schema migration management. |
| **Authentication & Security** | **JWT (JSON Web Tokens) + Bcrypt** | Role-Based Access Control (`Citizen`, `Officer`, `Admin`) with encrypted password hashing. |
| **Natural Language Processing** | **PyTorch + HuggingFace SentenceTransformers (`all-MiniLM-L6-v2`)** | 384-dimensional dense semantic text embeddings for classification and duplicate search. |
| **Multilingual Engine** | **2-Tier Translation Pipeline (Google Translate + Kanglish Guard + Longest-Match Local Dictionary)** | High-precision language detection, Kanglish/Hinglish bypass prevention, and multi-word phrase fallback normalizer. |
| **Computer Vision** | **Ultralytics YOLOv8 (`yolov8n.pt`) + OpenCV + Pillow** | Real-time object detection identifying municipal hazards (potholes, garbage, wires) + Laplacian variance blur & exposure diagnostics. |
| **Machine Learning Engine** | **Scikit-Learn (RandomForest) + Joblib + NumPy + Pandas** | Predictive intelligence, SLA breach classification (84.4% acc, 0.922 AUC), duration regression, and spatial forecasting. |
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
* **47 Standard Categories across 4 State Authorities**:
  - **BBMP (Roads, Infrastructure & Municipal Services)**: Potholes & Damaged Roads, Broken Footpaths & Walkways, Blocked Stormwater Drains & Waterlogging, Streetlights Not Working, Broken Streetlight Pole, Dark Stretches & Unlit Roads, Fallen Trees & Broken Branches, Overgrown Tree Pruning, Encroached Roads & Footpaths, Illegal Hoardings & Banners, Lake Pollution & Encroachment, Lakes & Water Bodies, Damaged Public Parks & Playgrounds, Stray Dog Menace & Animal Control, Public Toilet Maintenance & Sanitation.
  - **BESCOM (Electricity Distribution & Consumer Services)**: Frequent Power Cuts & Load Shedding, Low Voltage & Voltage Fluctuations, Snapped & Low-Hanging Power Cables, Streetlight Power Supply Fault, Sparking Electric Transformers, Tilted & Damaged Electric Poles, Faulty / Burnt Electricity Meters, Electricity Bill Discrepancies, Dangerous Exposed Wiring & Shock Hazards, Tree Branches Touching Power Lines.
  - **BWSSB (Water Supply & Underground Drainage/Sewerage)**: No Drinking Water Supply, Low Water Pressure, Water Pipeline Burst & Leakage, Contaminated & Muddy Drinking Water, Sewage Overflow on Roads & Gutters, Blocked Sewer Lines & Choked Manholes, Damaged & Missing Manhole Covers, Faulty Water Meters & Billing, Water Tanker Supply Irregularities, Overflowing Drainage Storm Chambers.
  - **BSWML (Solid Waste & C&D Waste Management)**: Door-to-Door Garbage Not Collected, Irregular Garbage Collection Vehicle, Overflowing Garbage Bins & Community Blackspots, Illegal Roadside Waste Dumping, Foul Smell & Decomposing Waste Hazards, Open Garbage Burning & Toxic Smoke, Wet and Dry Waste Segregation Disputes, Construction & Demolition (C&D) Debris Dumping, Commercial Bulk Waste Dumping, Dead Animal Removal from Public Areas.

### Phase 2 — System Architecture & Modular Codebase Skeleton
* **Core Deliverable**: Established clean separation of concerns between `frontend/` (Next.js 16), `backend/` (FastAPI), and `ml_models/`.
* **Structure**: Configured CORS middleware, static upload directories (`backend/uploads`), environmental configurations (`backend/app/core/config.py`), and unified error handling.

### Phase 3 — Database, Users & Role-Based Access Control (RBAC)
* **Core Deliverable**: Secure user authentication and authorization using JWT bearer tokens.
* **Database Engine**: Neon Serverless Cloud PostgreSQL (`postgresql://...aws.neon.tech/neondb?sslmode=require`) with SSL enforcement, connection pooling (`pool_pre_ping=True`, `pool_recycle=300`, `pool_size=10`, `max_overflow=20`), and an automated 3-attempt exponential startup retry to handle serverless cold starts gracefully.
* **Security Mechanics**: Passwords hashed with `passlib.context.CryptContext(schemes=["bcrypt"])`. Role enforcement via FastAPI dependency injection (`get_current_active_user`, role checks).
* **Database Models**: `User`, `Role`, `Officer`, `Department`, `Complaint`, `ComplaintCategory`, `ComplaintImage`, `ComplaintStatusHistory`, `ComplaintEvidenceCheck`, `DuplicateComplaintMapping`, `AIPrediction`, `SLAPolicy`, `Notification`.

### Phase 4 — Karnataka Geography & Civic Agency Master Model
* **Core Deliverable**: Configured 4 primary Karnataka civic agencies and 8 Bengaluru administrative zones.
* **Agencies**:
  1. **BBMP** (*Bruhat Bengaluru Mahanagara Palike*) — Municipal/civic services: roads, potholes, footpaths, storm drains, streetlights, trees, parks, public health, lakes.
  2. **BESCOM** (*Bangalore Electricity Supply Company Limited*) — Electricity distribution: power outages, electrical faults, voltage fluctuations, transformers, poles, wires, meters, billing.
  3. **BWSSB** (*Bangalore Water Supply and Sewerage Board*) — Water supply and underground drainage: dry taps, pipe leakage, contaminated water, sewer overflow, blocked drains, manhole covers.
  4. **BSWML** (*Bengaluru Solid Waste Management Limited*) — Solid waste and C&D waste: door-to-door garbage collection, auto-tipper, black spots, illegal dumping, garbage burning, segregation.
* **Zones**: East, West, South, Mahadevapura, Bommanahalli, Yelahanka, Rajarajeshwari Nagar, Dasarahalli.
* **Category Parity**: 1:1 synchronization across 47 standardized categories between database seeder (`backend/app/seed.py`) and code taxonomy (`backend/app/services/ai.py`).

### Phase 5 — Citizen Multimodal Complaint Collection
* **Core Deliverable**: Modern citizen intake interface supporting rich media submissions.
* **Features**: Text input with real-time character counters, audio recording via browser MediaStream API, Leaflet map pin placement with auto-reverse geocoding, and image evidence upload.

### Phase 6 — Preprocessing & Multilingual Translation Pipeline
* **Core Deliverable**: `backend/app/services/ai.py` (`translate_text`) implements an intelligent 2-tier translation and transliteration pipeline.
* **Kanglish & Indic Detection Guard**: Requires verified high-confidence English (`langdetect` > 0.95) with zero Indic/Kanglish marker words to bypass translation, ensuring Romanized Kannada text is never misclassified as English.
* **Tier-2 Multi-Word Phrase Matching**: Offline local dictionary evaluates longest multi-word Kannada phrases first (e.g. `"ಬೀದಿ ದೀಪ"` &rarr; `"streetlight"`, `"ರಸ್ತೆ ಹಾಳಾಗಿದೆ"` &rarr; `"road is completely damaged"`) before individual tokens, followed by unmapped Kannada script stripping.
* **Non-Destructive Storage**: Retains `original_description` (raw citizen submission) alongside the normalized `description` (translated English text used for vector embeddings and officer queues).

### Phase 7 — AI Classification & Priority Prediction Engine
* **Core Deliverable**: `backend/app/services/ai.py` (`classify_complaint`, `predict_priority`) computes dense semantic embeddings using SentenceTransformer `all-MiniLM-L6-v2`.
* **Classification**: Classifies incoming normalized English text across 47 categories via maximum cosine similarity against pre-computed category anchor vectors.
* **Domain Routing Overrides**: Enforces domain-specific rules (e.g., municipal streetlighting and unlit roads strictly route to BBMP, whereas transformer sparking and power supply faults route to BESCOM).
* **Priority Engine**: Evaluates safety keywords ("accident", "spark", "flood", "danger", "hazard", "injury") combined with category severity weights to output priority (`Critical`, `High`, `Medium`, `Low`) and a confidence score (0.0–1.0).

### Phase 8 — Structured Computer Vision & Image Quality Validation (YOLOv8 & OpenCV)
* **Core Deliverable**: `backend/app/services/evidence.py` executes structured image analysis and quality diagnostics.
* **Ultralytics YOLOv8n**: Identifies civic hazard objects, outputting structured payloads:
  - `detected_objects`: Categorized COCO & civic infrastructure labels
  - `bounding_boxes`: Label, confidence score, and `[x1, y1, x2, y2]` bounding coordinates
  - `confidence_scores`: Highest confidence per detected object class
* **OpenCV Preprocessing & Quality Diagnostics**:
  - Blurriness detection via Laplacian variance ($\text{var} < 25.0 \implies \text{BLURRY}$)
  - Exposure diagnostics (underexposed mean brightness $< 25$ or overexposed $> 245$)
  - Minimum resolution thresholding ($100 \times 100\text{ px}$)
* **PIL EXIF Metadata Parsing**:
  - GPS coordinate extraction (DMS rational conversion with hemispheric signs)
  - UTC capture timestamps (with legacy `_getexif` and modern IFD subtable support)
  - Camera make/model hardware signatures

### Phase 9 — Hard-Gate Multimodal Evidence Verification & Trust Scoring Engine
* **Core Deliverable**: `backend/app/services/evidence.py` implements a 4-Gate verification architecture with absolute server-side authority.
* **The 4 Hard Verification Gates**:
  1. **Gate 1: Live GPS vs EXIF Cross-Validation**: Haversine distance threshold ($\le 500\text{m} \implies \text{MATCH}$, $\ge 5000\text{m} \implies \text{SUSPICIOUS}$). Handles missing EXIF as `EXIF_MISSING`. Incorporates browser `gps_accuracy`.
  2. **Gate 2: Timestamp Freshness**: Rejects future timestamps ($> 10\text{m} \implies \text{FUTURE} \to \text{MANUAL\_REVIEW}$) and flags stale evidence ($> 72\text{h} \implies \text{STALE} \to \text{MANUAL\_REVIEW}$).
  3. **Gate 3: Semantic Complaint $\leftrightarrow$ Image Matching**: Cross-evaluates complaint text/category against image content using SentenceTransformers `all-MiniLM-L6-v2` and YOLO object categories. Negative filters for cross-category mismatches (e.g. Pothole complaint with Garbage photo) immediately trigger `MISMATCH`. *Semantic mismatches are strictly barred from being VERIFIED*.
  4. **Gate 4: Reused Image Detection (Perceptual Hashing)**: Generates 64-bit difference hashes (`dHash`). Hamming distance $\le 4$ detects recycled photos across complaints, flagging `is_reused_image = True` $\to$ `SUSPICIOUS`.
* **Hard-Gate Decisions**: `VERIFIED`, `PARTIALLY_VERIFIED`, `MANUAL_REVIEW`, `SUSPICIOUS`, `REJECTED`.
* **Composite Trust Score (0–100%)**: Weighted composition: GPS ($35\%$), Timestamp ($20\%$), Semantic Vision ($45\%$), clamped to $\le 24\%$ on `REJECTED` and $\le 35\%$ on `SUSPICIOUS`.
* **Audit Endpoint**: `GET /api/v1/complaints/{id}/evidence` exposes the full verification payload to officers and citizens.

### Phase 10 — Duplicate & Incident Intelligence
* **Core Deliverable**: `backend/app/services/duplicate.py` stops redundant ticketing and detects localized clusters.
* **Translated English Embedding Guarantee**: Generates embeddings strictly from translated English descriptions (`candidate.description` / `candidate.translated_text`), preventing duplicate detection failures when one report is submitted in Kannada script, another in Romanized Kanglish, and a third in English.
* **Clustering Algorithm**:
  1. Filters active complaints within **Haversine Distance $\le 100\text{m}$**.
  2. Same category constraint.
  3. Computes SentenceTransformer cosine similarity between translated complaint descriptions.
  4. If combined similarity score $\ge 0.85$, marks new complaint as duplicate (`duplicate_of_complaint_id`), increments parent `impact_count`, and auto-joins citizen to the parent ticket.

### Phase 11 — Karnataka Smart Routing Engine
* **Core Deliverable**: `backend/app/services/routing.py` automates officer assignment without manual dispatch bottlenecks.
* **Load-Balancing Logic**:
  $$\text{Selected Officer} = \arg\min_{o \in \text{Officers}(\text{Dept})} \big( \text{ActiveComplaints}(o) \big)$$
* Automatically generates status history audit trails and officer dispatch notifications.

### Phase 12 — Field Officer Operational Workflow
* **Core Deliverable**: `frontend/src/app/officer/dashboard/page.tsx` + `backend/app/routers/complaints.py` + `backend/app/routers/officers.py`.
* **Enforced Translated-Only English Display**: Field officers strictly receive and view translated English descriptions across all complaint queues to eliminate language barriers on site, while citizens continue viewing their original native text.
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

### Phase 17 — Security Hardening, Automated Testing & Verification Harness
* **Core Deliverable**: Comprehensive multi-suite test harness confirming zero regressions across all workflows:
  1. `test_neon_connection.py`: Verifies Neon cloud database connectivity, SSL enforcement, and schema tables.
  2. `test_evidence_gates.py`: Validates all 11 evidence hard-gate scenarios (GPS deltas, timestamp freshness, semantic agreement, dHash).
  3. `test_kanglish_duplicate.py` & `test_multilingual_duplicate.py`: Verifies duplicate detection across Kannada, Kanglish, Hinglish, and English.
  4. `test_multiword_phrase_translation.py`: Validates longest-first multi-word Kannada phrase replacement.
  5. `test_officer_translated_only.py`: Confirms field officers never receive untranslated native script in queues.
  6. `test_e2e.py`: Executes 13-step comprehensive lifecycle test from registration to citizen verification.
  7. Production build validation (`npm run build`) with zero errors.

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
5. **`complaint_categories`**: 47 standardized grievance classifications linked to the 4 Karnataka departments with 1:1 parity between code taxonomy and database.
6. **`complaints`**: Core ticket table (`id`, `citizen_id`, `category_id`, `description`, `original_description`, `language`, `detected_language`, `audio_url`, `location_latitude`, `location_longitude`, `location_address`, `status`, `priority`, `assigned_officer_id`, `duplicate_of_complaint_id`, `impact_count`, `sla_deadline`, `sla_status`, `is_escalated`, `citizen_verified`, `citizen_feedback_rating`, `citizen_feedback_remarks`, `reopen_count`, `created_at`, `updated_at`). Provides dynamic `translated_text` property for safe multilingual handling.
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
      ┌──────────────────┬───────────────────┼───────────────────┐
      ▼                  ▼                   ▼                   ▼
    BBMP               BESCOM              BWSSB               BSWML
• Potholes         • Power Outage      • Water Leakage     • Garbage Dumping
• Road Damage      • Snapped Wire      • Pipe Burst        • Waste Burning
• Footpath & Drain • Transformer Spark • No Water Supply   • Auto-Tipper Delay
• Tree Fall        • Voltage Surge     • Sewage Overflow   • Blackspot Cleanup
      │                  │                   │                   │
      └──────────────────┴───────────────────┼───────────────────┘
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
* `POST /api/v1/auth/register` — Citizen account registration and password hashing.
* `POST /api/v1/auth/login` — OAuth2 JWT token login for Citizen, Officer, and Admin.
* `GET /api/v1/auth/me` — Retrieve active authenticated user profile.
* `PUT /api/v1/auth/profile` — Update user profile details.

### Complaints Engine (`/api/v1/complaints`)
* `POST /api/v1/complaints` — Submit multimodal complaint (Form text, audio URL, image upload, live coordinates, GPS accuracy radius).
* `GET /api/v1/complaints` — Retrieve complaints (Role-filtered: Citizen sees own, Officer sees assigned translated English queue, Admin sees all).
* `GET /api/v1/complaints/{id}` — Get full complaint details with AI inference, SLA status, evidence verification status, and history.
* `GET /api/v1/complaints/{id}/evidence` — Retrieve multimodal evidence trust analysis and 4-gate verification diagnostic report.
* `GET /api/v1/complaints/departments-categories` — Public listing of the 4 civic departments and 47 categories.
* `GET /api/v1/complaints/nearby` — Fetch nearby geotagged complaints within radius.
* `POST /api/v1/complaints/preview-ai` — Real-time AI preview of category, priority, and translation before submission.
* `POST /api/v1/complaints/check-duplicate` — Proximity (100m) and translated-text semantic duplicate check.
* `PUT /api/v1/complaints/{id}/status` — Officer status transition (`Accepted`, `In Progress`).
* `POST /api/v1/complaints/{id}/resolve` — Officer resolution proof submission (mandatory after-photo and notes).
* `POST /api/v1/complaints/{id}/verify-resolution` — Citizen approve (1–5 star rating -> `Closed`) or reject (`Reopened`) loop.

### Field Officers & Administration (`/api/v1/officers`)
* `GET /api/v1/officers/departments` — List departments and active officer counts.
* `GET /api/v1/officers/categories` — List 47 categories with current routing rules.
* `PUT /api/v1/officers/categories/{id}/routing` — Admin update of category routing parameters.
* `GET /api/v1/officers/officers` — List field officers, department affiliations, and active caseloads.
* `PUT /api/v1/officers/officers/{id}/status` — Toggle officer duty status (`On Duty`, `Inactive`).

### Dashboard & Analytics (`/api/v1/dashboard`)
* `GET /api/v1/dashboard/citizen` — Citizen dashboard metrics, active tickets, and recent activity.
* `GET /api/v1/dashboard/officer` — Field officer workload, SLA countdowns, and assigned queue.
* `GET /api/v1/dashboard/admin` — Master admin metrics, SLA compliance, department load, and GIS hotspot counts.
* `POST /api/v1/dashboard/admin/run-sla-check` — Trigger manual/daemon SLA status evaluation across active complaints.

### Notifications (`/api/v1/notifications`)
* `GET /api/v1/notifications` — Fetch user's notification alerts.
* `PUT /api/v1/notifications/{id}/read` — Mark notification as read.
* `PUT /api/v1/notifications/read-all` — Mark all notifications as read.

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
* Neon Serverless Cloud PostgreSQL (or local PostgreSQL 14+ instance)

### 1. Database Configuration (.env)
Configure your connection string in `backend/.env` (and root `.env`):
```env
# Neon Serverless Cloud PostgreSQL
DATABASE_URL=postgresql://user:password@ep-domain.neon.tech/neondb?sslmode=require

# JWT Secret Key
SECRET_KEY=karnataka_civic_grievance_management_ai_secret_key_2026

# AI Models
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
YOLO_MODEL=yolov8n.pt
```

### 2. Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Activate Virtual Environment
.\venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Seed Database (Initializes tables, 4 Karnataka authorities, 47 categories, test users)
python -m backend.app.seed

# Start FastAPI ASGI Server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API: `http://127.0.0.1:8000`
* Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```powershell
# Open terminal in frontend directory
cd frontend

# Install Node Dependencies
npm install

# Start Next.js Development Server
npm run dev
```
* Frontend Portal: `http://localhost:3000`

### 4. Specialized Automated Verification Suites
```powershell
# 1. Neon Cloud Serverless Database Connectivity & Health
python backend/test_neon_connection.py

# 2. Hard-Gate Evidence Verification Test Suite (11 Scenarios)
python -m backend.test_evidence_gates

# 3. Multilingual & Kanglish Duplicate Detection Tests
python backend/test_kanglish_duplicate.py
python backend/test_multilingual_duplicate.py

# 4. Multi-Word Kannada Phrase Translation Fallback Test
python backend/test_multiword_phrase_translation.py

# 5. Field Officer Translated-Only Text Verification Test
python backend/test_officer_translated_only.py

# 6. Complete End-to-End 17-Phase Test Suite
python backend/test_e2e.py
```

### 5. Default Seeded Credentials
| Role | Email | Password | Responsible Authority |
|---|---|---|---|
| **System Admin** | `admin@civicai.gov.in` | `adminpassword` | State / City Administrator (`/admin/dashboard`) |
| **Citizen User** | `citizen@gmail.com` | `citizenpassword` | Public Citizen (`/citizen/dashboard`) |
| **BBMP Officer** | `officer.bbmp@civicai.gov.in` | `officerpassword` | BBMP Roads, Lights & Infrastructure (`/officer/dashboard`) |
| **BESCOM Officer** | `officer.bescom@civicai.gov.in` | `officerpassword` | BESCOM Electricity & Power (`/officer/dashboard`) |
| **BWSSB Officer** | `officer.bwssb@civicai.gov.in` | `officerpassword` | BWSSB Water Supply & Sewerage (`/officer/dashboard`) |
| **BSWML Officer** | `officer.bswml@civicai.gov.in` | `officerpassword` | BSWML Solid Waste Management (`/officer/dashboard`) |

---

## 11. Recent Engineering Enhancements & Infrastructure Hardening

1. **Neon Serverless PostgreSQL Migration**:
   - Transitioned from local instances to Neon serverless cloud PostgreSQL with SSL enforcement (`sslmode=require`).
   - Integrated production connection pooling (`pool_pre_ping=True`, `pool_recycle=300`, `pool_size=10`, `max_overflow=20`) and 3-attempt exponential startup retry backoff in FastAPI to handle cloud cold starts gracefully.
2. **Translated-Text Embedding for Spatial Duplicate Detection**:
   - Fixed duplicate detection in `backend/app/services/duplicate.py` to generate SentenceTransformer embeddings strictly on translated English text rather than untranslated native descriptions, ensuring accurate duplicate clustering across Kannada, Kanglish, Hinglish, and English submissions.
3. **Kanglish & Indic Language Detection Guard**:
   - Overrode `langdetect` false-positive English classifications on Romanized Indic words, guaranteeing translation before classification or duplicate matching.
4. **Longest-First Multi-Word Kannada Phrase Fallback**:
   - Solved single-token dictionary matching limitations by matching longest multi-word phrases (e.g. `"ಬೀದಿ ದೀಪ"`, `"ರಸ್ತೆ ಹಾಳಾಗಿದೆ"`) first, followed by clean removal of residual unmapped script.
5. **Officer Queue Translated-Only Presentation**:
   - Guaranteed that field officers and officer APIs strictly view translated English descriptions across all queue items, eliminating vernacular language barriers for on-site crews.
6. **1:1 Taxonomy & Database Category Parity**:
   - Aligned all 47 categories between `backend/app/services/ai.py` (`CATEGORY_HIERARCHY`) and `backend/app/seed.py` (`complaint_categories`), resolving category drift.

---

## 🏁 Summary
The **Karnataka AI-Powered Civic Grievance Platform** successfully satisfies all requirements across all 17 phases of the development blueprint. The system combines verified citizen accessibility with state-of-the-art AI intelligence, robust operational workflows, and predictive analytics.
