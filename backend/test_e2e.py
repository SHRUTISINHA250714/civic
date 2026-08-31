import sys
import os
import requests
import json
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_full_workflow():
    print("=" * 70)
    print("CIVICAI KARNATAKA - COMPREHENSIVE END-TO-END VERIFICATION")
    print("=" * 70)
    
    # 1. Login as Citizen
    print("\n[Step 1] Logging in as Citizen (citizen@gmail.com)...")
    login_res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "citizen@gmail.com",
        "password": "citizenpassword"
    })
    assert login_res.status_code == 200, f"Citizen login failed: {login_res.text}"
    citizen_token = login_res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("✓ Citizen logged in successfully.")

    # 2. Raise a new Complaint with Kannada Voice/Text & Live GPS
    print("\n[Step 2] Raising a new Civic Complaint (Garbage & Pothole issue)...")
    import random
    rand_offset = random.uniform(0.01, 0.5)
    test_lat = round(12.9352 + rand_offset, 6)
    test_lon = round(77.6245 + rand_offset, 6)
    complaint_data = {
        "description": "Rasteyalli kachada thumbide mattu dodda gundi ide near Koramangala 5th block. Heavy traffic hazard!",
        "language": "Kannada",
        "location_latitude": test_lat,
        "location_longitude": test_lon,
        "location_address": "Koramangala 5th Block, Bengaluru, Karnataka"
    }
    
    # Create a small dummy image for testing upload
    dummy_img_path = "test_evidence.jpg"
    with open(dummy_img_path, "wb") as f:
        # Minimal JPEG header bytes
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9')
    
    with open(dummy_img_path, "rb") as img_file:
        files = {"file": ("test_evidence.jpg", img_file, "image/jpeg")}
        raise_res = requests.post(
            f"{BASE_URL}/complaints",
            data=complaint_data,
            files=files,
            headers=citizen_headers
        )
    
    assert raise_res.status_code == 201, f"Raise complaint failed: {raise_res.text}"
    complaint = raise_res.json()
    complaint_id = complaint["id"]
    print(f"✓ Complaint #{complaint_id} created successfully!")
    print(f"  - Translated Description: {complaint['description']}")
    print(f"  - Detected Category: {complaint['category_name']} (Dept: {complaint['department_name']})")
    print(f"  - AI Priority: {complaint['priority']}")
    print(f"  - SLA Deadline: {complaint['sla_deadline']}")
    print(f"  - SLA Status: {complaint['sla_status']}")
    
    # 3. Check Evidence Trust Score
    print("\n[Step 3] Verifying Multimodal Evidence Trust Score...")
    ev_res = requests.get(f"{BASE_URL}/complaints/{complaint_id}/evidence", headers=citizen_headers)
    assert ev_res.status_code == 200, f"Get evidence failed: {ev_res.text}"
    evidence = ev_res.json()
    print(f"✓ Evidence Trust Analysis:")
    print(f"  - Trust Score: {evidence['trust_score']}% ({evidence['trust_level']})")
    print(f"  - Live GPS provided: {evidence['live_gps_provided']}")
    print(f"  - Verification Details: {evidence['verification_details']}")

    # 4. Test Duplicate Detection
    print("\n[Step 4] Testing AI Duplicate Detection for nearby complaint...")
    dup_res = requests.post(f"{BASE_URL}/complaints/check-duplicate", data={
        "latitude": round(test_lat + 0.0001, 6),
        "longitude": round(test_lon + 0.0001, 6),
        "description": "Severe garbage dump and road hole blocking traffic at Koramangala 5th block",
        "category_name": complaint['category_name']
    }, headers=citizen_headers)
    assert dup_res.status_code == 200, f"Duplicate check failed: {dup_res.text}"
    dup_data = dup_res.json()
    print(f"✓ Duplicate Check Response: is_duplicate={dup_data['is_duplicate']}, score={dup_data['similarity_score']}")

    # 5. Login as Assigned Officer
    officer_id_to_email = {
        1: "officer.bbmp@civicai.gov.in",
        2: "officer.bwssb@civicai.gov.in",
        3: "officer.bescom@civicai.gov.in",
        4: "officer.traffic@civicai.gov.in",
        5: "officer.bmrcl@civicai.gov.in",
        6: "officer.bda@civicai.gov.in",
    }
    assigned_off_id = complaint.get("assigned_officer_id")
    officer_email = officer_id_to_email.get(assigned_off_id, "officer.bbmp@civicai.gov.in")
    print(f"\n[Step 5] Logging in as Assigned Officer #{assigned_off_id} ({officer_email} - {complaint.get('assigned_officer_name')})...")
    off_login = requests.post(f"{BASE_URL}/auth/login", data={
        "username": officer_email,
        "password": "officerpassword"
    })
    assert off_login.status_code == 200, f"Officer login failed: {off_login.text}"
    officer_token = off_login.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    print(f"✓ Assigned Officer ({officer_email}) logged in.")

    # 6. Officer moves status: Registered -> Accepted -> In Progress
    print("\n[Step 6] Officer Accepting Complaint and starting action work...")
    acc_res = requests.put(f"{BASE_URL}/complaints/{complaint_id}/status", json={
        "status": "Accepted",
        "remarks": "Assigned crew to inspect Koramangala 5th block site."
    }, headers=officer_headers)
    assert acc_res.status_code == 200, f"Accept failed: {acc_res.text}"
    print(f"✓ Status transitioned to 'Accepted'.")

    prog_res = requests.put(f"{BASE_URL}/complaints/{complaint_id}/status", json={
        "status": "In Progress",
        "remarks": "Crew dispatched with garbage compactor and asphalt patch team."
    }, headers=officer_headers)
    assert prog_res.status_code == 200, f"In Progress failed: {prog_res.text}"
    print(f"✓ Status transitioned to 'In Progress'.")

    # 7. Officer Resolves Complaint with resolution proof
    print("\n[Step 7] Officer Submitting Resolution Proof Photo...")
    with open(dummy_img_path, "rb") as res_img:
        resolve_res = requests.post(
            f"{BASE_URL}/complaints/{complaint_id}/resolve",
            data={"remarks": "Garbage cleared completely and pothole filled with cold mix asphalt."},
            files={"file": ("resolution_proof.jpg", res_img, "image/jpeg")},
            headers=officer_headers
        )
    assert resolve_res.status_code == 200, f"Resolve failed: {resolve_res.text}"
    resolved_complaint = resolve_res.json()
    print(f"✓ Complaint marked 'Resolved'. Citizen verification state: {resolved_complaint['citizen_verified']}")

    # 8. Citizen Feedback Loop - REJECT & REOPEN
    print("\n[Step 8] Citizen Verification: Rejecting resolution (Pothole not leveled properly)...")
    reject_res = requests.post(
        f"{BASE_URL}/complaints/{complaint_id}/verify-resolution",
        json={
            "approve": False,
            "feedback_rating": 2,
            "feedback_remarks": "Garbage was cleared but the road pothole was only half-filled and is still uneven."
        },
        headers=citizen_headers
    )
    assert reject_res.status_code == 200, f"Reject/reopen failed: {reject_res.text}"
    reopened = reject_res.json()
    print(f"✓ Complaint Status is now '{reopened['status']}'! Reopen count: {reopened['reopen_count']}")
    assert reopened["status"] == "Reopened"
    assert reopened["reopen_count"] == 1

    # 9. Officer Re-Resolves with complete fix
    print("\n[Step 9] Officer addressing feedback and re-resolving...")
    with open(dummy_img_path, "rb") as re_res_img:
        re_resolve_res = requests.post(
            f"{BASE_URL}/complaints/{complaint_id}/resolve",
            data={"remarks": "Steam roller applied, road patch leveled flush with street surface."},
            files={"file": ("final_resolution.jpg", re_res_img, "image/jpeg")},
            headers=officer_headers
        )
    assert re_resolve_res.status_code == 200, f"Re-resolve failed: {re_resolve_res.text}"
    print("✓ Officer re-submitted resolution.")

    # 10. Citizen Approves & Closes Complaint
    print("\n[Step 10] Citizen Verification: Approving resolution with 5-star rating...")
    approve_res = requests.post(
        f"{BASE_URL}/complaints/{complaint_id}/verify-resolution",
        json={
            "approve": True,
            "feedback_rating": 5,
            "feedback_remarks": "Great work! Perfectly leveled road and spotlessly clean."
        },
        headers=citizen_headers
    )
    assert approve_res.status_code == 200, f"Approve failed: {approve_res.text}"
    closed_complaint = approve_res.json()
    print(f"✓ Complaint Status is now '{closed_complaint['status']}'!")
    assert closed_complaint["status"] == "Closed"
    assert closed_complaint["citizen_feedback_rating"] == 5

    # 11. Admin Dashboard & SLA Analytics Verification
    print("\n[Step 11] Logging in as Admin (admin@civicai.gov.in) & checking Dashboard...")
    admin_login = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "admin@civicai.gov.in",
        "password": "adminpassword"
    })
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    dash_res = requests.get(f"{BASE_URL}/dashboard/admin", headers=admin_headers)
    assert dash_res.status_code == 200, f"Admin dashboard failed: {dash_res.text}"
    dash_data = dash_res.json()
    print("✓ Admin Analytics retrieved successfully:")
    print(f"  - Total Complaints: {dash_data['complaints']['total']}")
    print(f"  - Closed Complaints: {dash_data['complaints']['closed']}")
    print(f"  - Reopened Complaints: {dash_data['complaints']['reopened']}")
    print(f"  - SLA Compliance: {dash_data['sla_monitoring']['compliance_percent']}%")
    print(f"  - Evidence Trust (High/Med/Low/Suspicious): {dash_data['evidence_trust']['high']}/{dash_data['evidence_trust']['medium']}/{dash_data['evidence_trust']['low']}/{dash_data['evidence_trust']['suspicious']}")
    print(f"  - GIS Hotspots Count: {len(dash_data['gis_hotspots'])}")
    print(f"  - Departments monitored: {list(dash_data['department_distribution'].keys())}")

    # 12. Trigger Admin SLA Check
    print("\n[Step 12] Running manual Admin SLA Check...")
    sla_check_res = requests.post(f"{BASE_URL}/dashboard/admin/run-sla-check", headers=admin_headers)
    assert sla_check_res.status_code == 200
    print(f"✓ SLA check result: {sla_check_res.json()['message']}")

    # 13. Test Phase 16: Predictive Analytics & ML Forecasting
    print("\n[Step 13] Testing Phase 16 Predictive Intelligence & ML Forecasting...")
    pred_res = requests.get(f"{BASE_URL}/predictive/overview", headers=admin_headers)
    assert pred_res.status_code == 200, f"Predictive overview failed: {pred_res.text}"
    pred_data = pred_res.json()
    print("✓ Predictive Overview retrieved:")
    print(f"  - Model Accuracy: {pred_data['model_metadata'].get('sla_classifier_accuracy')}% (ROC-AUC: {pred_data['model_metadata'].get('sla_classifier_auc')})")
    print(f"  - Resolution Time MAE: ±{pred_data['model_metadata'].get('resolution_mae_hours')} hrs")
    print(f"  - Highest Risk Zone: {pred_data['early_warning_kpis'].get('highest_risk_zone')} (Score: {pred_data['early_warning_kpis'].get('highest_risk_zone_score')})")
    print(f"  - 14-Day Projected Grievances: {pred_data['early_warning_kpis'].get('projected_14d_volume')}")

    # Test ML Real-time Estimate API
    est_res = requests.post(f"{BASE_URL}/predictive/estimate", json={
        "category": "Pothole",
        "ward": "Koramangala",
        "priority": "High",
        "department": "BBMP"
    }, headers=admin_headers)
    assert est_res.status_code == 200, f"Predictive estimate failed: {est_res.text}"
    est_data = est_res.json()
    print("✓ ML Risk & Time Estimator:")
    print(f"  - Predicted Breach Risk: {est_data['sla_breach_probability_pct']}% ({est_data['risk_level']})")
    print(f"  - Estimated Resolution Time: {est_data['estimated_resolution_hours']} hours ({est_data['estimated_resolution_days']} days)")

    # Test Hotspot Forecasts API
    hot_res = requests.get(f"{BASE_URL}/predictive/hotspots", headers=admin_headers)
    assert hot_res.status_code == 200, f"Hotspots failed: {hot_res.text}"
    hot_data = hot_res.json()
    print(f"✓ Hotspot Wards Forecast retrieved: {len(hot_data)} wards analyzed.")
    assert len(hot_data) > 0

    # Test Time-Series Daily Forecast API
    fc_res = requests.get(f"{BASE_URL}/predictive/forecast?days=14", headers=admin_headers)
    assert fc_res.status_code == 200, f"Forecast failed: {fc_res.text}"
    fc_data = fc_res.json()
    print(f"✓ 14-Day Forecast Projections retrieved: {len(fc_data['forecast_14d'])} days projected.")
    assert len(fc_data['forecast_14d']) == 14

    # Clean up test image
    if os.path.exists(dummy_img_path):
        os.remove(dummy_img_path)

    print("\n" + "=" * 70)
    print("🎉 ALL END-TO-END TESTS (PHASE 1 - 17) COMPLETED & PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    test_full_workflow()
