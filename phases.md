# 🌳 CivicAI Karnataka — Project Phases Architecture & Execution Flowcharts

This document decomposes the complete **Karnataka AI-Powered Civic Grievance Platform** into **17 sequential and modular phases**. It provides:
1. **Master Project Phases Tree Flowchart** illustrating inter-phase relationships and data flow.
2. **Individual Phase Deep Dives**, each featuring a **dedicated internal logic flowchart**, **how it works (short operational description)**, **key files & technologies**, and **inputs/outputs**.

---

## 🗺️ Master Project Phases Tree Flowchart

```mermaid
flowchart TD
    subgraph Foundation ["🏗️ FOUNDATION & CORE SETUP"]
        P1["Phase 1: Requirements & Domain Modeling"]
        P2["Phase 2: Modular Architecture & Skeleton"]
        P3["Phase 3: Database & RBAC Auth (JWT)"]
        P4["Phase 4: Karnataka Geography & Civic Agencies"]
        
        P1 --> P2
        P2 --> P3
        P3 --> P4
    end

    subgraph Intake ["📥 CITIZEN INTAKE & INGESTION"]
        P5["Phase 5: Multimodal Complaint Collection"]
        P6["Phase 6: Preprocessing & Translation Pipeline"]
        
        P4 --> P5
        P5 --> P6
    end

    subgraph AIIntelligence ["🧠 MULTIMODAL AI INTELLIGENCE LAYER"]
        P7["Phase 7: NLP Classification & Priority"]
        P8["Phase 8: Computer Vision (YOLOv8)"]
        P9["Phase 9: Multimodal Evidence Trust Scoring"]
        P10["Phase 10: Spatial & Semantic Duplicate AI"]
        
        P6 --> P7
        P5 --> P8
        P7 --> P9
        P8 --> P9
        P9 --> P10
    end

    subgraph Operations ["⚙️ SMART ROUTING & FIELD OPERATIONS"]
        P11["Phase 11: Karnataka Smart Agency Routing"]
        P12["Phase 12: Field Officer Operational Workflow"]
        P13["Phase 13: Citizen Verification & Reopen Loop"]
        P14["Phase 14: SLA Tracking & Escalation Engine"]
        
        P10 --> P11
        P11 --> P12
        P12 --> P13
        P11 --> P14
        P12 --> P14
        P13 -->|Reopened| P12
    end

    subgraph Analytics ["📊 ANALYTICS, ML & DEPLOYMENT"]
        P15["Phase 15: GIS Mapping & Admin Analytics"]
        P16["Phase 16: Predictive ML Intelligence"]
        P17["Phase 17: Security Hardening & E2E Testing"]
        
        P12 --> P15
        P14 --> P15
        P15 --> P16
        P16 --> P17
    end

    classDef foundation fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;
    classDef intake fill:#0f172a,stroke:#06b6d4,stroke-width:2px,color:#f8fafc;
    classDef ai fill:#1e1b4b,stroke:#8b5cf6,stroke-width:2px,color:#f8fafc;
    classDef ops fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#f8fafc;
    classDef analytics fill:#312e81,stroke:#ec4899,stroke-width:2px,color:#f8fafc;

    class P1,P2,P3,P4 foundation;
    class P5,P6 intake;
    class P7,P8,P9,P10 ai;
    class P11,P12,P13,P14 ops;
    class P15,P16,P17 analytics;
```

---

## 🔍 Phase-by-Phase Breakdown & Internal Tree Flowcharts

---

### Phase 1: Requirements, Domain Modeling & Specifications

#### Flowchart
```mermaid
flowchart LR
    A["Civic Problem Analysis"] --> B["Identify Key Actors\n(Citizen, Officer, Admin)"]
    B --> C["Define 20 Standard\nCivic Categories"]
    C --> D["Map Karnataka Agencies\n(BBMP, BWSSB, BESCOM, etc.)"]
    D --> E["Establish Complaint Lifecycle\n(Registered ➔ Resolved ➔ Closed)"]
```

#### How It Works (Short Description)
* Establishes the municipal boundaries, roles, and grievance classifications for Bengaluru and Karnataka.
* Identifies 3 primary roles (**Citizen**, **Field Officer**, **System Admin**) and establishes 20 canonical civic categories across civic services (potholes, garbage, sewage, power lines, metro tracks, traffic).
* Specifies the full ticket lifecycle state machine and data retention requirements.
* **Key Files / Specs**: Domain rules in `PROJECT_DOCUMENTATION.md` & `backend/app/models/`.

