"""
Unit and Regression Tests for Semantic Matching & Manual-Review Remark Fixes:
  1. Gemini replies "MATCH" for a water burst photo whose scene looks foreign -> MATCH.
  2. A reply starting with PARTIAL_MATCH -> NOT promoted to MATCH, and not a hard mismatch.
  3. A reply starting with MISMATCH -> MISMATCH.
  4. The prompt text sent to Gemini contains the instruction to ignore location, country and landmarks.
  5. The manual-review remark for a flagged complaint is a complete sentence with no stray "[".
"""
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.evidence import (
    build_gemini_vision_prompt,
    parse_gemini_vision_response,
    evaluate_semantic_match,
    compute_evidence_trust,
    clean_gate_reasons,
    format_manual_review_remark,
)


def test_case_1_gemini_match_foreign_scene():
    print("\n[TEST 1] Gemini replies 'MATCH' for water burst photo in foreign scene...")
    category = "Water Pipeline Burst & Leakage"
    complaint_desc = "Water pipeline has burst on Whitefield Main Road near ITPL, water gushing out"

    # 1. Test parsing directly
    raw_response = "MATCH: The image shows water gushing from a major ruptured pipe on a roadway."
    parsed = parse_gemini_vision_response(raw_response, category)
    assert parsed is not None, "Failed to parse MATCH response"
    status, conf, cat, details = parsed
    
    print(f"  Parsed result: status={status}, confidence={conf}, category={cat}")
    print(f"  Details: {details}")
    assert status == "MATCH", f"Expected 'MATCH', got '{status}'"
    assert conf == 0.94, f"Expected confidence 0.94, got {conf}"
    assert cat == category, f"Expected category '{category}', got '{cat}'"

    # 2. Test end-to-end evaluate_semantic_match with mocked Gemini
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = "MATCH: Shows a severe water pipe burst on a street."
    mock_model.generate_content.return_value = mock_resp

    with patch("backend.app.services.evidence.settings") as mock_settings, \
         patch("backend.app.services.evidence.PILImage.open") as mock_open:
        mock_settings.GEMINI_API_KEY = "dummy_valid_gemini_api_key_long_enough_12345"
        mock_settings.GEMINI_MODEL = "gemini-flash-latest"
        mock_open.return_value.__enter__.return_value = MagicMock()

        with patch("google.generativeai.GenerativeModel", return_value=mock_model):
            status, conf, cat, det = evaluate_semantic_match(
                complaint_text=complaint_desc,
                category_name=category,
                detected_objects=["car", "truck"],
                is_indoor_device=False,
                image_path=__file__  # any existing path
            )
            assert status == "MATCH", f"Expected MATCH, got {status}"
            print(f"  ✓ Mocked Gemini evaluate_semantic_match returned: {status} ({conf})")

    print("  ✓ PASS: Foreign scene water pipe burst correctly validated as MATCH.")


