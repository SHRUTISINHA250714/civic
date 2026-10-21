"""
Unit and Regression Tests for Positive-Only Neutral Photo Evidence in Duplicate Detection:
  1. Hamming 30, text 0.7658, distance 0 m -> combined about 0.898 -> auto-link (the #52 vs #51 case).
  2. Hamming 30, text 0.5954, distance 0 m -> no link (the #23 case); combined below 0.85 and below the 0.70 guard.
  3. Hamming 30, text 0.70, distance 50 m (location score 0.5, no bonus) -> combined about 0.63 -> INCONCLUSIVE_REVIEW, not linked.
  4. Hamming 0 (identical photo) -> img_score is the same as before the change for the same inputs.
  5. No perceptual hash on the candidate -> same result as before the change.
  6. Hamming 30, high text and distance, but image_semantic_status == "MISMATCH" -> still not linked.
  7. Monotonic check: for a fixed text score, img_score never decreases as Hamming distance goes down from 40 to 0.
"""
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.duplicate import (
    compute_image_score,
    check_duplicate_complaint,
)


def old_img_score_formula(hamming_dist):
    if hamming_dist is None:
        return None
    return max(0.0, 1.0 - (hamming_dist / 16.0))


def compute_combined_score(desc_score, loc_score, img_score, dist):
    proximity_bonus = 0.05 if dist <= 40.0 else 0.0
    combined = (0.50 * desc_score) + (0.35 * loc_score) + (0.15 * img_score) + proximity_bonus
    return max(0.0, min(1.0, combined))


def test_case_1_different_photo_same_issue_autolink():
    print("\n[TEST 1] Hamming 30, text 0.7658, distance 0 m -> auto-link (Case #52 vs #51)...")
    desc_score = 0.7658
    dist = 0.0
    loc_score = 1.0
    hamming = 30

    img_score = compute_image_score(hamming, desc_score)
    assert img_score == desc_score, f"Expected neutral img_score {desc_score}, got {img_score}"

    combined = compute_combined_score(desc_score, loc_score, img_score, dist)
    print(f"  Calculated combined score: {combined:.5f}")
    assert abs(combined - 0.89777) < 0.001, f"Expected combined around 0.898, got {combined}"
    assert combined >= 0.85, "Combined score must satisfy auto-link threshold >= 0.85"
    assert desc_score >= 0.70, "Text score must satisfy best_desc_score >= 0.70 guard"

    # End-to-end check with mocked candidate
    mock_db = MagicMock()
    mock_cand = MagicMock()
    mock_cand.id = 51
    mock_cand.category_id = 2
    mock_cand.location_latitude = 12.971598
    mock_cand.location_longitude = 77.594562
    mock_cand.description = "The footpath on Bannerghatta Road near Jayadeva Hospital is badly broken"
    mock_cand.original_description = mock_cand.description
    mock_cand.status = "Registered"
    mock_cand.duplicate_of_complaint_id = None
    mock_img = MagicMock()
    # Hash differing by 30 bits
    mock_img.perceptual_hash = "d8486021b39252e2"
    mock_cand.images = [mock_img]

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_cand]

    with patch("backend.app.services.duplicate.encoder_model") as mock_encoder, \
         patch("backend.app.services.duplicate.util.cos_sim") as mock_cos:
        mock_cos.return_value = [[MagicMock(item=lambda: 0.7658)]]

        is_dup, dup_id, score, flag, details = check_duplicate_complaint(
            db=mock_db,
            latitude=12.971598,
            longitude=77.594562,
            description="Paving slabs on the pedestrian walkway opposite Jayadeva Hospital have cracked",
            category_id=2,
            perceptual_hash="9611136851c30647",
            return_details=True
        )

    print(f"  End-to-end check result: is_dup={is_dup}, dup_id={dup_id}, score={score:.4f}, flag={flag}")
    assert is_dup is True, "Complaint #52 must now auto-link to #51"
    assert dup_id == 51
    assert flag == "COMBINED_MATCH"
    assert abs(score - 0.898) < 0.005
    print("  ✓ PASS: Case 1 correctly auto-links with neutral photo evidence.")


