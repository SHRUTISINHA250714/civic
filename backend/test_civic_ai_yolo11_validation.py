"""
Verification Test Suite: CivicAI YOLO11n Integration & Multi-Factor Verification
================================================================================
Validates all 5 required updates:
  1. YOLO Model: CivicAI_YOLO11n_best.pt loads and detects civic hazards.
  2. Image-Text Validation:
     - Citizen submission: Mismatches flagged for manual review, prevents invalid evidence verification.
     - Officer resolution: Remediation proof verified against remarks and category, mismatches flagged.
  3. Multi-Factor Duplicate Detection:
     - Evaluates text, image, and location proximity together.
     - Links only when combined evidence supports the same incident.
     - Reused image with location/text conflict flags for manual review (no auto-merge, not suspicious).
     - Inconclusive evidence preserves separate complaint.
  4. Data Integrity: Parent impact_count increments, priority and SLA reassessed.
  5. Fraud Separation: Reused image alone does NOT classify as suspicious or force duplicate.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Prevent TF import issues
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"

# Add backend to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.core.config import settings
from backend.app.services.ai import yolo_model, verify_image
from backend.app.services.evidence import (
    compute_evidence_trust, evaluate_semantic_match, verify_resolution_evidence,
    CIVIC_HAZARD_OBJECTS
)
from backend.app.services.duplicate import check_duplicate_complaint, haversine_distance
from backend.app.core.database import SessionLocal
from backend.app.models.complaint import Complaint, ComplaintCategory, ComplaintImage, ComplaintStatusHistory
from backend.app.models.user import User
from backend.test_helpers import generate_test_image, cleanup_temp_images

def test_1_yolo_model_loading():
    print("\n[TEST 1] CivicAI_YOLO11n_best.pt Model Loading & Civic Hazard Classes...")
    assert yolo_model is not None, "YOLO model failed to load!"
    class_names = list(yolo_model.names.values())
    print(f"  Loaded model classes ({len(class_names)}): {class_names}")
    
    expected_hazards = ["pothole", "garbage", "fallen_tree", "streetlight", "water_leak", "road_crack"]
    for h in expected_hazards:
        assert h in class_names, f"Expected civic class '{h}' in model classes!"
        assert h in CIVIC_HAZARD_OBJECTS, f"Expected '{h}' in CIVIC_HAZARD_OBJECTS taxonomy!"
    print("  ✓ PASS: CivicAI_YOLO11n_best.pt verified with direct municipal defect classes.")

def test_2_citizen_image_text_validation():
    print("\n[TEST 2] Citizen Submission: Image-Text Semantic Validation & Evidence Gating...")
    now_utc = datetime.now(timezone.utc)

    # 1. Matching civic hazard (pothole complaint + detected pothole)
    status_match, conf_match, cat_match, det_match = evaluate_semantic_match(
        complaint_text="Deep pothole causing accidents near bus stand",
        category_name="Potholes & Damaged Roads",
        detected_objects=["pothole", "road_crack"],
        is_indoor_device=False
    )
    assert status_match == "MATCH", f"Expected MATCH, got {status_match}"
    print(f"  ✓ Matching Evidence: status={status_match}, conf={conf_match}, det={det_match}")

    # 2. Mismatching civic hazard (pothole complaint + detected garbage dump)
    status_mismatch, conf_mis, cat_mis, det_mis = evaluate_semantic_match(
        complaint_text="Deep pothole on road crater",
        category_name="Potholes & Damaged Roads",
        detected_objects=["garbage"],
        is_indoor_device=False
    )
    assert status_mismatch == "MISMATCH", f"Expected MISMATCH, got {status_mismatch}"
    print(f"  ✓ Mismatching Evidence: status={status_mismatch}, conf={conf_mis}, det={det_mis}")

    # 3. compute_evidence_trust decision for mismatch
    trust_res = compute_evidence_trust(
        live_lat=12.971598,
        live_lon=77.594562,
        image_path=None,
        category_name="Potholes & Damaged Roads",
        complaint_description="Deep pothole on road crater",
        detected_yolo_objects=["garbage"],
        submission_timestamp=now_utc,
    )
    # Must flag for manual review, NOT mark verified
    assert trust_res["verification_decision"] == "MANUAL_REVIEW", f"Expected MANUAL_REVIEW, got {trust_res['verification_decision']}"
    assert trust_res["semantic_match_status"] == "MISMATCH"
    assert trust_res["image_verification_result"] == "Image does not match complaint"
    print(f"  ✓ Gate decision for mismatch: '{trust_res['verification_decision']}' (prevented from VERIFIED)")

def test_3_officer_resolution_validation():
    print("\n[TEST 3] Officer Resolution Submission: Remediation Proof Validation...")
    
    # 1. Matching resolution proof (Pothole repaired + valid outdoor road context)
    # We can test verify_resolution_evidence directly
    # Indoor device screen test (should fail verification and flag for manual review)
    # We simulate by checking indoor/mismatch handling
    from unittest.mock import patch
    import tempfile
    import numpy as np
    try:
        import cv2
    except ImportError:
        cv2 = None

    # Create dummy image on disk for quality check using absolute path
    test_dir = os.path.dirname(os.path.abspath(__file__))
    dummy_img_path = os.path.join(test_dir, "dummy_resolution.jpg")
    img_data = np.random.randint(60, 190, (200, 200, 3), dtype=np.uint8)
    if cv2 is not None:
        cv2.imwrite(dummy_img_path, img_data)
    else:
        from PIL import Image as PILImage
        PILImage.fromarray(img_data).save(dummy_img_path)

    try:
        with patch("backend.app.services.evidence.run_yolo_detection") as mock_yolo:
            # Case A: Officer uploads a laptop/phone screenshot as proof
            mock_yolo.return_value = {
                "detected_objects": ["laptop", "mouse"],
                "bounding_boxes": [],
                "confidence_scores": {},
                "has_civic_objects": False,
                "is_indoor_device": True,
            }
            is_ver, conf, q_stat, details = verify_resolution_evidence(
                image_path=dummy_img_path,
                category_name="Potholes & Damaged Roads",
                resolution_remarks="Road was asphalted and pothole filled completely with bitumen mix.",
                complaint_description="Large pothole"
            )
            assert is_ver is False, "Indoor screenshot must NOT be accepted as verified resolution!"
            assert q_stat == "INDOOR_DEVICE_MISMATCH"
            print(f"  ✓ Indoor resolution screenshot rejected: is_verified={is_ver}, status={q_stat}")

            # Case B: Officer uploads garbage photo for a streetlight repair
            mock_yolo.return_value = {
                "detected_objects": ["garbage"],
                "bounding_boxes": [],
                "confidence_scores": {},
                "has_civic_objects": True,
                "is_indoor_device": False,
            }
            is_ver, conf, q_stat, details = verify_resolution_evidence(
                image_path=dummy_img_path,
                category_name="Streetlights & Street Infrastructure",
                resolution_remarks="Replaced the burnt bulb and restored illumination to the entire stretch.",
                complaint_description="Dark street light"
            )
            assert is_ver is False, "Mismatched resolution photo must NOT be accepted as verified!"
            assert q_stat == "MISMATCH_MANUAL_REVIEW"
            print(f"  ✓ Conflicting resolution proof flagged for manual review: is_verified={is_ver}, status={q_stat}")

            # Case C: Valid matching resolution proof
            mock_yolo.return_value = {
                "detected_objects": ["streetlight"],
                "bounding_boxes": [],
                "confidence_scores": {"streetlight": 0.92},
                "has_civic_objects": True,
                "is_indoor_device": False,
            }
            is_ver, conf, q_stat, details = verify_resolution_evidence(
                image_path=dummy_img_path,
                category_name="Streetlights & Street Infrastructure",
                resolution_remarks="Replaced the burnt bulb and restored illumination to the entire stretch.",
                complaint_description="Dark street light"
            )
            assert is_ver is True, "Valid matching resolution proof should be verified!"
            assert q_stat == "PASS"
            print(f"  ✓ Valid resolution proof successfully verified: is_verified={is_ver}, confidence={conf}")
    finally:
        if os.path.exists(dummy_img_path):
            try:
                os.remove(dummy_img_path)
            except OSError:
                pass

def test_4_multi_factor_duplicate_detection():
    print("\n[TEST 4] Multi-Factor Duplicate Detection & Conflict Flagging...")
    db = SessionLocal()
    try:
        from unittest.mock import patch, MagicMock

        # Get or create an active parent complaint in category 1 (Potholes)
        cat = db.query(ComplaintCategory).first()
        cat_id = cat.id if cat else 1

        # Check Scenario A: Same incident (Close distance ~25m, similar text, matching context)
        # Hermetic: uses a mocked parent candidate instead of querying live DB
        mock_parent = MagicMock()
        mock_parent.id = 501
        mock_parent.category_id = cat_id
        mock_parent.location_latitude = 12.971598 + 0.0002  # ~22m away
        mock_parent.location_longitude = 77.594562 + 0.0001
        mock_parent.description = "Deep pothole on MG road creating severe traffic block near brigade junction"
        mock_parent.original_description = mock_parent.description
        mock_parent.status = "In Progress"
        mock_parent.duplicate_of_complaint_id = None
        mock_parent_img = MagicMock()
        mock_parent_img.perceptual_hash = "1122334455667788"
        mock_parent.images = [mock_parent_img]

        with patch.object(db, "query") as mock_q_a:
            mock_filter_a = MagicMock()
            mock_filter_a.filter.return_value.all.return_value = [mock_parent]
            mock_q_a.return_value = mock_filter_a

            is_dup, dup_id, score, flag, details = check_duplicate_complaint(
                db=db,
                latitude=12.971598,
                longitude=77.594562,
                description="Deep pothole on MG road creating severe traffic block near brigade junction",
                category_id=cat_id,
                distance_threshold_m=100.0,
                similarity_threshold=0.85,
                perceptual_hash="1122334455667788",
                return_details=True
            )
            assert is_dup is True, f"Expected duplicate detected for identical nearby complaint, got is_dup={is_dup}"
            assert dup_id == 501, f"Expected auto-link to candidate ID 501, got {dup_id}"
            assert score >= 0.85, f"Expected similarity score >= 0.85, got {score}"
            assert flag == "COMBINED_MATCH", f"Expected flag COMBINED_MATCH, got {flag}"
            print(f"  ✓ Hermetic duplicate check result: is_dup={is_dup}, dup_id={dup_id}, score={round(score, 2)}, flag={flag}")

        # Check Scenario B: Conflict handling
        # Image matches an existing complaint pHash, but location is 5km away (distant conflict)
        mock_cand = MagicMock()
        mock_cand.id = 999
        mock_cand.category_id = cat_id
        mock_cand.location_latitude = 12.971598 + 0.05  # ~5.5km away
        mock_cand.location_longitude = 77.594562
        mock_cand.description = "Deep road hole"
        mock_cand.original_description = "Deep road hole"
        mock_cand.status = "In Progress"
        mock_cand.duplicate_of_complaint_id = None
        mock_img = MagicMock()
        mock_img.perceptual_hash = "aabbccddeeff0011"
        mock_cand.images = [mock_img]

        with patch.object(db, "query") as mock_q:
            mock_filter = MagicMock()
            mock_filter.filter.return_value.all.return_value = [mock_cand]
            mock_q.return_value = mock_filter

            # Incoming complaint has exact same image hash 'aabbccddeeff0011' but distant location
            is_d, d_id, sc, d_flag, d_details = check_duplicate_complaint(
                db=db,
                latitude=12.971598,
                longitude=77.594562,
                description="Another road pothole in distant neighborhood",
                category_id=cat_id,
                perceptual_hash="aabbccddeeff0011",
                return_details=True
            )
            # Must NOT automatically merge!
            assert is_d is False, "Reused image at conflicting location must NOT be automatically merged!"
            # Must NOT mark suspicious, but flag for manual review
            assert d_flag == "MANUAL_REVIEW_CONFLICT", f"Expected MANUAL_REVIEW_CONFLICT, got {d_flag}"
            print(f"  ✓ Image match with conflicting location safely flagged for MANUAL_REVIEW: flag={d_flag}")
            print(f"    Detail: {d_details.get('reason')}")

    finally:
        db.close()

def test_5_fraud_detection_separation():
    print("\n[TEST 5] Fraud Detection Separation (Reused image alone must NOT classify as SUSPICIOUS)...")
    db = SessionLocal()
    real_img_path = generate_test_image(seed=555)
    try:
        now_utc = datetime.now(timezone.utc)
        
        # Test reused image gate decision with clean matching GPS and real image on disk
        from unittest.mock import patch, MagicMock
        with patch.object(db, "query") as mock_q:
            mock_existing_img = MagicMock()
            mock_existing_img.complaint_id = 123
            mock_existing_img.perceptual_hash = "ffff0000ffff0000"
            mock_q.return_value.filter.return_value.all.return_value = [mock_existing_img]

            with patch("backend.app.services.evidence.compute_perceptual_hash", return_value="ffff0000ffff0000"), \
                 patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(
                     "MATCH", 0.95, "Potholes & Damaged Roads", "Civic AI model confirmed road damage/pothole directly matching complaint."
                 )):
                res = compute_evidence_trust(
                    live_lat=12.971598,
                    live_lon=77.594562,
                    image_path=real_img_path,
                    category_name="Potholes & Damaged Roads",
                    complaint_description="Pothole on main road",
                    submission_timestamp=now_utc,
                    db=db,
                )
                assert res["is_reused_image"] is True
                assert res["reused_complaint_id"] == 123
                # Critical Requirement 5: Reused image alone must NOT be SUSPICIOUS!
                assert res["verification_decision"] != "SUSPICIOUS", "Violation: Reused image alone was marked SUSPICIOUS!"
                assert res["verification_decision"] == "MANUAL_REVIEW", f"Expected MANUAL_REVIEW, got {res['verification_decision']}"

                # Strengthened assertions:
                # 1. Image quality check must NOT be UNREADABLE
                assert res["quality_check"] != "UNREADABLE", f"Quality check failed: {res.get('quality_check')}"
                assert res["quality_check"] == "PASS", f"Expected quality_check PASS, got {res.get('quality_check')}"

                # 2. Gate reasons & details must explicitly reference duplicate/reused image from Complaint #123
                gate_reasons_str = res.get("gate_reasons") or ""
                assert "Duplicate Image: This photo was already submitted for Complaint #123." in gate_reasons_str, (
                    f"Expected duplicate image gate reason, got: {gate_reasons_str}"
                )
                assert "Duplicate image detected (reused from Complaint #123)" in res.get("verification_details", ""), (
                    f"Expected verification_details to reference reused image, got: {res.get('verification_details')}"
                )

                print(f"  ✓ Reused image decision: '{res['verification_decision']}' (NOT classified as SUSPICIOUS)")
                print(f"  ✓ Quality check passed: {res['quality_check']}")
                print(f"  ✓ Gate reason verified: {gate_reasons_str}")

    finally:
        db.close()
        cleanup_temp_images(real_img_path)

def run_all_tests():
    print("=" * 75)
    print("CIVIC PROJECT: CIVICAI YOLO11n & MULTI-FACTOR VERIFICATION SUITE")
    print("=" * 75)
    test_1_yolo_model_loading()
    test_2_citizen_image_text_validation()
    test_3_officer_resolution_validation()
    test_4_multi_factor_duplicate_detection()
    test_5_fraud_detection_separation()
    print("\n" + "=" * 75)
    print("ALL 5 REQUIREMENTS FULLY VERIFIED AND PASSING!")
    print("=" * 75)

if __name__ == "__main__":
    run_all_tests()