---

### Phase 2: System Architecture & Modular Codebase Skeleton

#### Flowchart
```mermaid
flowchart TD
    Client["Next.js 16 Client Portal\n(App Router + Tailwind)"] 
    API["FastAPI Asynchronous Gateway\n(ASGI + CORS + Router Specs)"]
    Storage["Storage & Engine Mounts\n(Static Uploads + Model Weights)"]
    
    Client <-->|REST API / JSON| API
    API --> Storage
```

#### How It Works (Short Description)
* Constructs a clean separation between the frontend single-page web app and the asynchronous backend API.
* Sets up CORS policies, environment configurations (`config.py`), central routing `/api/v1`, static media upload folders, and global error handling middleware.
* **Key Files**: `backend/app/main.py`, `backend/app/core/config.py`, `frontend/package.json`.

---

### Phase 3: Database, Users & Role-Based Access Control (RBAC)

#### Flowchart
```mermaid
flowchart TD
    User["User Registration / Login"] --> Auth["Auth Router\n(/api/v1/auth)"]
    Auth --> Hash["Bcrypt Password Hashing\n& Verification"]
    Hash --> JWT["Generate Signed\nJWT Bearer Token"]
    JWT --> Guards["FastAPI Role Dependencies\n(get_current_active_user)"]
    Guards --> DB[(PostgreSQL Database\nusers, roles, officers)]
```

#### How It Works (Short Description)
* Implements relational schema management using SQLAlchemy 2.0 with PostgreSQL.
* Secures citizen and officer identity with Bcrypt password hashing and OAuth2 JWT tokens.
* Enforces role-based permissions: Citizens can only access their own filings, Officers access assigned field cases, and Admins oversee city-wide operations.
* **Key Files**: `backend/app/models/user.py`, `backend/app/routers/auth.py`, `backend/app/core/security.py`.

---

### Phase 4: Karnataka Geography & Civic Agency Master Model

#### Flowchart
```mermaid
flowchart TD
    Seed["Database Seeder\n(seed.py)"] --> Agencies["Initialize 4 State Agencies\n(BBMP, BESCOM, BWSSB, BSWML)"]
    Agencies --> Zones["Register 8 Bengaluru Zones\n(East, West, South, Mahadevapura, etc.)"]
    Zones --> Wards["Map 198 Wards & Categories"]
    Wards --> Staff["Seed Pre-assigned Department Officers"]
```

#### How It Works (Short Description)
* Seeds the spatial and departmental administrative hierarchy of Karnataka and Bengaluru.
* Binds grievance categories to responsible authorities (e.g. *Potholes & Roads* &rarr; **BBMP**, *Power & Outages* &rarr; **BESCOM**, *Water & Sewerage* &rarr; **BWSSB**, *Solid Waste Management* &rarr; **BSWML**).
* Populates initial test officers across all 8 civic zones for load testing.
* **Key Files**: `backend/app/seed.py`, `backend/app/models/department.py`.

---

### Phase 5: Citizen Multimodal Complaint Collection

#### Flowchart
```mermaid
flowchart TD
    Citizen["Citizen Input Screen"] --> Forms["Multimodal Form Inputs"]
    Forms --> Text["Text Description\n(Kannada / English / Hinglish)"]
    Forms --> Audio["Voice Audio Capture\n(MediaRecorder Web API)"]
    Forms --> GPS["Device GPS Geolocation\n+ Leaflet Map Pin"]
    Forms --> Photo["Camera / Photo Upload\n(EXIF Metadata Preservation)"]
    Text --> Payload["Multipart Form Submit\nPOST /api/v1/complaints"]
    Audio --> Payload
    GPS --> Payload
    Photo --> Payload
```

#### How It Works (Short Description)
* Provides a citizen-facing portal (`/report`) supporting text in multiple regional languages, audio voice recording, live GPS coordinate capture, and photographic evidence.
* Captures high-precision geolocation via browser Geolocation API and synchronizes with an interactive Leaflet map pin.
* **Key Files**: `frontend/src/app/report/page.tsx`, `backend/app/routers/complaints.py`.

---

### Phase 6: Preprocessing & Multilingual Translation Pipeline

