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
* **Multimodal Citizen Intake**: Text in Kannada/English/Hinglish, voice-to-text recording, live device geolocation, and mandatory photo capture with decoupled, high-performance rendering.
* **Zero-Drop Translation & Preprocessing**: Automatically normalizes Kannada/Hinglish input to standard English for NLP classification while preserving the citizen's original statement and audio recordings. Features strict word-boundary checks protecting genuine English text with Indian location names from corruption.
* **Explainable Multimodal Evidence Trust Scoring (0–100%)**: Cross-evaluates live device GPS against EXIF photo metadata, checks upload timestamp plausibility, and validates whether YOLOv8 computer vision detected objects match the reported category with explicit *"Image matches complaint"* vs *"Image does not match complaint"* status badges.
* **Spatial & Semantic Duplicate Detection with Image Mismatch Guard**: Prevents ticket flooding by merging new complaints within a 100m radius and high semantic cosine similarity into active master cases, with a hard multimodal filter rejecting complaints with mismatched evidence from duplicate linking.
* **Deterministic Karnataka Agency Smart Routing**: Deterministically routes grievances to responsible state authorities (potholes and road damage to BBMP, garbage and litter to BSWML, water and drainage to BWSSB, power hazards to BESCOM) and assigns them to on-duty officers based on least active load.
* **Officer Workflow & Proof of Resolution**: Field officers view dual clearly-labeled sections (*"Original Complaint"* and *"English Translation"*), inspect separate Citizen Evidence vs Officer Repair Verification images, and must upload after-fix photographic proof with detailed remediation logs to mark tickets resolved.
* **Citizen Verification & Reopen Loop**: The citizen retains the final authority to approve resolution (closing the case with a 1–5 star rating) or reject it (reopening the case with feedback), with immediate UI state synchronization hiding the verification prompt once completed.
* **Automated SLA Policies, Duration Tracking & Escalations**: Dynamic countdown timers displaying exact SLA duration, live time remaining, breach warning pills, and resolution SLA compliance tracking (*"Met SLA"* vs *"Breached SLA"*).
* **Frictionless Authentication & Session Resilience**: Interactive password visibility toggles (`Eye`/`EyeOff`) and dual-storage session persistence (`tokenStorage.ensureSession`) preventing logout drops on page refreshes.
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
* **Core Deliverable**: Secure user authentication, password controls, session persistence, and authorization using JWT bearer tokens.
* **Database Engine**: Neon Serverless Cloud PostgreSQL (`postgresql://...aws.neon.tech/neondb?sslmode=require`) with SSL enforcement, connection pooling (`pool_pre_ping=True`, `pool_recycle=300`, `pool_size=10`, `max_overflow=20`), and an automated 3-attempt exponential startup retry to handle serverless cold starts gracefully.
* **Password Visibility Toggle**: Interactive `Eye` / `EyeOff` toggles on all password and confirm-password fields across `/login` and `/register`, allowing citizens and officers to verify inputs before submission.
* **Dual-Storage Session Persistence**: Client-side dual-storage fallback (`localStorage` + `sessionStorage`) with `tokenStorage.ensureSession(expectedRole)` in `frontend/src/lib/api.ts` to prevent premature logouts or session drops upon page reload across Citizen and Officer dashboards.
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

### Phase 5 — Citizen Multimodal Complaint Collection & High-Performance Intake
* **Core Deliverable**: Modern citizen intake interface supporting rich media submissions and high-performance dashboard rendering.
* **Features**: Text input with real-time character counters, audio recording via browser MediaStream API, Leaflet map pin placement with auto-reverse geocoding, and compulsory image evidence upload.
* **Citizen Dashboard Loading Optimization**: Decoupled primary complaint fetching from secondary nearby geolocation queries to eliminate UI rendering freezes. The backend `GET /api/v1/complaints` leverages SQLAlchemy eager loading (`joinedload` on `category`, `category.department`, `assigned_officer`, `user`, and `selectinload` on `images`), eliminating N+1 queries and reducing dashboard load times drastically.

