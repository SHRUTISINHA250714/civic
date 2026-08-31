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
10. [Edge Cases & Security Validation](#10-edge-cases--security-validation)

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
| 🚰 **BWSSB Officer** | Anil Gowda (BWSSB) | `officer.bwssb@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| ⚡ **BESCOM Officer** | Manjunath Swamy (BESCOM) | `officer.bescom@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| 🚦 **Traffic Police Officer**| Inspector Girish (BTP) | `officer.traffic@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| 🚇 **BMRCL Officer** | Suresh Nair (BMRCL) | `officer.bmrcl@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |
| 🏗️ **BDA Officer** | Kavitha Reddy (BDA) | `officer.bda@civicai.gov.in` | `officerpassword` | [`/officer/dashboard`](http://localhost:3000/officer/dashboard) |

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
* ✅ **Evidence Trust Card**: Displays a **Composite Trust Score (0–100%)** validating the GPS coordinate plausibility, submission timestamp, and YOLOv8 image-text agreement.
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

### Scenario 2.1: Officer Ticket Acceptance and Field Work
1. Log out (or open an Incognito browser window) and navigate to **`http://localhost:3000/login`**.
2. Sign in as the **BBMP Officer**:
   * **Email**: `officer.bbmp@civicai.gov.in`
   * **Password**: `officerpassword`
3. You will be redirected to the **Officer Dashboard** (`/officer/dashboard`).
4. Locate the newly filed complaint in your assigned queue:
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
  * Real-time active ticket distribution across *BBMP, BWSSB, BESCOM, BMRCL, BDA, and Traffic Police*.
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
| **Roads & Waste** | *"Large pothole and uncollected garbage on 100ft road Indiranagar"* | **BBMP** | `officer.bbmp@civicai.gov.in` |
| **Water Supply** | *"Main water pipe burst flooding road and low water pressure in 4th block"* | **BWSSB** | `officer.bwssb@civicai.gov.in` |
| **Electricity** | *"High voltage electric wire snapped and sparking on transformer pole"* | **BESCOM** | `officer.bescom@civicai.gov.in` |
| **Traffic** | *"Traffic signal junction stuck on red causing 2km bottleneck jam"* | **Traffic Police** | `officer.traffic@civicai.gov.in` |
| **Metro Transit**| *"Escalator broken and water leaking onto track at Indiranagar Metro Station"* | **BMRCL** | `officer.bmrcl@civicai.gov.in` |
| **Encroachment** | *"Illegal construction and layout footpath encroachment blocking stormwater drain"* | **BDA** | `officer.bda@civicai.gov.in` |

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
   * `POST /api/v1/predictive/estimate`: Submit `{ "category": "Pothole", "ward": "Bommanahalli", "priority": "High" }` to inspect raw JSON predictions.
   * `GET /api/v1/predictive/overview`: Inspect live model metrics and telemetry.
   * `GET /api/v1/predictive/forecast`: View day-by-day projected grievance volumes.

---

## 10. Edge Cases & Security Validation

| Security / Integrity Check | Test Action | Expected Safe Result |
|---|---|---|
| **Cross-Officer Tampering** | Log in as BWSSB Officer and try to transition a BBMP complaint | ❌ Returns `HTTP 403 Forbidden: Officer is not assigned to this complaint` |
| **Citizen Status Bypass** | Log in as Citizen and try to force status to `Resolved` | ❌ Returns `HTTP 400 Bad Request: Citizens can only close or reopen complaints` |
| **Duplicate Flooding** | Submit two identical complaints within 50m of each other | ℹ️ Automatically links second complaint as duplicate and closes child ticket |
| **Tampered / Indoor Image** | Submit a blank or indoor screen photo | ℹ️ Multimodal Trust Score drops to `Low / Suspicious` and flags ticket for officer inspection |
| **SLA Deadline Breach** | Wait for SLA duration to exceed policy limit | ⚠️ System automatically marks ticket `SLA Status: Breached` and flags `is_escalated = True` |

---

## 🏁 Testing Summary Checklist

- [ ] Citizen can log in and submit complaints in Kannada and English.
- [ ] AI automatically categorizes issue and routes to the correct Karnataka agency.
- [ ] Multimodal Evidence Trust Score evaluates GPS, timestamp, and YOLO visual data.
- [ ] Field officers can accept, progress, and submit photo resolution proof.
- [ ] Citizen verification allows both 1-click approval (5-star rating) and reopen feedback loops.
- [ ] Admin dashboard displays GIS hotspot clustering and SLA compliance dials.
- [ ] Phase 16 ML early warning calculates SLA breach probability and 14-day grievance forecasts.
- [ ] Automated integration test suite (`test_e2e.py`) executes 100% cleanly.