#### Flowchart
```mermaid
flowchart TD
    Raw["Raw Input Data"] --> LangCheck{"Detect Language\n(Kannada / Hinglish / English)"}
    LangCheck -->|Kannada / Hinglish| Trans["Indic / Google Translate\nPipeline"]
    LangCheck -->|English| Clean["Text Sanitization & Normalization"]
    Trans --> Clean
    Clean --> Store["Store Dual Formats\n(original_description + normalized description)"]
    Store --> Next["Feed to NLP Classification"]
```

#### How It Works (Short Description)
* Normalizes multilingual inputs (Kannada, Hinglish, regional slang) into clean English text optimized for NLP models while preserving the citizen's original verbatim text.
* Stores voice audio recordings securely in static storage for officer review.
* **Key Files**: `backend/app/services/translation.py`.

---

### Phase 7: AI Classification & Priority Prediction Engine

#### Flowchart
```mermaid
flowchart TD
    Text["Normalized Description"] --> ST["SentenceTransformer Model\n(all-MiniLM-L6-v2)"]
    ST --> Embed["384-Dim Semantic Embedding Vector"]
    Embed --> Sim["Cosine Similarity Matrix against\n20 Category Class Anchors"]
    Sim --> TopClass["Predicted Complaint Category\n+ Confidence Score (0.0-1.0)"]
    
    Text --> Rules["Emergency Keywords Engine\n(spark, flood, accident, danger)"]
    TopClass --> Priority["Priority Determinant:\nCritical | High | Medium | Low"]
    Rules --> Priority
```

#### How It Works (Short Description)
* Uses SentenceTransformer (`all-MiniLM-L6-v2`) to produce 384-dimensional dense semantic embeddings of the complaint text.
* Classifies the text into one of 20 civic categories by calculating maximum cosine similarity against pre-computed category anchor vectors.
* Assesses severity using category risk weights and emergency keyword detection to assign priority: `Critical` (12h SLA), `High` (24h), `Medium` (48h), or `Low` (72h).
* **Key Files**: `backend/app/services/ai_classifier.py`.

---

### Phase 8: Structured Computer Vision & Image Quality Validation (YOLOv8 & OpenCV)

#### Flowchart
```mermaid
flowchart TD
    Img["Uploaded Evidence Image"] --> Pre["OpenCV Quality Evaluation\n(Blur, Luminance, Resolution)"]
    Pre -->|Laplacian var < 25.0| FlagBlur["Flag BLURRY"]
    Pre -->|Brightness < 25 or > 245| FlagExp["Flag EXPOSURE ISSUE"]
    Pre -->|Pass| PassQ["Quality: PASS"]
    
    Img --> YOLO["Ultralytics YOLOv8n\nNeural Network"]
    YOLO --> Detect["Object Detection & Bounding Boxes\n[x1, y1, x2, y2] + Confidences"]
    Detect --> Classes["Identify Civic Hazards\n(potholes, garbage piles, broken cables, poles)"]
    
    Img --> EXIF["PIL / piexif Metadata Parser"]
    EXIF --> EXIFData["Extract EXIF GPS (DMS)\n& Capture Timestamp (UTC)"]
    
    Classes --> Payload["Phase 8 Image Analysis Payload\n(detected_objects, bounding_boxes, quality_check, EXIF)"]
    PassQ --> Payload
    FlagBlur --> Payload
    FlagExp --> Payload
    EXIFData --> Payload
```

#### How It Works (Short Description)
* Ingests citizen-uploaded photos and runs real-time object detection using a lightweight YOLOv8 network (`yolov8n.pt`).
* Extracts structured detection payloads including categorized object classes, bounding boxes (`[x1, y1, x2, y2]`), and per-class confidence scores.
* Executes automated **OpenCV image quality diagnostics**:
  1. **Blurriness**: Evaluates Laplacian variance ($\text{var} < 25.0 \implies \text{BLURRY}$).
  2. **Exposure / Contrast**: Flags underexposed ($< 25$) or overexposed ($> 245$) whiteout images.
  3. **Resolution**: Enforces minimum dimensional sanity ($100 \times 100\text{ px}$).
* Uses PIL and `piexif` to extract embedded GPS coordinates and capture timestamps across standard EXIF and modern IFD sub-tables.
* **Key Files**: `backend/app/services/evidence.py`, `yolov8n.pt`.

---

### Phase 9: Hard-Gate Multimodal Evidence Verification & Trust Scoring Engine