### Phase 6 — Preprocessing & Multilingual Translation Pipeline
* **Core Deliverable**: `backend/app/services/ai.py` (`translate_text`) implements an intelligent 2-tier translation and transliteration pipeline.
* **Kanglish & Indic Detection Guard with Boundary Precision**: Requires verified high-confidence English (`langdetect` > 0.95) with zero Indic/Kanglish marker words to bypass translation. Uses strict word boundaries (`\b[a-zA-Z]+\b`) and a clean Indic lexicon.
* **Indian Location Preservation**: Protects genuine English text containing local Karnataka location names (e.g. *"potholes on MG Road"*, *"Indiranagar"*, *"Koramangala"*, *"Bengaluru"*) from being falsely classified as Kanglish or corrupted, preserving the detected language as `en`.
* **Tier-2 Multi-Word Phrase Matching**: Offline local dictionary evaluates longest multi-word Kannada phrases first (e.g. `"ಬೀದಿ ದೀಪ"` &rarr; `"streetlight"`, `"ರಸ್ತೆ ಹಾಳಾಗಿದೆ"` &rarr; `"road is completely damaged"`) before individual tokens, followed by unmapped Kannada script stripping.
* **Non-Destructive Storage**: Retains `original_description` (raw citizen submission) alongside the normalized `description` (translated English text used for vector embeddings and officer queues).

### Phase 7 — AI Classification & Priority Prediction Engine
* **Core Deliverable**: `backend/app/services/ai.py` (`classify_complaint`, `predict_priority`) computes dense semantic embeddings using SentenceTransformer `all-MiniLM-L6-v2`.
* **Deterministic Department Routing Rules**: Implements strict precedence rules before vector similarity to prevent misclassifications:
  1. **Roads & Potholes &rarr; BBMP**: Keywords like *"pothole"*, *"crater"*, *"sinkhole"*, *"road damage"*, *"broken asphalt"* (e.g. *"potholes on MG Road"*) deterministically route to BBMP `Potholes & Damaged Roads`.
  2. **Solid Waste & Garbage &rarr; BSWML**: Keywords like *"garbage"*, *"trash"*, *"dump"*, *"debris"* route strictly to BSWML (`Door-to-Door Garbage Not Collected` or `Illegal Roadside Waste Dumping`).
  3. **Water & Drainage &rarr; BWSSB**: Keywords like *"pipe burst"*, *"water supply"*, *"manhole"*, *"sewage"* route to BWSSB.
  4. **Streetlights vs. Grid**: Municipal streetlighting faults route to BBMP, whereas transformer sparking, high-voltage wires, and grid outages route to BESCOM.
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
  3. **Gate 3: Semantic Complaint $\leftrightarrow$ Image Matching**: Cross-evaluates complaint text/category against image content using SentenceTransformers `all-MiniLM-L6-v2` and YOLO object categories. Strict negative filters detect cross-category mismatches (e.g., streetlight or pothole complaint with garbage photo, or road complaint with indoor furniture). *Semantic mismatches are strictly barred from being VERIFIED*.
  4. **Gate 4: Reused Image Detection (Perceptual Hashing)**: Generates 64-bit difference hashes (`dHash`). Hamming distance $\le 4$ detects recycled photos across complaints, flagging `is_reused_image = True` $\to$ `SUSPICIOUS`.
* **Standardized Image Verification Result**: Computes a clear user-facing `image_verification_result` string exposed across Citizen and Officer dashboards:
  - `"Image matches complaint"` for confirmed semantic alignment (`MATCH`).
  - `"Image does not match complaint"` for cross-category mismatches (`MISMATCH`).
  - `"Image partially matches complaint"` for ambiguous or unconfirmed imagery (`PARTIAL`).
* **Hard-Gate Decisions**: `VERIFIED`, `PARTIALLY_VERIFIED`, `MANUAL_REVIEW`, `SUSPICIOUS`, `REJECTED`.
* **Composite Trust Score (0–100%)**: Weighted composition: GPS ($35\%$), Timestamp ($20\%$), Semantic Vision ($45\%$), clamped to $\le 24\%$ on `REJECTED` and $\le 35\%$ on `SUSPICIOUS`.
* **Audit Endpoint**: `GET /api/v1/complaints/{id}/evidence` exposes the full verification payload to officers and citizens.