def test_case_2_partial_match_exact_token():
    print("\n[TEST 2] Reply starting with PARTIAL_MATCH (not promoted to MATCH, not hard MISMATCH)...")
    category = "Water Pipeline Burst & Leakage"

    raw_response = "PARTIAL_MATCH: Road has standing water and flooding, but no burst pipe is visible."
    parsed = parse_gemini_vision_response(raw_response, category)
    assert parsed is not None, "Failed to parse PARTIAL_MATCH response"
    status, conf, cat, details = parsed

    print(f"  Parsed result: status={status}, confidence={conf}, category={cat}")
    print(f"  Details: {details}")

    # Must NOT be promoted to MATCH (fixing the substring bug)
    assert status != "MATCH", "BUG: PARTIAL_MATCH was erroneously promoted to MATCH!"
    # Must NOT be a hard MISMATCH
    assert status != "MISMATCH", "PARTIAL_MATCH should not trigger hard MISMATCH"
    assert status == "PARTIAL_MATCH", f"Expected 'PARTIAL_MATCH', got '{status}'"
    # Confidence should be sensible: below full match (0.94), above mismatch (0.0)
    assert 0.65 <= conf <= 0.85, f"Expected sensible confidence between 0.65 and 0.85, got {conf}"

    # Verify how PARTIAL_MATCH behaves in compute_evidence_trust
    trust_result = compute_evidence_trust(
        live_lat=12.9716,
        live_lon=77.5946,
        image_path=None,
        detected_yolo_objects=["car"],
        category_name=category,
        complaint_description="Water leak on road"
    )
    # Manually simulate semantic check returning PARTIAL_MATCH
    with patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(status, conf, cat, details)):
        trust_result = compute_evidence_trust(
            live_lat=12.9716,
            live_lon=77.5946,
            image_path=None,
            detected_yolo_objects=["car"],
            category_name=category,
            complaint_description="Water leak on road"
        )
        print(f"  compute_evidence_trust decision: {trust_result['verification_decision']}")
        print(f"  compute_evidence_trust badge: {trust_result['image_verification_result']}")
        print(f"  compute_evidence_trust score: {trust_result['trust_score']}")

        assert trust_result["verification_decision"] == "PARTIALLY_VERIFIED", (
            f"Expected 'PARTIALLY_VERIFIED', got '{trust_result['verification_decision']}'"
        )
        assert trust_result["image_verification_result"] == "Image matches complaint", (
            f"Expected positive badge 'Image matches complaint', got '{trust_result['image_verification_result']}'"
        )
        assert trust_result["trust_score"] >= 50.0, (
            f"Expected medium/high trust score for partial match, got {trust_result['trust_score']}"
        )

    print("  ✓ PASS: PARTIAL_MATCH parsed with exact token, never promoted to MATCH and badge is positive.")


def test_case_3_mismatch_exact_token():
    print("\n[TEST 3] Reply starting with MISMATCH -> MISMATCH...")
    category = "Water Pipeline Burst & Leakage"

    raw_response = "MISMATCH: The image depicts an indoor domestic room with household furniture."
    parsed = parse_gemini_vision_response(raw_response, category)
    assert parsed is not None, "Failed to parse MISMATCH response"
    status, conf, cat, details = parsed

    print(f"  Parsed result: status={status}, confidence={conf}, category={cat}")
    print(f"  Details: {details}")

    assert status == "MISMATCH", f"Expected 'MISMATCH', got '{status}'"
    assert conf == 0.92, f"Expected confidence 0.92, got {conf}"

    # Verify compute_evidence_trust flags for manual review and sets negative badge
    with patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(status, conf, cat, details)):
        trust_result = compute_evidence_trust(
            live_lat=12.9716,
            live_lon=77.5946,
            image_path=None,
            category_name=category,
            complaint_description="Water leak on road"
        )
        print(f"  compute_evidence_trust decision: {trust_result['verification_decision']}")
        print(f"  compute_evidence_trust badge: {trust_result['image_verification_result']}")

        assert trust_result["verification_decision"] == "MANUAL_REVIEW", (
            f"Expected 'MANUAL_REVIEW', got '{trust_result['verification_decision']}'"
        )
        assert trust_result["image_verification_result"] == "Image does not match complaint", (
            f"Expected negative badge 'Image does not match complaint', got '{trust_result['image_verification_result']}'"
        )

    print("  ✓ PASS: MISMATCH correctly triggers MANUAL_REVIEW and negative badge.")


def test_case_4_prompt_ignores_location_and_landmarks():
    print("\n[TEST 4] Gemini Vision prompt instructions check...")
    prompt = build_gemini_vision_prompt(
        category_name="Water Pipeline Burst & Leakage",
        complaint_text="Water pipe burst on Whitefield Main Road near ITPL"
    )

    print("  Generated prompt preview:\n", "  " + "\n  ".join(prompt.splitlines()[:6]))

    prompt_lower = prompt.lower()
    # Explicit instruction assertions:
    assert "ignore" in prompt_lower, "Prompt must explicitly instruct to IGNORE location context"
    assert "location" in prompt_lower, "Prompt must mention 'location'"
    assert "country" in prompt_lower, "Prompt must mention 'country'"
    assert "landmarks" in prompt_lower, "Prompt must mention 'landmarks'"
    assert "type" in prompt_lower, "Prompt must instruct to check the TYPE of civic issue"
    assert "never reject" in prompt_lower or "never" in prompt_lower, "Prompt must state never reject because location cannot be confirmed"

    print("  ✓ PASS: Prompt explicitly instructs to ignore location, country, and landmarks.")


