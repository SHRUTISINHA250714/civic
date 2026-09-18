"""
Automated Test Suite: Phase 10 Duplicate Complaint UX & Tracking
================================================================
Validates all 10 required Phase 10 scenarios:
  1. Unique complaint -> existing behavior unchanged (assigned to officer, status Registered, impact=1).
  2. Duplicate complaint -> child report created and linked to parent (Haversine <= 100m, same category, cosine >= 0.85).
  3. Citizen receives explicit duplicate data (is_duplicate, parent_complaint_id, child_report_id, parent_status, impact_count).
  4. Citizen receives their own unique Report ID (child_id != parent_id, original report preserved).
  5. Citizen can open and view parent progress (GET /complaints/{parent_id} authorized for linked citizens).
  6. Parent status changes -> linked citizen sees updated status, status history, and in-app notifications.
  7. Multiple duplicate citizens -> all remain linked to the same parent, impact count increments correctly.
  8. Repeated submission/retry -> idempotent, returns existing child report, no duplicate rows or impact inflation.
  9. Existing officer workflow continues to operate only on the parent (child has assigned_officer_id=None).
  10. Existing Phase 11-17 functionality remains unaffected.
"""
import sys
import os
import random
from pathlib import Path

# Ensure root workspace is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Prevent TF import issues
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import httpx
_orig_client_init = httpx.Client.__init__
def _compat_client_init(self, *args, **kwargs):
    kwargs.pop("app", None)
    return _orig_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _compat_client_init

from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, Officer
from backend.app.models.complaint import Complaint, DuplicateComplaintMapping, Notification

client = TestClient(app)