#### Flowchart
```mermaid
flowchart TD
    subgraph Gate1 ["GATE 1: GEOLOCATION VALIDATION"]
        LiveGPS["Live Device GPS\n(± Accuracy Radius)"] <--> EXIFGPS["Photo EXIF GPS"]
        LiveGPS -->|Haversine <= 500m| GeoMatch["MATCH (+35 pts)"]
        LiveGPS -->|Haversine >= 5000m| GeoCritical["SEVERE MISMATCH\n(SUSPICIOUS)"]
        LiveGPS -->|No EXIF GPS| GeoMissing["EXIF_MISSING\n(Partial Credit: +25 pts)"]
    end

    subgraph Gate2 ["GATE 2: TIMESTAMP FRESHNESS"]
        ServerTime["Server Receipt (UTC)"] <--> PhotoTime["Photo EXIF Timestamp"]
        ServerTime -->|Age <= 72h| Fresh["FRESH (+20 pts)"]
        ServerTime -->|Age > 72h| Stale["STALE\n(MANUAL_REVIEW)"]
        ServerTime -->|Future > 10m| Future["FUTURE ANOMALY\n(MANUAL_REVIEW)"]
    end

    subgraph Gate3 ["GATE 3: SEMANTIC ALIGNMENT"]
        NLPDesc["Complaint Category & Description"] <--> YOLOFeat["YOLO Objects & Image Context"]
        NLPDesc -->|Category Matches Visuals| SemMatch["MATCH (+45 pts)"]
        NLPDesc -->|Cross-Category Mismatch\ne.g. Pothole vs Garbage| SemMismatch["HARD MISMATCH\n(REJECTED)"]
    end

    subgraph Gate4 ["GATE 4: REUSED IMAGE DETECTION"]
        CurImg["Current Photo dHash"] <--> PrevImgs["Database Complaint Images"]
        CurImg -->|Hamming Distance <= 4| Reused["REUSED IMAGE\n(SUSPICIOUS)"]
    end

    Gate1 --> DecisionEngine{"Hard-Gate Decision Engine"}
    Gate2 --> DecisionEngine
    Gate3 --> DecisionEngine
    Gate4 --> DecisionEngine

    DecisionEngine -->|All Gates Pass| DecVerified["VERIFIED"]
    DecisionEngine -->|Minor Quality / Missing EXIF| DecPartial["PARTIALLY_VERIFIED"]
    DecisionEngine -->|Stale / Future / Borderline| DecReview["MANUAL_REVIEW"]
    DecisionEngine -->|Severe Distance / Reused Photo| DecSuspicious["SUSPICIOUS"]
    DecisionEngine -->|Semantic Mismatch / Indoor Device| DecRejected["REJECTED"]

    DecisionEngine --> CalcScore["Weighted Trust Score (0 - 100%)\nGPS (35%) + Time (20%) + Semantic (45%)"]
    CalcScore --> Audit["GET /api/v1/complaints/{id}/evidence\nAudit Trail & Officer Dashboard"]
```

#### How It Works (Short Description)
* Enforces server-side authority with **4 Hard Verification Gates** to prevent spoofed, fraudulent, or recycled submissions:
  1. **Gate 1 (Geospatial Cross-Validation)**: Calculates Haversine distance between reported live device GPS and photo EXIF coordinates. Distance $\le 500\text{m}$ confirms `MATCH`. Distance $\ge 5000\text{m}$ triggers `SUSPICIOUS`. Missing EXIF gracefully falls back to `EXIF_MISSING`.
  2. **Gate 2 (Timestamp Freshness)**: Ensures photo was taken within 72 hours (`FRESH`). Photos $> 72\text{h}$ are flagged `STALE`, and future timestamps ($> 10\text{m}$) are flagged `FUTURE` $\to$ `MANUAL_REVIEW`.
  3. **Gate 3 (Semantic Agreement)**: Cross-checks complaint text and category against image features using `all-MiniLM-L6-v2` SentenceTransformers and YOLO indicators. Strict negative filters detect cross-category mismatches (e.g. Pothole complaint with Garbage photo). **Critical rule: Semantic mismatches are barred from ever receiving `VERIFIED` status and are routed to `REJECTED`**.
  4. **Gate 4 (Reused Image Detection)**: Computes a 64-bit difference perceptual hash (`dHash`). Bitwise Hamming distance $\le 4$ flags duplicate or re-submitted images across complaints, setting `is_reused_image = True` $\to$ `SUSPICIOUS`.
