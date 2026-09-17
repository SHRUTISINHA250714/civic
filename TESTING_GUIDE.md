# 🧪 Karnataka AI-Powered Civic Grievance Platform
### *Complete End-to-End Testing Manual & Role-by-Role Verification Guide*

---

## 📑 Table of Contents
1. [Prerequisites & Running Services](#1-prerequisites--running-services)
2. [Master Credentials Matrix](#2-master-credentials-matrix)
3. [Test Track 1: Citizen Workflow & Multimodal Intake](#3-test-track-1-citizen-workflow--multimodal-intake)
4. [Test Track 2: Field Officer Operations & Resolution Proof](#4-test-track-2-field-officer-operations--resolution-proof)
5. [Test Track 3: Citizen Verification & Reopen Feedback Loop](#5-test-track-3-citizen-verification--reopen-feedback-loop)
6. [Test Track 4: Executive Administrator, GIS & Phase 16 ML Analytics](#6-test-track-4-executive-administrator-gis--phase-16-ml-analytics)
7. [Test Track 5: Multi-Department Testing Scenarios](#7-test-track-5-multi-department-testing-scenarios)
8. [Test Track 6: Automated End-to-End Terminal Suite](#8-test-track-6-automated-end-to-end-terminal-suite)
9. [Test Track 7: Interactive Swagger REST API Testing](#9-test-track-7-interactive-swagger-rest-api-testing)
10. [Test Track 8: Automated Hard-Gate Evidence Verification Suite](#10-test-track-8-automated-hard-gate-evidence-verification-suite)
11. [Edge Cases & Security Validation](#11-edge-cases--security-validation)

---

## 1. Prerequisites & Running Services

Before starting manual or automated tests, ensure the platform services are running:

| Component | Target URL | Startup Command (if not running) |
|---|---|---|
| **Frontend Web App** | **`http://localhost:3000`** | `cd frontend && npm run dev` |
| **Backend API Engine** | **`http://127.0.0.1:8000`** | `uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload` |
| **Swagger API Docs** | **`http://127.0.0.1:8000/docs`** | *Automatically available with backend* |

---

## 2. Master Credentials Matrix

All accounts are pre-seeded in the database and ready for immediate login:

| Role / Department | Full Name | Email | Password | Primary Dashboard |
|---|---|---|---|---|
| 👑 **System Administrator** | Karnataka Civic Admin | `admin@civicai.gov.in` | `adminpassword` | [`/admin/dashboard`](http://localhost:3000/admin/dashboard) |
| 🧑‍💼 **Citizen User** | Siddaramaiah K | `citizen@gmail.com` | `citizenpassword` | [`/citizen/dashboard`](http://localhost:3000/citizen/dashboard) |
| 🚧 **BBMP Officer** | Rajesh Kumar (BBMP) | `officer.bbmp@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| ⚡ **BESCOM Officer** | Manjunath Swamy (BESCOM) | `officer.bescom@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| 🚰 **BWSSB Officer** | Anil Gowda (BWSSB) | `officer.bwssb@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| 🗑️ **BSWML Officer** | Sunitha Murthy (BSWML) | `officer.bswml@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |

---

## 3. Test Track 1: Citizen Workflow & Multimodal Intake

### Scenario 1.1: Standard Kannada Multimodal Complaint Submission
1. Open your browser to **`http://localhost:3000/login`**.
2. Enter the Citizen credentials:
   * **Email**: `citizen@gmail.com`
   * **Password**: `citizenpassword`
3. Click **"Sign In"**. You will be directed to `/citizen/dashboard`.
4. In the **"Report Civic Issue"** form:
   * **Language**: Select **Kannada** from the dropdown.
   * **Description**: Enter the following sample Kannada text:
     ```text
     Rasteyalli kachada thumbide mattu dodda gundi ide near Indiranagar 100ft road. Heavy traffic hazard!
     ```
   * **Location**: Click any point on the interactive Leaflet map to drop a pin (or click *"Use Live GPS"*).
   * **Photo Evidence**: Click the upload area and select any sample `.jpg` or `.png` image.
5. Click **"Submit Grievance"**.

#### 🔍 What to Verify:
* ✅ **Zero-Drop Translation**: The backend translates the Kannada text into English while storing the original Kannada text.
* ✅ **AI Classification**: The AI classifies the issue as `Pothole` or `Garbage` and assigns it to **BBMP**.
* ✅ **AI Priority Engine**: Computes priority (`Medium` or `High`) and sets an SLA deadline.
* ✅ **Verification Gate Badge**: Displays the **Hard-Gate Decision Badge** (`VERIFIED`, `PARTIALLY_VERIFIED`, `MANUAL_REVIEW`, `SUSPICIOUS`, or `REJECTED`).
* ✅ **Evidence Trust Card**: Displays a **Composite Trust Score (0–100%)** broken down into GPS proximity (35%), timestamp recency (20%), and YOLOv8 semantic vision agreement (45%).
* ✅ **High-Accuracy GPS**: Client geolocation accuracy radius (`pos.coords.accuracy`) is sent to the backend and factored into Gate 1 location checks.
* ✅ **Tracking Timeline**: Complaint appears in the Citizen's active list under status **Registered**.

---

### Scenario 1.2: English Submission with Audio Voice Note
1. On the Citizen Dashboard, select **English** or **Voice Note**.
2. Click the **Microphone** icon to start browser voice recording, speak for 3–5 seconds, and click Stop.
3. Type: *"Severe water pipeline burst and flooding on 80 Feet Road Koramangala"*.
4. Select a location pin in Koramangala and submit.

#### 🔍 What to Verify:
* ✅ AI classifies category as `Water Leakage` and routes the case to **BWSSB**.
* ✅ Audio attachment URL is safely persisted and accessible in the complaint media list.

---

## 4. Test Track 2: Field Officer Operations & Resolution Proof

### Scenario 2.1: Officer Ticket Acceptance, Evidence Audit & Field Work
1. Log out (or open an Incognito browser window) and navigate to **`http://localhost:3000/login`**.
2. Sign in as the **BBMP Officer**:
   * **Email**: `officer.bbmp@civicai.gov.in`
   * **Password**: `officerpassword`
3. You will be redirected to the **Officer Dashboard** (`/officer/dashboard`).
4. Locate the newly filed complaint in your assigned queue:
   * **Inspect Evidence Audit Diagnostic Panel**: Click the evidence section to view:
     - **OpenCV Diagnostics**: Laplacian blur variance (threshold $\ge 25.0$), exposure brightness ($25 \le L \le 245$), and minimum resolution ($100 \times 100\text{px}$).
     - **Gate 1 (GPS)**: Client coordinates vs. EXIF coordinates distance delta ($\le 500\text{m}$).
     - **Gate 2 (Timestamp)**: Capture recency ($\le 72\text{h}$) and future clock skew rejection ($> 10\text{m}$).
     - **Gate 3 (Semantic)**: YOLOv8 detected objects and NLP cross-modal cosine similarity score against complaint text.
     - **Gate 4 (Reused dHash)**: 64-bit perceptual image hash verifying no duplicate recycled photo abuse across past tickets.
   * Click **"Accept"** &rarr; Verify status changes to **Accepted** and SLA timer starts counting.
   * Click **"Start Work"** &rarr; Verify status changes to **In Progress**.

---

### Scenario 2.2: Submitting Resolution Proof Photo
1. While the ticket is **In Progress**, click the green **"Submit Resolution Proof"** button.
2. In the modal:
   * **Resolution Remarks**: Enter:
     ```text
     Pothole excavated and patched with 40mm wet mix macadam concrete. Garbage dump cleared by BBMP solid waste team.
     ```
   * **Resolution Proof Image**: Upload an "After" resolution image.
3. Click **"Submit Proof & Mark Resolved"**.

#### 🔍 What to Verify:
* ✅ Status updates from `In Progress` &rarr; **Resolved**.
* ✅ Resolution image is tagged as `image_type: "Resolution"` in the database.
* ✅ Audit trail records the officer's action and timestamp in `complaint_status_history`.
* ✅ A notification is sent to the citizen alerting them to verify the work.

---

## 5. Test Track 3: Citizen Verification & Reopen Feedback Loop

### Scenario 3.1: Citizen Rejects Inadequate Fix (Reopen Flow)
1. Log back in as the citizen: `citizen@gmail.com` / `citizenpassword`.
2. Open the newly **Resolved** complaint card.
3. Notice the **Citizen Verification Banner** with two actions:
   * Green Button: *"Approve & Close"*
   * Amber Button: *"Reject & Reopen"*
4. Click **"Reject & Reopen"**.
5. Enter rejection feedback remarks:
   ```text
   The road patch is uneven and debris was left on the pedestrian sidewalk. Please clear it.
   ```
6. Submit.

#### 🔍 What to Verify:
* ✅ Ticket status immediately reverts from `Resolved` &rarr; **Reopened**.
* ✅ `reopen_count` increments from `0` &rarr; `1`.
* ✅ Officer receives an escalation alert to re-dispatch field crews.

---

### Scenario 3.2: Officer Re-resolves & Citizen Approves with 5 Stars
1. Log in as `officer.bbmp@civicai.gov.in`, open the reopened ticket, re-submit resolution proof notes (*"Debris cleared and surface leveled"*), and click **Resolve**.
2. Log back in as `citizen@gmail.com`.
3. Click **"Approve & Close"**.
4. Select a **5-Star Rating (★★★★★)** and enter praise remarks (*"Excellent and fast work!"*).
5. Submit.

#### 🔍 What to Verify:
* ✅ Status changes permanently to **Closed**.
* ✅ `citizen_verified` is set to `True` and `citizen_feedback_rating` is set to `5`.
* ✅ SLA timer stops, recording compliant closure.

---

## 6. Test Track 4: Executive Administrator, GIS & Phase 16 ML Analytics

1. Navigate to **`http://localhost:3000/login`**.
2. Sign in as the **System Administrator**:
   * **Email**: `admin@civicai.gov.in`
   * **Password**: `adminpassword`
3. You will land on the **Admin Dashboard** (`/admin/dashboard`).

---

### 🗺️ Tab 1: Operational Overview & GIS Hotspots
* **Executive KPI Cards**:
  * Total City Complaints, Pending vs. Closed Tickets, Reopened Ratio, and Overall SLA Compliance (%).
* **Department Workload Cards**:
  * Real-time active ticket distribution across *BBMP, BESCOM, BWSSB, and BSWML*.
* **Interactive GIS Map**:
  * Leaflet map displaying active complaints across Bengaluru with color-coded status pins and hotspot density rings.
* **Manual SLA Check**:
  * Click **"Run SLA Check Daemon"** to manually trigger warning/breach evaluations across all active complaints.

---

### 🧠 Tab 2: Phase 16 Predictive ML Intelligence & Early Warning
Click the **"Predictive Intelligence (Phase 16)"** tab at the top of the Admin Dashboard:

#### 1. Early Warning Telemetry Cards
* **SLA Breach Risk Model Accuracy**: `84.4%` (`0.922 ROC-AUC`).
* **Resolution Duration Regressor MAE**: `±12.75 Hours`.
* **Highest Risk Zone**: Real-time identification of the most vulnerable zone (e.g. *Bommanahalli* or *Mahadevapura* with risk score `98.0/100`).
* **14-Day City Forecast**: Projected grievance volume for the upcoming two weeks (e.g., `~3,052 grievances`).

#### 2. Interactive ML Risk & Resolution Duration Estimator
Test the real-time machine learning prediction simulator:
1. In the **"Simulate New Grievance Risk"** form:
   * **Category**: Select `Pothole` (or `Water Leakage`, `Power Outage`).
   * **Bengaluru Ward / Zone**: Select `Bommanahalli` (or `Mahadevapura`, `East`).
   * **Priority**: Select `Critical` or `High`.
2. Click **"Run ML Estimation"**.
3. **Observe Results**:
   * **Predicted SLA Breach Risk**: Displays exact percentage probability (e.g., `27.4%`) and badge (`Low`, `Medium`, `High`, `Critical`).
   * **Estimated Resolution Duration**: Displays predicted turnaround hours (e.g., `67.0 Hours / 2.8 Days`).

#### 3. 14-Day Grievance Intake Forecast Graph
* Visualizes the projected daily grievance intake trend using an interactive SVG projection curve with weekend and seasonal modulations.

#### 4. 8-Zone Spatial Hotspot Rankings
* Displays ranked risk cards for all 8 administrative zones (*Bommanahalli, Mahadevapura, East, West, South, Yelahanka, RR Nagar, Dasarahalli*) with active monsoon surge multipliers (+35% to +45%).

#### 5. One-Click Model Retraining
* Click **"Retrain ML Models on Historical Data"** to trigger asynchronous re-fitting over the 128,573 historical records.

---

## 7. Test Track 5: Multi-Department Testing Scenarios

Test how different issue types route to different civic agencies:

| Test Case | Sample Description Text | Expected Department | Assigned Officer Email |
|---|---|---|---|
| **Roads & Potholes** | *"Large pothole and broken asphalt on 100ft road Indiranagar"* | **BBMP** | `officer.bbmp@civicai.gov.in` |
| **Street Lighting** | *"Streetlight not working and road is pitch dark"* | **BBMP** | `officer.bbmp@civicai.gov.in` |
| **Electricity & Power** | *"High voltage electric wire snapped and transformer sparking"* | **BESCOM** | `officer.bescom@civicai.gov.in` |
| **Water & Sewerage** | *"Main water pipe burst flooding road and sewage overflowing"* | **BWSSB** | `officer.bwssb@civicai.gov.in` |
| **Solid Waste (Garbage)**| *"Garbage not collected by auto-tipper and massive blackspot waste pile"* | **BSWML** | `officer.bswml@civicai.gov.in` |
| **Waste Burning** | *"Plastic and garbage burning on roadside with toxic smoke"* | **BSWML** | `officer.bswml@civicai.gov.in` |

---

## 8. Test Track 6: Automated End-to-End Terminal Suite

To run the complete automated integration test suite in your terminal:

```powershell
# In workspace root (c:\Users\Lenovo\Desktop\CIVIC)
.\backend\venv\Scripts\python.exe backend\test_e2e.py
```

### What the Automated Suite Executes:
```
[Step 1] Logging in as Citizen (citizen@gmail.com)... ➔ PASSED
[Step 2] Raising a new Civic Complaint with Kannada text & GPS... ➔ PASSED
[Step 3] Verifying Multimodal Evidence Trust Score... ➔ PASSED
[Step 4] Testing AI Duplicate Detection for nearby complaint... ➔ PASSED
[Step 5] Logging in as Assigned Officer... ➔ PASSED
[Step 6] Officer Accepting Complaint and starting action work... ➔ PASSED
[Step 7] Officer Submitting Resolution Proof Photo... ➔ PASSED
[Step 8] Citizen Verification: Rejecting resolution (Reopen loop)... ➔ PASSED
[Step 9] Officer addressing feedback and re-resolving... ➔ PASSED
[Step 10] Citizen Verification: Approving resolution with 5 stars... ➔ PASSED
[Step 11] Logging in as Admin & checking Master Analytics... ➔ PASSED
[Step 12] Running manual Admin SLA Check Daemon... ➔ PASSED
[Step 13] Testing Phase 16 ML Predictive Intelligence & Forecasts... ➔ PASSED

🎉 ALL END-TO-END TESTS COMPLETED WITH 100% SUCCESS!
```

---

## 9. Test Track 7: Interactive Swagger REST API Testing

1. Open **`http://127.0.0.1:8000/docs`** in your browser.
2. Click the green **"Authorize"** button at the top right:
   * **Username**: `citizen@gmail.com`
   * **Password**: `citizenpassword`
   * Click **Authorize**.
3. Test key endpoints directly:
   * `POST /api/v1/complaints/check-duplicate`: Submit coordinates to test proximity scoring.
   * `GET /api/v1/complaints/{id}/evidence`: Inspect the detailed hard-gate verification diagnostic report, OpenCV quality metrics, gate states, and perceptual dHash.
   * `POST /api/v1/predictive/estimate`: Submit `{ "category": "Pothole", "ward": "Bommanahalli", "priority": "High" }` to inspect raw JSON predictions.
   * `GET /api/v1/predictive/overview`: Inspect live model metrics and telemetry.
   * `GET /api/v1/predictive/forecast`: View day-by-day projected grievance volumes.

---

## 10. Test Track 8: Automated Hard-Gate Evidence Verification Suite

To run the dedicated 11-scenario evidence verification test suite:

```powershell
# In workspace root (c:\Users\Lenovo\Desktop\CIVIC)
python -m backend.test_evidence_gates
```

### The 11 Verification Scenarios Executed:
```
================================================================================
TEST SUITE: Phase 8 & 9 Hard-Gate Evidence Verification & OpenCV Diagnostics
================================================================================

[Scenario 1] Genuine Field Image with Matching EXIF GPS & Timestamp...
   -> Decision: VERIFIED | Trust Score: 95.0% | Status: PASSED (Match: True)

[Scenario 2] GPS Mismatch Gate (EXIF >5000m away from complaint pin)...
   -> Decision: SUSPICIOUS | Trust Score: 25.0% | Status: PASSED (Match: True)

[Scenario 3] Stale Timestamp Gate (EXIF captured 5 days ago)...
   -> Decision: MANUAL_REVIEW | Trust Score: 40.0% | Status: PASSED (Match: True)

[Scenario 4] Future Timestamp Anomaly (EXIF 2 hours in future)...
   -> Decision: MANUAL_REVIEW | Trust Score: 40.0% | Status: PASSED (Match: True)

[Scenario 5] Semantic Category Mismatch (Pothole text vs. Laptop image)...
   -> Decision: SUSPICIOUS | Trust Score: 20.0% | Status: PASSED (Match: True)

[Scenario 6] Reused Image / Recycled Evidence (Duplicate 64-bit dHash)...
   -> Decision: SUSPICIOUS | Trust Score: 30.0% | Status: PASSED (Match: True)

[Scenario 7] Stripped EXIF / Social Media Upload (Missing EXIF headers)...
   -> Decision: PARTIALLY_VERIFIED | Trust Score: 60.0% | Status: PASSED (Match: True)

[Scenario 8] Blurry Low-Quality Photo (OpenCV Laplacian Var < 25.0)...
   -> Decision: MANUAL_REVIEW | Quality: BLURRY | Status: PASSED (Match: True)

[Scenario 9] Underexposed / Dark Photo (Mean Luminance < 25)...
   -> Decision: MANUAL_REVIEW | Quality: UNDEREXPOSED | Status: PASSED (Match: True)

[Scenario 10] Overexposed / Washed-out Photo (Mean Luminance > 245)...
   -> Decision: MANUAL_REVIEW | Quality: OVEREXPOSED | Status: PASSED (Match: True)

[Scenario 11] Sub-Resolution Image (Dimensions < 100x100 pixels)...
   -> Decision: MANUAL_REVIEW | Quality: LOW_RESOLUTION | Status: PASSED (Match: True)

================================================================================
SUMMARY: 11/11 Passed (100.0%) | Failures: 0
================================================================================
```

---

## 11. Edge Cases & Security Validation

| Security / Integrity Check | Test Action | Expected Safe Result |
|---|---|---|
| **Cross-Officer Tampering** | Log in as BWSSB Officer and try to transition a BBMP complaint | ❌ Returns `HTTP 403 Forbidden: Officer is not assigned to this complaint` |
| **Citizen Status Bypass** | Log in as Citizen and try to force status to `Resolved` | ❌ Returns `HTTP 400 Bad Request: Citizens can only close or reopen complaints` |
| **Duplicate Flooding** | Submit two identical complaints within 50m of each other | ℹ️ Automatically links second complaint as duplicate and closes child ticket |
| **Tampered / Recycled Image** | Submit a recycled photo from an older complaint or mismatched EXIF GPS | ℹ️ Hard Gate flags `is_reused_image = True` or `gps_match_status = SUSPICIOUS` $\to$ Decision: `SUSPICIOUS` |
| **Semantic Mismatch** | Submit a complaint for "pothole" with a photo of a dog or office computer | ⚠️ Gate 3 fails $\to$ Decision strictly barred from `VERIFIED`, capped at `SUSPICIOUS` |
| **Blurry / Dark Image** | Upload an unreadable, pitch-dark, or blurry photo | ℹ️ OpenCV triggers `MANUAL_REVIEW` requiring officer physical inspection |
| **SLA Deadline Breach** | Wait for SLA duration to exceed policy limit | ⚠️ System automatically marks ticket `SLA Status: Breached` and flags `is_escalated = True` |

---

## 🏁 Testing Summary Checklist

- [ ] Citizen can log in and submit complaints in Kannada and English.
- [ ] AI automatically categorizes issue and routes to the correct Karnataka agency (**BBMP, BESCOM, BWSSB, BSWML**).
- [ ] OpenCV verifies image quality (Laplacian blur variance, luminance, resolution).
- [ ] Multimodal Hard Gates evaluate EXIF GPS proximity, timestamp recency, semantic matching, and perceptual dHash reuse.
- [ ] Evidence Trust Score accurately displays badge (`VERIFIED`, `PARTIALLY_VERIFIED`, `MANUAL_REVIEW`, `SUSPICIOUS`, `REJECTED`).
- [ ] Field officers can inspect evidence audit diagnostics, accept, progress, and submit photo resolution proof.
- [ ] Citizen verification allows both 1-click approval (5-star rating) and reopen feedback loops.
- [ ] Admin dashboard displays GIS hotspot clustering and SLA compliance dials.
- [ ] Phase 16 ML early warning calculates SLA breach probability and 14-day grievance forecasts.
- [ ] Hard-Gate Evidence test suite (`python -m backend.test_evidence_gates`) executes 11/11 tests cleanly.
- [ ] Master integration test suite (`test_e2e.py`) executes 13/13 steps cleanly.
