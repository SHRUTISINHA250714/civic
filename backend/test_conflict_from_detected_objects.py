"""
Test Suite: Cross-Department Image-Text Conflict Detection from YOLO Detected Objects
=====================================================================================
Tests the cross-department evidence conflict path in `raise_complaint`:
1. Positive Case:
   - Complaint text describes a water pipe burst (routed to BWSSB).
   - Vision evidence returns detected civic objects as a JSON string containing "pothole" / "road_crack".
   - The JSON string is parsed, the cross-agency conflict (BWSSB text vs BBMP image) is detected.
   - Text department (BWSSB) is retained pending manual officer inspection.
   - verification_decision becomes 'MANUAL_REVIEW'.
   - Initial status remark is formatted as a clean sentence without raw brackets or quotes.
2. Negative Case:
   - Complaint text describes a road pothole (routed to BBMP).
   - Vision evidence returns detected civic objects ["pothole"] (matching BBMP).
   - No department conflict occurs.
   - Status history remark does NOT flag a department conflict.
"""
import os
import sys
import json
import random
from unittest.mock import patch

# Prevent TF import issues
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"

# Add project root to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# httpx compatibility with starlette.testclient
import httpx
_orig_client_init = httpx.Client.__init__
def _compat_client_init(self, *args, **kwargs):
    kwargs.pop("cookies", None)
    return _orig_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _compat_client_init

from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.complaint import Complaint, ComplaintStatusHistory
from backend.test_helpers import get_test_image_bytes, cleanup_temp_images

client = TestClient(app)