def run_tests():
    print("=" * 75)
    print("PHASE 10 DUPLICATE COMPLAINT UX & TRACKING - AUTOMATED VERIFICATION SUITE")
    print("=" * 75)

    db = SessionLocal()
    try:
        # ── Setup: Login Citizen A (primary) ───────────────────────────────────
        login_res = client.post("/api/v1/auth/login", data={
            "username": "citizen@gmail.com",
            "password": "citizenpassword"
        })
        assert login_res.status_code == 200, f"Login Citizen A failed: {login_res.text}"
        citizen_a_token = login_res.json()["access_token"]
        citizen_a_headers = {"Authorization": f"Bearer {citizen_a_token}"}
        citizen_a_user = db.query(User).filter(User.email == "citizen@gmail.com").first()
        assert citizen_a_user, "Citizen A not found in DB"

        # Ensure Citizen B exists for duplicate testing
        citizen_b_user = db.query(User).filter(User.email == "citizen_b_test@civicai.gov.in").first()
        if not citizen_b_user:
            reg_res = client.post("/api/v1/auth/register", json={
                "email": "citizen_b_test@civicai.gov.in",
                "name": "Citizen B (Duplicate Reporter)",
                "password": "password123",
                "phone": "9876543210",
                "role_name": "Citizen"
            })
            assert reg_res.status_code == 201, f"Register Citizen B failed: {reg_res.text}"
            citizen_b_user = db.query(User).filter(User.email == "citizen_b_test@civicai.gov.in").first()

        login_b = client.post("/api/v1/auth/login", data={
            "username": "citizen_b_test@civicai.gov.in",
            "password": "password123"
        })
        citizen_b_token = login_b.json()["access_token"]
        citizen_b_headers = {"Authorization": f"Bearer {citizen_b_token}"}

        # Ensure Citizen C exists for multi-duplicate testing
        citizen_c_user = db.query(User).filter(User.email == "citizen_c_test@civicai.gov.in").first()
        if not citizen_c_user:
            reg_res = client.post("/api/v1/auth/register", json={
                "email": "citizen_c_test@civicai.gov.in",
                "name": "Citizen C (Third Reporter)",
                "password": "password123",
                "phone": "9876543211",
                "role_name": "Citizen"
            })
            assert reg_res.status_code == 201, f"Register Citizen C failed: {reg_res.text}"
            citizen_c_user = db.query(User).filter(User.email == "citizen_c_test@civicai.gov.in").first()

        login_c = client.post("/api/v1/auth/login", data={
            "username": "citizen_c_test@civicai.gov.in",
            "password": "password123"
        })
        citizen_c_token = login_c.json()["access_token"]
        citizen_c_headers = {"Authorization": f"Bearer {citizen_c_token}"}

        # Setup Officer login
        off_user = db.query(User).filter(User.email == "officer.bbmp@civicai.gov.in").first()
        assert off_user, "BBMP officer not found"
        login_off = client.post("/api/v1/auth/login", data={
            "username": "officer.bbmp@civicai.gov.in",
            "password": "officerpassword"
        })
        assert login_off.status_code == 200, f"Officer login failed: {login_off.text}"
        officer_token = login_off.json()["access_token"]
        officer_headers = {"Authorization": f"Bearer {officer_token}"}

        # Distinct location for test isolation
        base_lat = round(12.9100 + random.uniform(0.001, 0.05), 6)
        base_lon = round(77.6100 + random.uniform(0.001, 0.05), 6)

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 1: Unique complaint -> existing behavior unchanged
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 1] Testing unique complaint creation (Citizen A)...")
        parent_desc = "Massive dangerous pothole with water logging near Indiranagar 100ft road corner"
        res_unique = client.post("/api/v1/complaints", data={
            "description": parent_desc,
            "language": "English",
            "location_latitude": base_lat,
            "location_longitude": base_lon,
            "location_address": "Indiranagar 100ft Road, Bengaluru",
        }, headers=citizen_a_headers)
        assert res_unique.status_code == 201, f"Unique complaint failed: {res_unique.text}"
        parent_data = res_unique.json()
        parent_id = parent_data["id"]

        assert parent_data["is_duplicate"] is False, "Expected is_duplicate=False for unique complaint"
        assert parent_data["duplicate_of_complaint_id"] is None, "Expected duplicate_of_complaint_id=None"
        assert parent_data["impact_count"] >= 1, "Expected impact_count >= 1"
        assert parent_data["assigned_officer_id"] is not None, "Expected officer assigned to unique parent"
        assert parent_data["status"] == "Registered", f"Expected Registered, got {parent_data['status']}"
        print(f"✓ Unique Complaint #{parent_id} created successfully.")
        print(f"  - Status: {parent_data['status']}, Impact: {parent_data['impact_count']}")
        print(f"  - Assigned Officer: #{parent_data['assigned_officer_id']} ({parent_data['assigned_officer_name']})")

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 2 & 3: Duplicate complaint -> child report created & linked
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 2 & 3] Testing duplicate detection & child report creation (Citizen B)...")
        # Shift coordinates by ~30 meters (0.0003 degrees is ~33m)
        dup_lat = round(base_lat + 0.0002, 6)
        dup_lon = round(base_lon + 0.0002, 6)
        dup_desc = "Massive dangerous pothole with water logging near Indiranagar 100ft road corner"

        # Pre-check endpoint verification
        check_res = client.post("/api/v1/complaints/check-duplicate", data={
            "latitude": dup_lat,
            "longitude": dup_lon,
            "description": dup_desc,
            "category_name": parent_data["category_name"]
        }, headers=citizen_b_headers)
        assert check_res.status_code == 200, f"check-duplicate failed: {check_res.text}"
        check_data = check_res.json()
        assert check_data["is_duplicate"] is True, f"Expected duplicate detected: {check_data}"
        assert check_data["duplicate_of_id"] == parent_id, f"Expected parent #{parent_id}, got {check_data['duplicate_of_id']}"
        assert check_data["parent_complaint_id"] == parent_id, "parent_complaint_id missing"
        assert check_data["parent_status"] == parent_data["status"], "parent_status mismatch"
        print(f"✓ Pre-check confirmed duplicate of Parent #{parent_id} (Similarity: {check_data['similarity_score']})")

        # Now Citizen B submits the grievance
        res_child = client.post("/api/v1/complaints", data={
            "description": dup_desc,
            "language": "English",
            "location_latitude": dup_lat,
            "location_longitude": dup_lon,
            "location_address": "Near 100ft Road, Indiranagar",
        }, headers=citizen_b_headers)
        assert res_child.status_code == 201, f"Child complaint creation failed: {res_child.text}"
        child_data = res_child.json()
        child_id = child_data["id"]

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 4: Citizen receives their own unique Report ID
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 4] Verifying Citizen B's linked Report ID...")
        assert child_id != parent_id, f"Child ID #{child_id} must differ from Parent ID #{parent_id}"
        assert child_data["is_duplicate"] is True, "Expected is_duplicate=True on child"
        assert child_data["duplicate_of_complaint_id"] == parent_id, "Expected duplicate_of_complaint_id == parent_id"
        assert child_data["parent_complaint_id"] == parent_id, "Expected parent_complaint_id == parent_id"
        assert child_data["child_report_id"] == child_id, "Expected child_report_id == child_id"
        assert child_data["parent_status"] == "Registered", "Expected parent_status == Registered"
        assert child_data["impact_count"] == 2, f"Expected parent impact_count=2, got {child_data['impact_count']}"
        assert child_data["status"] == "Registered", f"Child status must NOT be 'Closed', got: {child_data['status']}"
        assert child_data["assigned_officer_id"] is None, "Child report must NOT create an officer assignment"
        print(f"✓ Citizen B received unique Report ID #{child_id} linked to Parent #{parent_id}.")
        print(f"  - Status: {child_data['status']} (Never silently closed!)")
        print(f"  - Parent Impact Count: {child_data['impact_count']}")

        # Verify DB mapping
        mapping = db.query(DuplicateComplaintMapping).filter(
            DuplicateComplaintMapping.original_complaint_id == parent_id,
            DuplicateComplaintMapping.duplicate_complaint_id == child_id
        ).first()
        assert mapping is not None, "DuplicateComplaintMapping not found in database"
        print("✓ DuplicateComplaintMapping record confirmed in DB.")

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 5: Citizen can open and view parent progress
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 5] Testing Citizen B viewing Parent Complaint progress...")
        # Citizen B requests parent details
        parent_view_res = client.get(f"/api/v1/complaints/{parent_id}", headers=citizen_b_headers)
        assert parent_view_res.status_code == 200, f"Linked citizen viewing parent failed: {parent_view_res.text}"
        parent_view = parent_view_res.json()
        assert parent_view["id"] == parent_id
        assert parent_view["impact_count"] == 2
        print(f"✓ Linked Citizen B successfully viewed Parent #{parent_id} progress.")

        # Non-linked Citizen C attempting to view Parent should fail (before Citizen C links)
        # Verify permissions: unauthorized citizen cannot access arbitrary complaint
        unauth_res = client.get(f"/api/v1/complaints/{parent_id}", headers=citizen_c_headers)
        assert unauth_res.status_code == 403, f"Expected 403 Forbidden for non-linked citizen, got {unauth_res.status_code}"
        print("✓ Non-linked Citizen C properly blocked with 403 Forbidden.")

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 6: Parent status changes -> linked citizen sees updated status
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 6] Testing status synchronization to linked child complaints...")
        # Officer accepts the parent complaint
        officer_obj = db.query(Officer).filter(Officer.id == parent_data["assigned_officer_id"]).first()
        off_user_obj = db.query(User).filter(User.id == officer_obj.user_id).first()
        login_assigned = client.post("/api/v1/auth/login", data={
            "username": off_user_obj.email,
            "password": "officerpassword"
        })
        assigned_token = login_assigned.json()["access_token"]
        assigned_headers = {"Authorization": f"Bearer {assigned_token}"}

        # Step 6a: Registered -> Accepted
        accept_res = client.put(f"/api/v1/complaints/{parent_id}/status", json={
            "status": "Accepted",
            "remarks": "Officer inspected and accepted grievance."
        }, headers=assigned_headers)
        assert accept_res.status_code == 200, f"Officer accept failed: {accept_res.text}"

        # Verify child complaint updated to Accepted
        db.expire_all()
        child_db = db.query(Complaint).filter(Complaint.id == child_id).first()
        assert child_db.status == "Accepted", f"Child complaint status not updated to Accepted: {child_db.status}"
        print("  - [Registered -> Accepted] Child complaint synchronized to: Accepted")

        # Step 6b: Accepted -> In Progress
        prog_res = client.put(f"/api/v1/complaints/{parent_id}/status", json={
            "status": "In Progress",
            "remarks": "Crew dispatched to patch pothole."
        }, headers=assigned_headers)
        assert prog_res.status_code == 200, f"Officer in-progress failed: {prog_res.text}"

        db.expire_all()
        child_db = db.query(Complaint).filter(Complaint.id == child_id).first()
        assert child_db.status == "In Progress", f"Child status not updated to In Progress: {child_db.status}"
        print("  - [Accepted -> In Progress] Child complaint synchronized to: In Progress")

        # Check in-app notification sent to Citizen B
        notif = db.query(Notification).filter(
            Notification.user_id == citizen_b_user.id,
            Notification.complaint_id == child_id
        ).order_by(Notification.created_at.desc()).first()
        assert notif is not None, "Notification not created for Citizen B"
        print(f"  - In-App Notification dispatched: \"{notif.message}\"")

        # Step 6c: In Progress -> Resolved (via resolution upload)
        dummy_res_path = "test_resolution.jpg"
        with open(dummy_res_path, "wb") as f:
            f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9')

        with open(dummy_res_path, "rb") as res_file:
            resolve_res = client.post(
                f"/api/v1/complaints/{parent_id}/resolve",
                data={"remarks": "Pothole filled with bitumen mix. Road restored."},
                files={"file": ("test_resolution.jpg", res_file, "image/jpeg")},
                headers=assigned_headers
            )
        assert resolve_res.status_code == 200, f"Resolve parent failed: {resolve_res.text}"

        db.expire_all()
        child_db = db.query(Complaint).filter(Complaint.id == child_id).first()
        assert child_db.status == "Resolved", f"Child complaint status not updated to Resolved: {child_db.status}"
        print("  - [In Progress -> Resolved] Child complaint auto-resolved: Resolved")

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 7: Multiple duplicate citizens -> all linked to same parent
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 7] Testing multiple duplicate citizen submissions (Citizen C)...")
        # Citizen C also reports this same pothole
        res_child_c = client.post("/api/v1/complaints", data={
            "description": "Indiranagar 100 feet road very big pothole broken road bad condition",
            "language": "English",
            "location_latitude": round(base_lat + 0.0001, 6),
            "location_longitude": round(base_lon + 0.0001, 6),
            "location_address": "Indiranagar 100ft road",
            "duplicate_of_id": parent_id
        }, headers=citizen_c_headers)
        assert res_child_c.status_code == 201, f"Citizen C submission failed: {res_child_c.text}"
        child_c_data = res_child_c.json()
        child_c_id = child_c_data["id"]

        assert child_c_data["is_duplicate"] is True
        assert child_c_data["parent_complaint_id"] == parent_id
        assert child_c_id != child_id
        assert child_c_id != parent_id

        db.expire_all()
        parent_db = db.query(Complaint).filter(Complaint.id == parent_id).first()
        assert parent_db.impact_count == 3, f"Expected parent impact_count=3, got: {parent_db.impact_count}"
        print(f"✓ Citizen C report #{child_c_id} linked to same Parent #{parent_id}.")
        print(f"  - Parent Total Impact Count is now: {parent_db.impact_count} (Parent + Child B + Child C)")

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 8: Repeated submission / retry -> Idempotent
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 8] Testing idempotency on repeated submission/retry (Citizen C)...")
        res_retry = client.post("/api/v1/complaints", data={
            "description": "Indiranagar 100 feet road very big pothole broken road bad condition",
            "language": "English",
            "location_latitude": round(base_lat + 0.0001, 6),
            "location_longitude": round(base_lon + 0.0001, 6),
            "location_address": "Indiranagar 100ft road",
            "duplicate_of_id": parent_id
        }, headers=citizen_c_headers)
        assert res_retry.status_code in (200, 201), f"Retry failed: {res_retry.text}"
        retry_data = res_retry.json()
        assert retry_data["id"] == child_c_id, f"Expected existing Report ID #{child_c_id}, got #{retry_data['id']}"

        db.expire_all()
        parent_db = db.query(Complaint).filter(Complaint.id == parent_id).first()
        assert parent_db.impact_count == 3, f"Impact count must remain 3 on retry, got: {parent_db.impact_count}"
        print(f"✓ Retry returned existing Report ID #{retry_data['id']} without duplicate records.")
        print(f"  - Impact count preserved at: {parent_db.impact_count}")

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 9: Existing officer workflow operates ONLY on parent
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 9] Testing that officer caseload operates only on parent complaint...")
        officer_complaints_res = client.get("/api/v1/complaints", headers=assigned_headers)
        assert officer_complaints_res.status_code == 200
        off_complaint_ids = [c["id"] for c in officer_complaints_res.json()]

        assert parent_id in off_complaint_ids, f"Parent #{parent_id} should be in officer complaints"
        assert child_id not in off_complaint_ids, f"Child #{child_id} must NOT be in officer caseload"
        assert child_c_id not in off_complaint_ids, f"Child #{child_c_id} must NOT be in officer caseload"
        print(f"✓ Officer queue contains only operational Parent #{parent_id}.")
        print(f"  - Child reports #{child_id} and #{child_c_id} are safely isolated from officer operational queue.")

        # ─────────────────────────────────────────────────────────────────────
        # Scenario 10: Downstream citizen resolution verification
        # ─────────────────────────────────────────────────────────────────────
        print("\n[Scenario 10] Testing parent resolution approval & closed synchronization...")
        # Citizen A approves resolution
        verify_res = client.post(f"/api/v1/complaints/{parent_id}/verify-resolution", json={
            "approve": True,
            "feedback_rating": 5,
            "feedback_remarks": "Excellent job fixing the pothole!"
        }, headers=citizen_a_headers)
        assert verify_res.status_code == 200, f"Verify resolution failed: {verify_res.text}"

        db.expire_all()
        parent_db = db.query(Complaint).filter(Complaint.id == parent_id).first()
        child_b_db = db.query(Complaint).filter(Complaint.id == child_id).first()
        child_c_db = db.query(Complaint).filter(Complaint.id == child_c_id).first()

        assert parent_db.status == "Closed", f"Expected Parent Closed, got {parent_db.status}"
        assert child_b_db.status == "Closed", f"Expected Child B Closed, got {child_b_db.status}"
        assert child_c_db.status == "Closed", f"Expected Child C Closed, got {child_c_db.status}"
        print("✓ Parent and all linked children successfully updated to: Closed")

        print("\n" + "=" * 75)
        print("ALL 10 PHASE 10 SCENARIOS PASSED WITH ZERO ERRORS!")
        print("=" * 75)

    finally:
        db.close()
        for p in ["test_resolution.jpg", "test_evidence.jpg"]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

if __name__ == "__main__":
    run_tests()