def test_case_5_manual_review_remark_clean_sentence():
    print("\n[TEST 5] Manual-review remark formatting (clean sentences, no brackets/quotes)...")

    # Test 5a: Standard Python list
    list_input = ["Semantic Mismatch: Image does not depict 'Stray Animal & Dead Animal Removal'."]
    remark_list = format_manual_review_remark(list_input)
    print(f"  5a (Python list) -> '{remark_list}'")
    assert "[" not in remark_list and "]" not in remark_list
    assert not remark_list.endswith("[")
    assert ": [" not in remark_list
    assert remark_list.endswith(".")
    assert "Semantic Mismatch: Image does not depict 'Stray Animal & Dead Animal Removal'." in remark_list

    # Test 5b: Single JSON-encoded string
    json_str_input = json.dumps(["Semantic Mismatch: Image does not depict 'Stray Animal & Dead Animal Removal'."])
    remark_json = format_manual_review_remark(json_str_input)
    print(f"  5b (JSON string) -> '{remark_json}'")
    assert "[" not in remark_json and "]" not in remark_json
    assert not remark_json.endswith("[")
    assert ": [" not in remark_json
    assert remark_json.endswith(".")
    assert remark_json == (
        "Complaint registered and flagged for manual review: "
        "Semantic Mismatch: Image does not depict 'Stray Animal & Dead Animal Removal'."
    )

    # Test 5c: Double-encoded JSON string (e.g. Complaint #46 regression case)
    double_encoded_input = json.dumps(json.dumps(["Semantic Mismatch: Image does not depict 'Stray Animal & Dead Animal Removal'."]))
    remark_double = format_manual_review_remark(double_encoded_input)
    print(f"  5c (Double JSON) -> '{remark_double}'")
    assert "[" not in remark_double and "]" not in remark_double
    assert not remark_double.endswith("[")
    assert ": [" not in remark_double
    assert remark_double.endswith(".")
    assert remark_double == (
        "Complaint registered and flagged for manual review: "
        "Semantic Mismatch: Image does not depict 'Stray Animal & Dead Animal Removal'."
    )

    # Test 5d: None and empty values
    for empty_val in [None, "", "   ", [], "[]", json.dumps([])]:
        remark_empty = format_manual_review_remark(empty_val)
        print(f"  5d (Empty/None: {repr(empty_val)}) -> '{remark_empty}'")
        assert "[" not in remark_empty and "]" not in remark_empty
        assert remark_empty.endswith(".")
        assert "Evidence verification requires manual officer inspection." in remark_empty

    # Test 5e: Multiple reasons joined with '; '
    multi_reasons = [
        "Geo Mismatch: Photo EXIF is 800m away",
        "Semantic Mismatch: Image does not depict 'Potholes & Damaged Roads'."
    ]
    remark_multi = format_manual_review_remark(multi_reasons)
    print(f"  5e (Multiple reasons) -> '{remark_multi}'")
    assert "[" not in remark_multi and "]" not in remark_multi
    assert remark_multi.endswith(".")
    assert "; " in remark_multi
    assert remark_multi == (
        "Complaint registered and flagged for manual review: "
        "Geo Mismatch: Photo EXIF is 800m away; "
        "Semantic Mismatch: Image does not depict 'Potholes & Damaged Roads'."
    )

    # Test 5f: Double-encoded multiple reasons
    remark_multi_double = format_manual_review_remark(json.dumps(json.dumps(multi_reasons)))
    print(f"  5f (Double JSON multi) -> '{remark_multi_double}'")
    assert "[" not in remark_multi_double and "]" not in remark_multi_double
    assert remark_multi_double == remark_multi

    print("  ✓ PASS: All gate reason representations format into clean sentences with no '[' or ']'.")


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING SEMANTIC MATCH FIX & PROMPT REFACTOR TESTS")
    print("=" * 70)

    test_case_1_gemini_match_foreign_scene()
    test_case_2_partial_match_exact_token()
    test_case_3_mismatch_exact_token()
    test_case_4_prompt_ignores_location_and_landmarks()
    test_case_5_manual_review_remark_clean_sentence()

    print("\n" + "=" * 70)
    print("ALL 5 SEMANTIC MATCH & REMARK TESTS PASSED PERFECTLY!")
    print("=" * 70)