### Phase 10 — Duplicate & Incident Intelligence with Image Mismatch Guard
* **Core Deliverable**: `backend/app/services/duplicate.py` stops redundant ticketing and detects localized clusters.
* **Translated English Embedding Guarantee**: Generates embeddings strictly from translated English descriptions (`candidate.description` / `candidate.translated_text`), preventing duplicate detection failures across Kannada, Kanglish, Hinglish, and English submissions.
* **Multimodal Image Mismatch Duplicate Guard**: Visual evidence analysis executes *prior* to duplicate evaluation. If an incoming complaint's image is evaluated as a semantic mismatch (`image_semantic_status == "MISMATCH"`, e.g. garbage photo uploaded for a pothole ticket), it is strictly barred from linking as a duplicate of any existing ticket.
* **Clustering Algorithm**:
  1. Filters active complaints within **Haversine Distance $\le 100\text{m}$**.
  2. Same category constraint.
  3. Computes SentenceTransformer cosine similarity between translated complaint descriptions.
  4. If combined similarity score $\ge 0.85$ and image semantic status $\neq \text{MISMATCH}$, marks new complaint as duplicate (`duplicate_of_complaint_id`), increments parent `impact_count`, and auto-joins citizen to the parent ticket.

### Phase 11 — Karnataka Smart Routing Engine
* **Core Deliverable**: `backend/app/services/routing.py` automates officer assignment without manual dispatch bottlenecks.
* **Load-Balancing Logic**:
  $$\text{Selected Officer} = \arg\min_{o \in \text{Officers}(\text{Dept})} \big( \text{ActiveComplaints}(o) \big)$$
* Integrates deterministic category mapping to ensure cases flow directly to the correct municipal authority (BBMP, BESCOM, BWSSB, BSWML) and the least-loaded on-duty officer in the zone.
* Automatically generates status history audit trails and officer dispatch notifications.

### Phase 12 — Field Officer Operational Workflow
* **Core Deliverable**: `frontend/src/app/officer/dashboard/page.tsx` + `backend/app/routers/complaints.py` + `backend/app/routers/officers.py`.
* **Dual-Section Translation Presentation**: Replaced single text display with dual, clearly-labeled cards:
  1. **Original Complaint**: Displays the exact verbatim text submitted by the citizen (in native Kannada script, Kanglish, Hinglish, or English), along with the preserved audio player when voice evidence is available.
  2. **English Translation**: Displays the AI-normalized English translation for immediate operational triage and work-order dispatch.
* **Separated Media Proof (Original vs. Repair)**: Media evidence is categorized into distinct views:
  - **Citizen Evidence (Original)**: Initial incident photo uploaded by the reporting citizen (`image_type == "Reporting"`).
  - **Officer Repair Verification (Completed)**: Post-remediation proof uploaded by the field crew (`image_type == "Resolution"`).
* **Evidence Audit & Semantic Alignment Badge**: Displays the `image_verification_result` badge directly in the officer's case audit panel (*"Image matches complaint"* vs *"Image does not match complaint"*).
* **State Progression**: `Registered` &rarr; `Accepted` &rarr; `In Progress` &rarr; `Resolved`.
* **Mandatory Resolution Validation Gate**:
  - **Mandatory After-Resolution Photo Proof**: Image upload is compulsory. Validates format (`.jpg`, `.jpeg`, `.png`, `.webp`), minimum size ($\ge 2\text{KB}$), image integrity (Pillow verification), and minimum dimensions ($\ge 50\times 50\text{px}$).
  - **Mandatory Descriptive Remediation Notes**: Explanation of actual action taken is compulsory ($\ge 15$ characters). Strictly rejects empty notes, short phrases, and meaningless placeholders (`"done"`, `"fixed"`, `"resolved"`, `"ok"`, `"test"`, `"action taken"`).

### Phase 13 — Citizen Verification & Reopen Feedback Loop
* **Core Deliverable**: Gives citizens democratic oversight over resolution validity.
* **Instant UI Synchronization & Action Guard**: Upon submitting verification (approve or reject), the Citizen Dashboard immediately updates local component state without requiring a manual page refresh. The "Verify Resolution" action button is automatically hidden once verification is completed (`citizen_verified == true`), displaying permanent feedback confirmation and preventing accidental duplicate submissions.
* **Approve Flow**: Citizen confirms fix &rarr; Status becomes `Closed` &rarr; Submits 1–5 star rating and optional praise remarks.
* **Reject Flow**: Citizen rejects inadequate fix &rarr; Status returns to `Reopened` &rarr; `reopen_count` increments &rarr; Officer receives urgent re-dispatch alert.