* **Decision States**: `VERIFIED`, `PARTIALLY_VERIFIED`, `MANUAL_REVIEW`, `SUSPICIOUS`, `REJECTED`.
* **Composite Trust Score (0–100%)**: Weighted composition: GPS ($35\%$), Timestamp ($20\%$), Semantic Vision ($45\%$). Clamped to $\le 24\%$ if `REJECTED` and $\le 35\%$ if `SUSPICIOUS`.
* **Audit API Endpoint**: `GET /api/v1/complaints/{id}/evidence` returns complete gate telemetry and explainable audit logs.
* **Key Files**: `backend/app/services/evidence.py`, `backend/test_evidence_gates.py`.

---

### Phase 10: Spatial & Semantic Duplicate Detection Engine

#### Flowchart
```mermaid
flowchart TD
    New["New Incoming Complaint"] --> Active["Query Active Tickets in Category"]
    Active --> Radius["Haversine Proximity Filter\n(Distance within 100m)"]
    Radius -->|Within 100m| VectorSim["Compute SentenceTransformer\nCosine Similarity"]
    Radius -->|Outside 100m| Unique["Mark as Unique Ticket"]
    
    VectorSim --> Check{"Similarity >= 0.85?"}
    Check -->|Yes| Merge["Link as Child Duplicate to Parent Ticket\n(Increment Upvote / Impact Count)"]
    Check -->|No| Unique
```

#### How It Works (Short Description)
* Eliminates redundant work orders for the same incident (e.g. 50 citizens reporting the same water burst or pothole).
* Applies a dual-gate screening algorithm:
  1. **Geospatial Proximity**: Filters active grievances within a 100-meter radius using the Haversine formula.
  2. **Semantic Similarity**: Computes cosine similarity of SentenceTransformer embeddings.
* If similarity score &ge; 0.85, associates the new report as a child duplicate of the master ticket, avoiding duplicate dispatches.
* **Key Files**: `backend/app/services/duplicate.py`.

---

### Phase 11: Karnataka Smart Routing Engine

#### Flowchart
```mermaid
flowchart TD
    Ticket["Verified Unique Complaint"] --> Agency["Map Category ➔ Karnataka Agency\n(BBMP / BWSSB / BESCOM / etc.)"]
    Agency --> Zone["Identify Civic Zone\n(e.g., Mahadevapura / South)"]
    Zone --> Officers["Fetch Active On-Duty Officers in Zone"]
    Officers --> LoadCalc["Calculate Active Caseload per Officer"]
    LoadCalc --> Min["Select Officer with Minimum Active Load\narg min(ActiveComplaints)"]
    Min --> Dispatch["Assign Ticket, Set Status = Registered\nSend Notification Alert"]
```

#### How It Works (Short Description)
* Eliminates manual dispatch delays through automated least-active load balancing.
* Identifies the responsible agency and geographical zone based on category and GPS coordinates.
* Assigns the case to the on-duty field officer with the lowest active caseload.
* Creates audit trail records in `complaint_status_history` and dispatches in-app notifications.
* **Key Files**: `backend/app/services/routing.py`.

---

### Phase 12: Field Officer Operational Workflow

#### Flowchart
```mermaid
flowchart TD
    Reg["Status: Registered\n(Officer Receives Notification)"] --> Accept["Officer Clicks 'Accept Case'\nStatus ➔ Accepted"]
    Accept --> Prog["Field Crew Dispatched\nStatus ➔ In Progress"]
    Prog --> Fix["Remediation Work Executed on Site"]
    Fix --> Proof["Officer Uploads 'After' Photo Proof\n+ Descriptive Remediation Notes"]
    Proof --> Resolved["Status ➔ Resolved\n(SLA Countdown Paused)"]
```

#### How It Works (Short Description)
* Provides a mobile-responsive dashboard for field officers (`/officer/dashboard`).
* Enforces an immutable progression sequence: `Registered` &rarr; `Accepted` &rarr; `In Progress` &rarr; `Resolved`.
* Strict resolution policy requires uploading photographic proof of resolution and entering remediation notes before a case can be marked resolved.
* **Key Files**: `frontend/src/app/officer/dashboard/page.tsx`, `backend/app/routers/complaints.py`.

---

### Phase 13: Citizen Verification & Reopen Feedback Loop