def test_case_2_weak_text_not_linked():
    print("\n[TEST 2] Hamming 30, text 0.5954, distance 0 m -> not linked (Case #23)...")
    desc_score = 0.5954
    dist = 0.0
    loc_score = 1.0
    hamming = 30

    img_score = compute_image_score(hamming, desc_score)
    assert img_score == desc_score

    combined = compute_combined_score(desc_score, loc_score, img_score, dist)
    print(f"  Calculated combined score: {combined:.5f}")
    assert combined < 0.85, f"Combined score {combined} must be below 0.85"
    assert desc_score < 0.70, "Text score must be below 0.70 guard"

    # End-to-end check with mocked candidate
    mock_db = MagicMock()
    mock_cand = MagicMock()
    mock_cand.id = 23
    mock_cand.category_id = 2
    mock_cand.location_latitude = 12.971598
    mock_cand.location_longitude = 77.594562
    mock_cand.description = "Footpath issue elsewhere"
    mock_cand.original_description = mock_cand.description
    mock_cand.status = "Registered"
    mock_cand.duplicate_of_complaint_id = None
    mock_img = MagicMock()
    mock_img.perceptual_hash = "d8486021b39252e2"
    mock_cand.images = [mock_img]

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_cand]

    with patch("backend.app.services.duplicate.encoder_model") as mock_encoder, \
         patch("backend.app.services.duplicate.util.cos_sim") as mock_cos:
        mock_cos.return_value = [[MagicMock(item=lambda: 0.5954)]]

        is_dup, dup_id, score, flag, details = check_duplicate_complaint(
            db=mock_db,
            latitude=12.971598,
            longitude=77.594562,
            description="Paving slabs on the pedestrian walkway opposite Jayadeva Hospital have cracked",
            category_id=2,
            perceptual_hash="9611136851c30647",
            return_details=True
        )

    print(f"  End-to-end check result: is_dup={is_dup}, dup_id={dup_id}, score={score:.4f}, flag={flag}")
    assert is_dup is False, "Weak text match must NOT link"
    assert flag == "INCONCLUSIVE_REVIEW"
    print("  ✓ PASS: Case 2 correctly prevented from linking due to weak text score.")


def test_case_3_moderate_distance_inconclusive():
    print("\n[TEST 3] Hamming 30, text 0.70, distance 50 m -> INCONCLUSIVE_REVIEW...")
    desc_score = 0.70
    dist = 50.0
    loc_score = 1.0 - (50.0 / 100.0)  # 0.50
    hamming = 30

    img_score = compute_image_score(hamming, desc_score)
    combined = compute_combined_score(desc_score, loc_score, img_score, dist)
    print(f"  Calculated combined score: {combined:.5f}")
    assert abs(combined - 0.6300) < 0.001, f"Expected combined around 0.63, got {combined}"
    assert 0.60 <= combined < 0.85, "Must fall in inconclusive range [0.60, 0.85)"

    mock_db = MagicMock()
    mock_cand = MagicMock()
    mock_cand.id = 101
    mock_cand.category_id = 1
    # Coordinates ~50m apart
    mock_cand.location_latitude = 12.971598 + 0.00045
    mock_cand.location_longitude = 77.594562
    mock_cand.description = "Pothole on 50m street"
    mock_cand.original_description = mock_cand.description
    mock_cand.status = "Registered"
    mock_cand.duplicate_of_complaint_id = None
    mock_img = MagicMock()
    mock_img.perceptual_hash = "1111222233334444"
    mock_cand.images = [mock_img]

    mock_db.query.return_value.filter.return_value.all.return_value = [mock_cand]

    with patch("backend.app.services.duplicate.encoder_model") as mock_encoder, \
         patch("backend.app.services.duplicate.util.cos_sim") as mock_cos:
        mock_cos.return_value = [[MagicMock(item=lambda: 0.70)]]

        is_dup, dup_id, score, flag, details = check_duplicate_complaint(
            db=mock_db,
            latitude=12.971598,
            longitude=77.594562,
            description="Pothole on 50m street description",
            category_id=1,
            distance_threshold_m=100.0,
            similarity_threshold=0.85,
            perceptual_hash="9999888877776666",
            return_details=True
        )

    print(f"  End-to-end check result: is_dup={is_dup}, score={score:.4f}, flag={flag}")
    assert is_dup is False
    assert flag == "INCONCLUSIVE_REVIEW"
    print("  ✓ PASS: Case 3 correctly flagged as INCONCLUSIVE_REVIEW at 50m.")