### Phase 14 — SLA Tracking, Predictive Early Warning & Progressive Escalation
* **Core Deliverable**: `backend/app/services/sla.py` + `backend/app/schemas/complaint.py`.
* **Unchanged Base SLA Service Charters**:
  * **Critical**: 12 Hours
  * **High**: 24 Hours
  * **Medium**: 48 Hours
  * **Low**: 72 Hours
* **Comprehensive SLA Duration & Time Remaining Telemetry**:
  - `sla_duration_hours` & `sla_duration_str`: Exposes allocated resolution window (e.g. *"12h (Critical)"*, *"24h (High)"*).
  - `time_remaining_str`: Formats human-readable countdowns (*"14h 32m remaining"* or *"Overdue by 2h 10m"*).
  - `resolution_sla_status`: Evaluates whether historical resolution satisfied the service charter (*"Met SLA"* vs *"Breached SLA"*).
  - `is_breached`: Boolean indicator powering dynamic warning badges on Citizen and Officer dashboard ticket headers.
* **Phase 16 Predictive SLA Early Warning**: Calls the predictive ML model before the 75% elapsed threshold. If breach probability $\ge 60\%$, an early alert is triggered before the conventional 75% warning timer.
* **SLA States & Progressive 3-Tier Escalation**: `Normal` ($\le 75\%$), `Warning` ($>75\%$ and $\le 100\%$), `Breached` ($>100\%$). If a breached complaint remains unresolved, it escalates progressively:
  * **Level 1** ($\le 12\text{h}$ overdue): Escalated to Assistant Executive Engineer (AEE).
  * **Level 2** ($12\text{–}24\text{h}$ overdue): Escalated to Executive Engineer (EE).
  * **Level 3** ($> 24\text{h}$ overdue): Escalated to Chief Commissioner & Karnataka State Monitoring Cell.

### Phase 15 — GIS Mapping & Operational Analytics Dashboard
* **Core Deliverable**: `frontend/src/app/admin/dashboard/page.tsx` + `frontend/src/components/MapComponent.tsx` + `backend/app/routers/dashboard.py`.
* **Current + Predicted Hotspots**: Displays both empirical active complaint density clusters (🔥 Flame pulse) and Phase 16 ML predicted surge hotspots (⚡ Violet radar pulse) on an interactive Leaflet map.
* **"Reported by X people" Marker Display**: Map markers and cards report duplicate citizen impact count (`impact_count`) to highlight multi-citizen incidents.
* **5 Interactive Filters & Layer Controls**: Full filtering toolbar supporting Agency (BBMP, BESCOM, BWSSB, BSWML), Grievance Category, Urgency Priority, Resolution Status, and Date Range (Today, 7d, 30d, All), with dynamic layer toggles.

### Phase 16 — Predictive Machine Learning Intelligence & Continuous Retraining
* **Core Deliverable**: `backend/app/services/predictive.py` + `backend/app/routers/predictive.py` + `frontend/src/app/admin/dashboard/page.tsx`.
* **Preserved Models & 13 Engineered Features**: Keeps `RandomForestClassifier` and `RandomForestRegressor` trained across 13 engineered dimensions: category, ward, zone, department, priority, month, day of week, hour, monsoon indicator, weekend indicator, department backlog count, SLA status code, and duplicate impact count.
* **Rigorous 70/15/15 Evaluation Split**: Evaluated on 70% Train, 15% Validation, and 15% Test partitions.
* **Comprehensive Metrics Reporting**:
  * **Classification**: Accuracy, Precision, Recall, F1-Score, ROC-AUC.
  * **Regression**: Mean Absolute Error (MAE in hours), Root Mean Squared Error (RMSE in hours), $R^2$ Score.
  * **Validation Set**: Separate validation metrics reported on unseen data.
* **Feature Importance & Explainability (XAI)**: Gini feature importances across all 13 dimensions visualised in progress bars with plain-language risk driver attribution.
* **Continuous Database Retraining**: `POST /api/v1/predictive/train` dynamically extracts newly resolved complaints from PostgreSQL, combines them with historical data, and persists updated models.