def test_conflict_detection_from_detected_objects():
    print("=" * 80)
    print("CROSS-DEPARTMENT CONFLICT DETECTION FROM YOLO DETECTED OBJECTS")
    print("=" * 80)

    # 1. Login as citizen
    login_res = client.post("/api/v1/auth/login", data={
        "username": "citizen@gmail.com",
        "password": "citizenpassword"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Isolated coordinates far from Bengaluru to avoid duplicate collisions
    base_lat = round(22.3000 + random.uniform(0.01, 0.05), 6)
    base_lon = round(73.1800 + random.uniform(0.01, 0.05), 6)

    # ─────────────────────────────────────────────────────────────────────────
    # CASE 1: Positive Case - Water leak complaint with pothole/road_crack image
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Case 1] Submitting Water Leak complaint with Pothole/Road Crack image...")
    water_desc = "Drinking water pipeline burst on main road with heavy water leakage and no water supply"
    seed1 = random.randint(100000, 499999)
    img_bytes_1 = get_test_image_bytes(seed=seed1)

    with patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(
        "MISMATCH", 0.90, "Potholes & Damaged Roads", "Image depicts road damage and potholes instead of water pipeline burst."
    )), patch("backend.app.services.evidence.run_yolo_detection", return_value={
        "detected_objects": ["pothole", "road_crack"],
        "bounding_boxes": [],
        "confidence_scores": {"pothole": 0.94, "road_crack": 0.88},
        "has_civic_objects": True,
        "is_indoor_device": False
    }):
        res1 = client.post("/api/v1/complaints", data={
            "description": water_desc,
            "language": "English",
            "location_latitude": base_lat,
            "location_longitude": base_lon,
            "location_address": "Koramangala 80ft Road, Bengaluru"
        }, files={"file": ("pothole_photo.jpg", img_bytes_1, "image/jpeg")}, headers=headers)

    assert res1.status_code == 201, f"Complaint submission failed: {res1.text}"
    c1_data = res1.json()
    c1_id = c1_data["id"]
    print(f"✓ Complaint #{c1_id} created successfully.")

    db = SessionLocal()
    try:
        c1 = db.query(Complaint).filter(Complaint.id == c1_id).first()
        assert c1 is not None, "Complaint record not found in DB"

        # Department must stay BWSSB (the text department)
        assert c1.category.department.code == "BWSSB", (
            f"Expected department BWSSB, got {c1.category.department.code}"
        )
        assert c1.category.name == "Water Pipeline Burst & Leakage", (
            f"Expected category 'Water Pipeline Burst & Leakage', got '{c1.category.name}'"
        )
        print(f"  ✓ Department correctly retained as text department: {c1.category.department.code}")

        # Verification decision must be MANUAL_REVIEW
        assert c1.evidence_check is not None, "Evidence check record missing"
        assert c1.evidence_check.verification_decision == "MANUAL_REVIEW", (
            f"Expected MANUAL_REVIEW, got {c1.evidence_check.verification_decision}"
        )
        print(f"  ✓ Verification decision set to: {c1.evidence_check.verification_decision}")

        # Detected objects must be parsed from JSON string
        vis_raw = c1.evidence_check.vision_objects_detected
        assert isinstance(vis_raw, str), f"Expected vision_objects_detected to be stored as str, got {type(vis_raw)}"
        parsed_objs = json.loads(vis_raw)
        assert "pothole" in parsed_objs and "road_crack" in parsed_objs, (
            f"Expected ['pothole', 'road_crack'] in parsed vision objects, got {parsed_objs}"
        )
        print(f"  ✓ Stored vision_objects_detected JSON parsed correctly: {parsed_objs}")

        # Initial status remark must be a clean sentence with no brackets
        hist1 = db.query(ComplaintStatusHistory).filter(
            ComplaintStatusHistory.complaint_id == c1_id
        ).order_by(ComplaintStatusHistory.id.asc()).first()
        assert hist1 is not None, "Initial status history missing"
        remark1 = hist1.remarks or ""
        print(f"  ✓ Initial remark: '{remark1}'")

        assert "Department mismatch between complaint text (BWSSB) and image evidence (BBMP:" in remark1, (
            f"Expected department mismatch explanation in remark, got: {remark1}"
        )
        assert "Retained text department BWSSB pending manual officer review." in remark1, (
            f"Expected retention notice in remark, got: {remark1}"
        )
        assert "[" not in remark1 and "]" not in remark1, (
            f"Remark contains list brackets: {remark1}"
        )
        print("  ✓ Remark is a clean sentence without list brackets or quotes.")

    finally:
        db.close()

    # ─────────────────────────────────────────────────────────────────────────
    # CASE 2: Negative Case - Pothole complaint with matching pothole image
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Case 2] Submitting Pothole complaint with matching Pothole image...")
    pothole_desc = "Massive deep pothole on main road creating severe accident hazard"
    seed2 = random.randint(500000, 999999)
    img_bytes_2 = get_test_image_bytes(seed=seed2)
    lat2 = round(base_lat + 0.05, 6)
    lon2 = round(base_lon + 0.05, 6)

    with patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(
        "MATCH", 0.95, "Potholes & Damaged Roads", "Civic AI model confirmed road damage/pothole directly matching complaint."
    )), patch("backend.app.services.evidence.run_yolo_detection", return_value={
        "detected_objects": ["pothole"],
        "bounding_boxes": [],
        "confidence_scores": {"pothole": 0.95},
        "has_civic_objects": True,
        "is_indoor_device": False
    }):
        res2 = client.post("/api/v1/complaints", data={
            "description": pothole_desc,
            "language": "English",
            "location_latitude": lat2,
            "location_longitude": lon2,
            "location_address": "Indiranagar 100ft Road, Bengaluru"
        }, files={"file": ("matching_pothole.jpg", img_bytes_2, "image/jpeg")}, headers=headers)

    assert res2.status_code == 201, f"Complaint submission failed: {res2.text}"
    c2_data = res2.json()
    c2_id = c2_data["id"]
    print(f"✓ Complaint #{c2_id} created successfully.")

    db = SessionLocal()
    try:
        c2 = db.query(Complaint).filter(Complaint.id == c2_id).first()
        assert c2 is not None, "Complaint record not found in DB"

        # Department is BBMP
        assert c2.category.department.code == "BBMP", (
            f"Expected department BBMP, got {c2.category.department.code}"
        )
        print(f"  ✓ Department correctly assigned: {c2.category.department.code}")

        # Verification decision must NOT be forced to MANUAL_REVIEW due to department conflict
        assert c2.evidence_check is not None
        assert c2.evidence_check.verification_decision != "MANUAL_REVIEW", (
            f"Matching evidence should not be forced into MANUAL_REVIEW, got {c2.evidence_check.verification_decision}"
        )
        assert c2.evidence_check.verification_decision in ["VERIFIED", "PARTIALLY_VERIFIED"], (
            f"Expected verified state (VERIFIED or PARTIALLY_VERIFIED), got {c2.evidence_check.verification_decision}"
        )
        print(f"  ✓ Verification decision is: {c2.evidence_check.verification_decision} (NOT MANUAL_REVIEW)")

        # Status history remark must NOT mention department mismatch
        hist2 = db.query(ComplaintStatusHistory).filter(
            ComplaintStatusHistory.complaint_id == c2_id
        ).order_by(ComplaintStatusHistory.id.asc()).first()
        remark2 = hist2.remarks or ""
        print(f"  ✓ Initial remark: '{remark2}'")
        assert "Department mismatch" not in remark2, (
            f"Matching complaint incorrectly flagged with department mismatch: {remark2}"
        )
        assert "[" not in remark2 and "]" not in remark2, (
            f"Remark contains brackets: {remark2}"
        )
        print("  ✓ Correctly verified: NO department conflict flagged.")

    finally:
        db.close()

    # ─────────────────────────────────────────────────────────────────────────
    # CASE 3 (Matrix Row 1): Streetlight fixture + ['streetlight', 'damaged_electrical_pole']
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Case 3] Submitting Streetlight Fixture complaint with pole/streetlight photo (Matrix Row 1)...")
    st_desc = "Streetlight fixture bulb is broken and dark on 80 Feet Road, Indiranagar."
    seed3 = random.randint(100000, 499999)
    img_bytes_3 = get_test_image_bytes(seed=seed3)
    lat3 = round(base_lat + 0.08, 6)
    lon3 = round(base_lon + 0.08, 6)

    with patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(
        "MATCH", 0.95, "Damaged Streetlights", "Streetlight fixture with bulb damaged."
    )), patch("backend.app.services.evidence.run_yolo_detection", return_value={
        "detected_objects": ["streetlight", "damaged_electrical_pole"],
        "bounding_boxes": [],
        "confidence_scores": {"streetlight": 0.92, "damaged_electrical_pole": 0.85},
        "has_civic_objects": True,
        "is_indoor_device": False
    }):
        res3 = client.post("/api/v1/complaints", data={
            "description": st_desc,
            "language": "English",
            "location_latitude": lat3,
            "location_longitude": lon3,
            "location_address": "80 Feet Road, Indiranagar"
        }, files={"file": ("streetlight_pole.jpg", img_bytes_3, "image/jpeg")}, headers=headers)

    assert res3.status_code == 201, f"Complaint 3 failed: {res3.text}"
    c3_id = res3.json()["id"]

    db = SessionLocal()
    try:
        c3 = db.query(Complaint).filter(Complaint.id == c3_id).first()
        assert c3.category.department.code == "BBMP", f"Expected BBMP, got {c3.category.department.code}"
        assert c3.evidence_check.verification_decision != "MANUAL_REVIEW"
        hist3 = db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == c3_id).first()
        assert "Department mismatch" not in (hist3.remarks or "")
        print(f"  ✓ Streetlight fixture on pole correctly retained BBMP without false conflict.")
    finally:
        db.close()

    # ─────────────────────────────────────────────────────────────────────────
    # CASE 4 (Matrix Row 3): Stormwater drain + ['water_leak']
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Case 4] Submitting Stormwater Drain complaint with water_leak photo (Matrix Row 3)...")
    drain_desc = "Heavy rain caused severe waterlogging and the stormwater drain is blocked on the road."
    seed4 = random.randint(500000, 999999)
    img_bytes_4 = get_test_image_bytes(seed=seed4)
    lat4 = round(base_lat + 0.12, 6)
    lon4 = round(base_lon + 0.12, 6)

    with patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(
        "MATCH", 0.95, "Blocked Stormwater Drains & Waterlogging", "Waterlogged street from drain."
    )), patch("backend.app.services.evidence.run_yolo_detection", return_value={
        "detected_objects": ["water_leak"],
        "bounding_boxes": [],
        "confidence_scores": {"water_leak": 0.90},
        "has_civic_objects": True,
        "is_indoor_device": False
    }):
        res4 = client.post("/api/v1/complaints", data={
            "description": drain_desc,
            "language": "English",
            "location_latitude": lat4,
            "location_longitude": lon4,
            "location_address": "Indiranagar Road, Bengaluru"
        }, files={"file": ("drain_water.jpg", img_bytes_4, "image/jpeg")}, headers=headers)

    assert res4.status_code == 201, f"Complaint 4 failed: {res4.text}"
    c4_id = res4.json()["id"]

    db = SessionLocal()
    try:
        c4 = db.query(Complaint).filter(Complaint.id == c4_id).first()
        assert c4.category.department.code == "BBMP", f"Expected BBMP, got {c4.category.department.code}"
        assert c4.evidence_check.verification_decision != "MANUAL_REVIEW"
        hist4 = db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == c4_id).first()
        assert "Department mismatch" not in (hist4.remarks or "")
        print(f"  ✓ Stormwater drain correctly retained BBMP without false BWSSB conflict.")
    finally:
        db.close()

    # ─────────────────────────────────────────────────────────────────────────
    # CASE 5 (Matrix Row 4): Garbage Overflow + ['garbage', 'road_crack']
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[Case 5] Submitting Garbage complaint with mixed garbage + road_crack photo (Matrix Row 4)...")
    garbage_desc = "Garbage has not been collected for a week and the bins are overflowing."
    seed5 = random.randint(100000, 499999)
    img_bytes_5 = get_test_image_bytes(seed=seed5)
    lat5 = round(base_lat + 0.16, 6)
    lon5 = round(base_lon + 0.16, 6)

    with patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(
        "MATCH", 0.95, "Overflowing Garbage Bins & Blackspots", "Overflowing garbage bins on roadside."
    )), patch("backend.app.services.evidence.run_yolo_detection", return_value={
        "detected_objects": ["garbage", "road_crack"],
        "bounding_boxes": [],
        "confidence_scores": {"garbage": 0.95, "road_crack": 0.80},
        "has_civic_objects": True,
        "is_indoor_device": False
    }):
        res5 = client.post("/api/v1/complaints", data={
            "description": garbage_desc,
            "language": "English",
            "location_latitude": lat5,
            "location_longitude": lon5,
            "location_address": "Indiranagar, Bengaluru"
        }, files={"file": ("mixed_garbage_road.jpg", img_bytes_5, "image/jpeg")}, headers=headers)

    assert res5.status_code == 201, f"Complaint 5 failed: {res5.text}"
    c5_id = res5.json()["id"]

    db = SessionLocal()
    try:
        c5 = db.query(Complaint).filter(Complaint.id == c5_id).first()
        assert c5.category.department.code == "BSWML", f"Expected BSWML, got {c5.category.department.code}"
        assert c5.evidence_check.verification_decision != "MANUAL_REVIEW"
        hist5 = db.query(ComplaintStatusHistory).filter(ComplaintStatusHistory.complaint_id == c5_id).first()
        assert "Department mismatch" not in (hist5.remarks or "")
        print(f"  ✓ Mixed garbage photo correctly retained BSWML without false BBMP conflict.")
    finally:
        db.close()