#### Flowchart
```mermaid
flowchart TD
    Res["Ticket Marked 'Resolved' by Officer"] --> Notify["Citizen Receives Review Prompt"]
    Notify --> Inspect["Citizen Inspects Resolution Proof Photo"]
    Inspect --> Decision{"Does Citizen Confirm Fix?"}
    
    Decision -->|Yes - Approved| Close["Status ➔ Closed\nSubmit 1-5 Star Rating & Feedback"]
    Decision -->|No - Rejected| Reopen["Status ➔ Reopened\nIncrement reopen_count"]
    Reopen --> Escalate["Trigger Urgent Officer Re-Dispatch\nAlert Department Supervisor"]
```

#### How It Works (Short Description)
* Places final verification authority in the hands of the reporting citizen.
* Citizens view the "Before" vs "After" photos on their dashboard.
* **Approved**: Ticket status becomes `Closed`, citizen submits a 1–5 star rating and optional comments.
* **Rejected**: Ticket status returns to `Reopened`, increments `reopen_count`, and triggers an urgent re-dispatch alert to the officer.
* **Key Files**: `frontend/src/app/citizen/dashboard/page.tsx`, `backend/app/routers/complaints.py`.

---

### Phase 14: SLA Tracking, Warning Timers & Escalation Engine

#### Flowchart
```mermaid
flowchart TD
    Clock["Live Time Monitoring Daemon\n(Periodic SLA Check)"] --> Calc["Calculate Elapsed Time vs SLA Deadline\n(Critical: 12h | High: 24h | Med: 48h | Low: 72h)"]
    Calc --> StateCheck{"Elapsed SLA Percentage"}
    
    StateCheck -->|0% to 75%| Norm["SLA Status: Normal"]
    StateCheck -->|75% to 100%| Warn["SLA Status: Warning\nSend Proactive Alert to Officer"]
    StateCheck -->|Over 100% Unresolved| Breach["SLA Status: Breached\nSet is_escalated = True"]
    
    Breach --> Escalation["Auto-Escalate to Departmental Supervisor\nFlag in Admin Hotlist"]
```

#### How It Works (Short Description)
* Automatically enforces citizen service charters based on grievance priority:
  * **Critical**: 12 hours
  * **High**: 24 hours
  * **Medium**: 48 hours
  * **Low**: 72 hours
* Dynamically shifts SLA status: `Normal` (&le; 75%) &rarr; `Warning` (75%–100%) &rarr; `Breached` (> 100%).
* Automatically flags overdue tickets (`is_escalated = True`) and notifies agency supervisors.
* **Key Files**: `backend/app/services/sla.py`.

---

### Phase 15: GIS Mapping & Operational Analytics Dashboard

#### Flowchart
```mermaid
flowchart TD
    DB[(Active Complaints & History)] --> Aggr["Spatial & Temporal Aggregations\n(/api/v1/dashboard/admin)"]
    Aggr --> Map["Interactive Leaflet Map\n(Color-Coded Status Pins & Clusters)"]
    Aggr --> Metrics["Executive KPI Cards\n(Resolution Rate, SLA Compliance %)"]
    Aggr --> Heatmap["Ward & Zone Density Breakdown"]
    Aggr --> Velocity["Department Caseload & Velocity Charts"]
```

#### How It Works (Short Description)
* Centralized command-and-control center for state and municipal administrators (`/admin/dashboard`).
* Renders real-time geospatial pin clusters, ward-level complaint distribution, agency resolution velocity, and SLA compliance metrics.
* Enables filtering by agency, zone, status, priority, and date range.
* **Key Files**: `frontend/src/app/admin/dashboard/page.tsx`, `backend/app/routers/dashboard.py`.

---

### Phase 16: Predictive Machine Learning Intelligence & Early Warning

#### Flowchart
```mermaid
flowchart TD
    History["128,573 Historical BBMP Records\n(Janahita Dataset)"] --> Train["Offline Scikit-Learn Training\n(RandomForest Models)"]
    Train --> Models["Exported ML Model Artifacts\n(sla_breach_model.joblib, duration_model.joblib)"]
    
    Models --> API["Predictive API Router\n(/api/v1/predictive)"]
    API --> F1["1. SLA Breach Risk Classifier\n(84.4% Accuracy, 0.922 ROC-AUC)"]
    API --> F2["2. Resolution Duration Regressor\n(MAE ±12.75 Hours)"]
    API --> F3["3. 8-Zone Spatial Risk Forecaster\n(+Monsoon Seasonal Multipliers)"]
    API --> F4["4. 14-Day Grievance Intake Time-Series"]
```