### Phase 17 — Security Hardening, Automated Testing & Verification Harness
* **Core Deliverable**: Comprehensive multi-suite test harness confirming zero regressions across all workflows:
  1. `test_neon_connection.py`: Verifies Neon cloud database connectivity, SSL enforcement, and schema tables.
  2. `test_evidence_gates.py`: Validates all 11 evidence hard-gate scenarios (GPS deltas, timestamp freshness, semantic agreement, dHash).
  3. `test_kanglish_duplicate.py` & `test_multilingual_duplicate.py`: Verifies duplicate detection across Kannada, Kanglish, Hinglish, and English.
  4. `test_multiword_phrase_translation.py`: Validates longest-first multi-word Kannada phrase replacement.
  5. `test_officer_translated_only.py`: Confirms field officers never receive untranslated native script in queues.
  6. `test_e2e.py`: Executes 13-step comprehensive lifecycle test from registration to citizen verification.
  7. `test_civic_fixes_verification.py`: Validates all 11 system enhancements (password visibility toggles, citizen dashboard eager loading, department routing rules for roads/waste, Kanglish vs genuine English with Indian locations, session persistence on refresh, SLA duration & resolution status metrics, multimodal duplicate image rejection, officer dual translation cards, image verification result badges, separated repair images, and citizen verification UI synchronization).
  8. Production build validation (`npm run build`) passing with zero errors across all static and dynamic routes.

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
6. **`complaints`**: Core ticket table (`id`, `citizen_id`, `category_id`, `description`, `original_description`, `language`, `detected_language`, `audio_url`, `location_latitude`, `location_longitude`, `location_address`, `status`, `priority`, `assigned_officer_id`, `duplicate_of_complaint_id`, `impact_count`, `sla_deadline`, `sla_status`, `is_escalated`, `citizen_verified`, `citizen_feedback_rating`, `citizen_feedback_remarks`, `reopen_count`, `created_at`, `updated_at`). Serialized API representations dynamically append computed operational attributes: `image_verification_result`, `sla_duration_hours`, `sla_duration_str`, `time_remaining_str`, `resolution_sla_status` (*"Met SLA"* vs *"Breached SLA"*), and `is_breached`.
7. **`complaint_images`**: File storage metadata (`image_url`, `image_type` [Reporting/Resolution], `is_verified`, `confidence_score`). Strictly categorizes images into citizen intake evidence (`Reporting`) vs field officer proof of repair (`Resolution`).
8. **`complaint_status_history`**: Immutable audit logs tracking every status transition and actor.
9. **`ai_predictions`**: NLP classification results, confidence scores, and translation latencies.
10. **`complaint_evidence_checks`**: Multimodal composite trust scores, GPS distance offsets, vision agreement metrics, semantic status (`MATCH`, `MISMATCH`, `PARTIAL`), and standardized `image_verification_result` strings.
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

### SLA Countdown Progression & Resolution Evaluation
```
[0% Elapsed] ─────────────── [75% Warning Trigger] ─────────────── [100% SLA Breach] ───> AUTO-ESCALATED
  (Normal)                      (Alert Sent)                           (Breached)

Final Ticket Resolution:
• Resolved before SLA Deadline ───> resolution_sla_status: "Met SLA"
• Resolved after SLA Deadline  ───> resolution_sla_status: "Breached SLA"
```

---

## 9. API Reference & Endpoint Catalog

### Authentication & Users (`/api/v1/auth`)
* `POST /api/v1/auth/register` — Citizen account registration and password hashing. Supports interactive password visibility toggles (`Eye`/`EyeOff`).
* `POST /api/v1/auth/login` — OAuth2 JWT token login for Citizen, Officer, and Admin. Backed by client dual-storage session persistence (`localStorage` + `sessionStorage`) with `tokenStorage.ensureSession()`.
* `GET /api/v1/auth/me` — Retrieve active authenticated user profile.
* `PUT /api/v1/auth/profile` — Update user profile details.