def test_12_matrix_rows_direct_helper():
    print("\n" + "=" * 80)
    print("DIRECT HELPER VERIFICATION: ALL 12 MATRIX ROWS")
    print("=" * 80)
    from backend.app.services.ai import classify_complaint_structured
    from backend.app.routers.complaints import detect_department_conflict

    matrix = [
        (1, "Streetlight fixture bulb is broken and dark on 80 Feet Road, Indiranagar.", ["streetlight", "damaged_electrical_pole"], False),
        (2, "Streetlight feeder line power supply fault, no power to the street light.", ["streetlight", "damaged_electrical_pole"], False),
        (3, "Heavy rain caused severe waterlogging and the stormwater drain is blocked on the road.", ["water_leak"], False),
        (4, "Garbage has not been collected for a week and the bins are overflowing.", ["garbage", "road_crack"], False),
        (5, "Drinking water pipeline burst on main road with heavy water leakage.", ["pothole", "road_crack"], True),
        (6, "A large pothole on the road is dangerous for two-wheelers.", ["garbage"], True),
        (7, "A large pothole on the road is dangerous for two-wheelers.", ["pothole", "water_leak"], False),
        (8, "Exposed live wires hanging from the electric pole near the school are dangerous.", ["damaged_electrical_pole"], False),
        (9, "Tree branches are touching the power lines near my house.", ["fallen_tree", "damaged_electrical_pole"], False),
        (10, "The pavement near the hospital is broken and the walkway is unsafe.", ["road_crack"], False),
        (11, "Garbage has been dumped into the drain and it is blocked.", ["garbage", "water_leak"], False),
        (12, "A dead dog is lying on the road since yesterday.", [], False),
    ]

    for idx, text, objs, expected in matrix:
        routing_res = classify_complaint_structured(text)
        cat_name = routing_res.get("category_name")
        text_dept = routing_res.get("department_code")
        sec_dept = routing_res.get("secondary_agency")

        conflict, img_dept, reason = detect_department_conflict(
            text_category=cat_name,
            text_dept=text_dept,
            secondary_dept=sec_dept,
            detected_set=set(objs),
            img_cat="Potholes & Damaged Roads" if idx == 5 else "Garbage" if idx == 6 else "",
            semantic_status="MISMATCH" if idx in [5, 6] else "MATCH"
        )
        assert conflict == expected, (
            f"Row {idx} failed: got conflict={conflict}, expected={expected} (reason: {reason})"
        )
        if conflict:
            assert "[" not in reason and "]" not in reason, f"Reason contains brackets: {reason}"
            assert f"Department mismatch between complaint text ({text_dept})" in reason
        print(f"  ✓ Row {idx:2d} passed: conflict={conflict} (expected={expected}) | text_dept={text_dept} | sec_dept={sec_dept} | cat={cat_name}")

    print("\n" + "=" * 80)
    print("ALL 12 MATRIX ROWS SUCCESSFULLY VERIFIED WITH detect_department_conflict!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_conflict_detection_from_detected_objects()
        test_12_matrix_rows_direct_helper()
    finally:
        cleanup_temp_images()