#### How It Works (Short Description)
* Adds predictive intelligence trained on **128,573 historical municipal records**.
* **SLA Breach Risk Predictor**: Evaluates category, zone, priority, and current backlog to estimate breach probability.
* **Resolution Duration Regressor**: Forecasts expected hours to resolve (MAE $\pm 12.75$ hours).
* **Spatial Risk Forecaster**: Ranks all 8 Bengaluru zones using seasonal monsoon multipliers (+35% to +45% during peak monsoon).
* **14-Day Intake Forecasting**: Projects future grievance volumes per department for proactive crew staffing.
* **Key Files**: `backend/app/services/predictive.py`, `backend/app/routers/predictive.py`.

---

### Phase 17: Security Hardening, Automated E2E Testing & Deployment

#### Flowchart
```mermaid
flowchart TD
    Suite["Automated E2E Test Suite\n(backend/test_e2e.py)"] --> T1["1. User & Officer Auth"]
    T1 --> T2["2. Multimodal Submission"]
    T2 --> T3["3. AI Classification & YOLO"]
    T3 --> T4["4. Trust Scoring & Duplicate AI"]
    T4 --> T5["5. Smart Routing & Assignment"]
    T5 --> T6["6. Officer Proof & Resolution"]
    T6 --> T7["7. Citizen Verification Loop"]
    T7 --> T8["8. SLA Breach & Escalation"]
    T8 --> T9["9. Phase 16 ML Predictive Endpoints"]
    T9 --> Build["Frontend Production Build Check\n(npm run build)"]
    Build --> Complete["System Verified: 100% Pass Rate\nProduction Ready"]
```

#### How It Works (Short Description)
* Verifies end-to-end platform integrity with an automated 13-step test suite covering the entire grievance lifecycle.
* Confirms zero regressions in ML inference, routing logic, SLA triggers, and Next.js frontend builds.
* **Key Files**: `backend/test_e2e.py`, `TESTING_GUIDE.md`.

---

## 📊 Summary Matrix: All 17 Phases at a Glance

| Phase # | Phase Name | Primary Technology / Tools | Key Input | Key Output |
|:---:|---|---|---|---|
| **1** | Requirements & Domain | Specification Specs | Civic Problems | 20 Categories, Roles, State Rules |
| **2** | System Architecture | FastAPI, Next.js 16 | System Scope | Modular skeleton, CORS, Routing |
| **3** | Database & RBAC | PostgreSQL, SQLAlchemy, JWT | User credentials | JWT tokens, Role guards, Tables |
| **4** | Karnataka Geography | Python Seeder | Civic structure | 5 Agencies, 8 Zones, 198 Wards |
| **5** | Multimodal Intake | React 19, Leaflet, MediaAPI | Citizen submission | Multi-part form payload |
| **6** | Translation & Clean | Indic / Google Translate | Raw KN/EN text | Normalized English text + Audio |
| **7** | NLP & Priority AI | SentenceTransformers (`all-MiniLM-L6-v2`) | Clean text | Category & Priority (`Critical` to `Low`) |
| **8** | YOLOv8 Computer Vision| Ultralytics YOLOv8n | Evidence photo | Detected objects & Bounding boxes |
| **9** | Evidence Trust Scoring | Haversine + EXIF + Agreement | GPS, Photo, Text | Composite Trust (0–100%) & Rating |
| **10** | Duplicate AI | Haversine + Cosine Sim | New complaint | Unique ticket OR Linked duplicate |
| **11** | Smart Agency Routing | Least-Load Balancing | Verified ticket | Dispatched officer & Status update |
| **12** | Officer Operations | Next.js Dashboard, REST | Assigned case | Proof photo & Status = `Resolved` |
| **13** | Citizen Verification | Next.js Dashboard, Rating | Resolution proof | `Closed` (Rating) OR `Reopened` |
| **14** | SLA Escalation | Periodic Daemon | Active timers | `Normal` &rarr; `Warning` &rarr; `Breached` |
| **15** | GIS Analytics | Leaflet, React, ChartJS | Ticket telemetry | Spatial pins, Hotspot heatmaps |
| **16** | Predictive ML | Scikit-Learn RandomForest | 128k records | SLA risk, Duration, 14-day forecasts |
| **17** | E2E Testing & Hardening| Python Unittest, Next Build | Full codebase | 100% test pass rate, Production build |