### Complaints Engine (`/api/v1/complaints`)
* `POST /api/v1/complaints` — Submit multimodal complaint (Form text, audio URL, image upload, live coordinates, GPS accuracy radius). Executes image upload and evidence verification *before* duplicate evaluation to reject mismatched evidence from duplicate linking.
* `GET /api/v1/complaints` — High-performance complaint retrieval with SQLAlchemy eager loading (`joinedload` and `selectinload`), eliminating N+1 bottlenecks. Returns `image_verification_result`, `sla_duration_str`, `time_remaining_str`, `resolution_sla_status`, and `is_breached`. (Role-filtered: Citizen sees own, Officer sees assigned queue, Admin sees all).
* `GET /api/v1/complaints/{id}` — Get full complaint details with AI inference, dual original/translated text, separated citizen reporting vs officer repair verification images, SLA status, and status history.
* `GET /api/v1/complaints/{id}/evidence` — Retrieve multimodal evidence trust analysis and 4-gate verification diagnostic report with explicit `image_verification_result` (*"Image matches complaint"* vs *"Image does not match complaint"*).
* `GET /api/v1/complaints/departments-categories` — Public listing of the 4 civic departments and 47 categories.
* `GET /api/v1/complaints/nearby` — Fetch nearby geotagged complaints within radius (decoupled from dashboard load for responsive UI).
* `POST /api/v1/complaints/preview-ai` — Real-time AI preview of category, priority, and translation before submission.
* `POST /api/v1/complaints/check-duplicate` — Proximity (100m) and translated-text semantic duplicate check with image mismatch guard.
* `PUT /api/v1/complaints/{id}/status` — Officer status transition (`Accepted`, `In Progress`).
* `POST /api/v1/complaints/{id}/resolve` — Officer resolution proof submission (mandatory after-photo and notes, categorizing image as `Resolution`).
* `POST /api/v1/complaints/{id}/verify-resolution` — Citizen approve (1–5 star rating -> `Closed`) or reject (`Reopened`) loop with immediate client-side state synchronization.

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

# 7. 11-Fix Comprehensive Verification Suite
python backend/test_civic_fixes_verification.py
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

### Core Infrastructure & AI Baseline
1. **Neon Serverless PostgreSQL Migration**:
   - Transitioned from local instances to Neon serverless cloud PostgreSQL with SSL enforcement (`sslmode=require`).
   - Integrated production connection pooling (`pool_pre_ping=True`, `pool_recycle=300`, `pool_size=10`, `max_overflow=20`) and 3-attempt exponential startup retry backoff in FastAPI to handle cloud cold starts gracefully.
2. **Translated-Text Embedding for Spatial Duplicate Detection**:
   - Fixed duplicate detection in `backend/app/services/duplicate.py` to generate SentenceTransformer embeddings strictly on translated English text rather than untranslated native descriptions, ensuring accurate duplicate clustering across Kannada, Kanglish, Hinglish, and English submissions.
3. **Kanglish & Indic Language Detection Guard**:
   - Overrode `langdetect` false-positive English classifications on Romanized Indic words, guaranteeing translation before classification or duplicate matching.
4. **Longest-First Multi-Word Kannada Phrase Fallback**:
   - Solved single-token dictionary matching limitations by matching longest multi-word phrases (e.g. `"ಬೀದಿ ದೀಪ"`, `"ರಸ್ತೆ ಹಾಳಾಗಿದೆ"`) first, followed by clean removal of residual unmapped script.
5. **1:1 Taxonomy & Database Category Parity**:
   - Aligned all 47 categories between `backend/app/services/ai.py` (`CATEGORY_HIERARCHY`) and `backend/app/seed.py` (`complaint_categories`), resolving category drift.
6. **Compulsory Photographic Evidence & Address Context**:
   - Enforced mandatory image upload in frontend UI validation and backend FastAPI verification. Submissions without image evidence are rejected at API entry.
   - Added editable street address / landmark input alongside live device GPS coordinates and interactive Leaflet map pin.
7. **Explainable Hybrid Priority Scoring**:
   - Implemented an explainable 5-factor weighted formula: $35\%$ Category Baseline Risk + $25\%$ Emergency Hazard Signals + $20\%$ Citizen Impact / Duplicate Count + $10\%$ Situation Context + $10\%$ AI / Evidence Confidence.

### 11 Platform Fixes & Operational Enhancements
8. **Password Visibility Toggle**:
   - Integrated interactive `Eye` / `EyeOff` toggles for password and confirm-password fields in `/login` and `/register`. Allows citizens and field officers to verify their passwords dynamically, preventing typing errors.
9. **Citizen Dashboard Performance Optimization**:
   - Eliminated dashboard loading freezes by decoupling initial complaint retrieval from heavy nearby geolocation queries.
   - Optimized backend database query in `get_complaints` using SQLAlchemy eager loading (`joinedload` on `category`, `category.department`, `assigned_officer`, `user` and `selectinload` on `images`), eliminating N+1 queries and speeding up initial render.