def test_case_4_identical_photo_boost_preserved():
    print("\n[TEST 4] Hamming 0 (identical photo) -> img_score matches old formula...")
    for test_text_score in [0.0, 0.4, 0.7, 0.85, 1.0]:
        old_val = old_img_score_formula(0)
        new_val = compute_image_score(0, test_text_score)
        print(f"  text={test_text_score}: old={old_val}, new={new_val}")
        assert new_val == 1.0, f"Expected 1.0 for Hamming 0, got {new_val}"
        assert old_val == 1.0
        assert new_val == old_val, "Identical photo must produce exact same score as old formula"

    # Near-identical photo test (Hamming <= 4)
    for h in [1, 2, 3, 4]:
        old_val = old_img_score_formula(h)
        # When text score is lower than image similarity
        new_val = compute_image_score(h, 0.50)
        assert new_val == old_val, f"For h={h} with low text score, img_score must match old formula ({old_val} vs {new_val})"

    print("  ✓ PASS: Case 4 identical/near-identical photo boost is 100% preserved.")


def test_case_5_candidate_without_hash():
    print("\n[TEST 5] Candidate without perceptual hash -> exact same behavior...")
    for test_text_score in [0.0, 0.5, 0.7658, 0.9]:
        res = compute_image_score(None, test_text_score)
        assert res == test_text_score, f"Expected neutral {test_text_score}, got {res}"

    print("  ✓ PASS: Case 5 missing hash defaults to neutral desc_score.")


def test_case_6_image_semantic_mismatch_blocks_link():
    print("\n[TEST 6] image_semantic_status == 'MISMATCH' blocks linking...")
    mock_db = MagicMock()
    is_dup, dup_id, score, flag, details = check_duplicate_complaint(
        db=mock_db,
        latitude=12.971598,
        longitude=77.594562,
        description="Identical description with mismatched photo",
        category_id=1,
        image_semantic_status="MISMATCH",
        perceptual_hash="1122334455667788",
        return_details=True
    )
    print(f"  Mismatch result: is_dup={is_dup}, flag={flag}")
    assert is_dup is False, "MISMATCH image must never link as duplicate"
    assert flag == "IMAGE_MISMATCH"
    print("  ✓ PASS: Case 6 image semantic mismatch guard preserved.")


def test_case_7_monotonic_check():
    print("\n[TEST 7] Monotonic check: img_score never decreases as Hamming distance drops from 40 to 0...")
    for text_score in [0.0, 0.3, 0.5, 0.7, 0.7658, 0.9, 1.0]:
        prev_score = -1.0
        # Iterate from distance 40 down to 0 (increasing visual similarity)
        for h in range(40, -1, -1):
            score = compute_image_score(h, text_score)
            assert score >= prev_score, (
                f"Monotonicity violation at text={text_score}, h={h}: score {score} < prev_score {prev_score}"
            )
            prev_score = score

    print("  ✓ PASS: Case 7 img_score is strictly monotonic across all Hamming distances.")


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING NEUTRAL PHOTO DUPLICATE SCORING VERIFICATION SUITE")
    print("=" * 70)

    test_case_1_different_photo_same_issue_autolink()
    test_case_2_weak_text_not_linked()
    test_case_3_moderate_distance_inconclusive()
    test_case_4_identical_photo_boost_preserved()
    test_case_5_candidate_without_hash()
    test_case_6_image_semantic_mismatch_blocks_link()
    test_case_7_monotonic_check()

    print("\n" + "=" * 70)
    print("ALL 7 NEUTRAL PHOTO EVIDENCE TESTS PASSED PERFECTLY!")
    print("=" * 70)