10. **Deterministic Department Routing (MG Road Potholes & Waste Rules)**:
    - Fixed classification logic in `backend/app/services/ai.py` (`classify_complaint`):
      - Potholes, road damage, and crater reports (e.g., *"There are dangerous potholes on MG Road in Bengaluru"*) deterministically route to BBMP `Potholes & Damaged Roads`, regardless of location keywords.
      - Garbage dumps, trash piles, and uncollected waste route deterministically to BSWML (`Door-to-Door Garbage Not Collected` or `Illegal Roadside Waste Dumping`).
      - Water leaks, pipe bursts, and sewage overflows route to BWSSB.
      - Streetlights route to BBMP, while high-voltage power lines and sparking transformers route to BESCOM.
11. **Kanglish vs. Genuine English Detection Fix**:
    - Refined `is_kanglish_or_indic_text` using regex word boundaries (`\b[a-zA-Z]+\b`) and cleaned marker dictionary.
    - Prevents genuine English text containing Indian location names (e.g., "MG Road", "Indiranagar", "Koramangala", "Bengaluru") from being falsely classified as Kanglish or mangled, keeping detected language as `en`.
12. **Dual-Storage Session Persistence on Refresh**:
    - Implemented dual-storage fallback (`localStorage` + `sessionStorage`) with `tokenStorage.ensureSession(expectedRole)` in `frontend/src/lib/api.ts`.
    - Prevents premature logout redirects and maintains authentication state when users refresh their browser on Citizen and Officer dashboards.
13. **SLA Duration, Time Remaining & Resolution Status**:
    - Enhanced `get_sla_summary` in `backend/app/services/sla.py` and complaint schemas to calculate:
      - `sla_duration_hours` (e.g. 12, 24, 48, 72)
      - `sla_duration_str` (e.g. "12h (Critical)")
      - `time_remaining_str` (e.g. "18h 24m remaining" or "Overdue by 3h 15m")
      - `resolution_sla_status`: Evaluates whether resolution met the service charter (*"Met SLA"* vs *"Breached SLA"*)
      - `is_breached`: Boolean flag powering red breach badges on ticket cards and headers.
14. **Multimodal Duplicate Detection Guard (Image Mismatch Rejection)**:
    - In `backend/app/services/duplicate.py` and `backend/app/routers/complaints.py`:
    - Moved image upload and evidence analysis to execute *before* duplicate detection.
    - If the complaint image fails semantic verification (`image_semantic_status == "MISMATCH"`), the complaint is strictly rejected from linking as a duplicate of an existing ticket.
15. **Officer Dashboard Dual Translation Display**:
    - Replaced single description display in `frontend/src/app/officer/dashboard/page.tsx` with dual clearly-labeled cards:
      - **Original Complaint**: Verbatim raw citizen report in original script/Kanglish with embedded audio recording player.
      - **English Translation**: AI-normalized English translation for immediate operational dispatch without language confusion.
16. **Standardized Image-Complaint Verification Badges**:
    - Exposed `image_verification_result` in `backend/app/schemas/complaint.py` and complaint serialization:
      - `"Image matches complaint"` for confirmed semantic alignment (`MATCH`).
      - `"Image does not match complaint"` for cross-category mismatches (`MISMATCH`).
      - `"Image partially matches complaint"` for borderline or unconfirmed imagery (`PARTIAL`).
    - Rendered prominently on Citizen and Officer complaint cards and evidence audit modals.
17. **Officer Repair Verification Image Separation**:
    - Separated image views in the Officer Dashboard:
      - **Citizen Evidence (Original)**: Uploaded at complaint filing (`image_type == "Reporting"`).
      - **Officer Repair Verification (Completed)**: Uploaded by field crew upon fix completion (`image_type == "Resolution"`).
18. **Citizen Resolution Verification UI Synchronization**:
    - In `frontend/src/app/citizen/dashboard/page.tsx`, submitting resolution verification (approve or reject) immediately updates local component state without requiring a page reload.
    - Automatically hides the "Verify Resolution" action button once completed (`citizen_verified == true`), displaying permanent feedback confirmation and preventing duplicate actions.

---

## 🏁 Summary
The **Karnataka AI-Powered Civic Grievance Platform** successfully satisfies all requirements across all 17 phases of the development blueprint. The system combines verified citizen accessibility with state-of-the-art AI intelligence, robust operational workflows, and predictive analytics.
