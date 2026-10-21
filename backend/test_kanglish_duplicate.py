"""
Deterministic regression tests for Kanglish/Hinglish translation and duplicate detection.
Uses in-process TestClient with deterministic translation patching and real synthetic test images.
Includes an explicit live translation test skipped unless RUN_LIVE_TRANSLATION=1.
"""
import os
import sys
import random
from unittest.mock import patch

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
from backend.test_helpers import get_test_image_bytes, cleanup_temp_images

client = TestClient(app)
BASE_URL = "/api/v1"


def fake_translate(text: str):
    """Deterministic translation mock for offline Kanglish/Hinglish test stability."""
    text_clean = (text or "").strip()
    if "bada gaddha" in text_clean or "bahut khatarnak" in text_clean:
        return ("There is a very large and hazardous pothole on 100 Feet Road in Indiranagar.", "hi-en", 0.02)
    if "doddha gundi" in text_clean or "haalagide" in text_clean:
        return ("There is a large pothole and damaged road on Indiranagar 100ft road.", "kn-en", 0.02)
    return (text_clean, "en", 0.01)


def test_kanglish_hinglish_duplicate_detection():
    print("=" * 80)
    print("KANGLISH / HINGLISH TRANSLATION & DUPLICATE DETECTION VERIFICATION TEST")
    print("=" * 80)

    with patch("backend.app.routers.complaints.translate_text", side_effect=fake_translate), \
         patch("backend.app.services.duplicate.translate_text", side_effect=fake_translate), \
         patch("backend.app.services.evidence.evaluate_semantic_match", return_value=(
             "MATCH", 0.95, "Potholes & Damaged Roads", "Verified pothole match"
         )):

        # 1. Login as Citizen
        print("\n[Step 1] Logging in as Citizen...")
        login_res = client.post(f"{BASE_URL}/auth/login", data={
            "username": "citizen@gmail.com",
            "password": "citizenpassword"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate isolated test coordinates far from Bengaluru to guarantee zero collision with real DB complaints
        offset = random.uniform(0.01, 0.05)
        lat = round(21.1700 + offset, 6)
        lon = round(72.8300 + offset, 6)

        # Real synthetic images with distinct perceptual hashes
        img_bytes_1 = get_test_image_bytes(seed=201)
        img_bytes_2 = get_test_image_bytes(seed=202)

        # 2. File Complaint #1 in ENGLISH
        english_text = "Dangerous open pothole on Indiranagar 100ft road"
        print(f"\n[Step 2] Submitting Complaint #1 in ENGLISH...")
        print(f"  - Raw Input Text: '{english_text}'")

        files1 = {"file": ("test_en.jpg", img_bytes_1, "image/jpeg")}
        data1 = {
            "description": english_text,
            "language": "English",
            "location_latitude": lat,
            "location_longitude": lon,
            "location_address": "Indiranagar 100ft Road, Bengaluru"
        }

        res1 = client.post(f"{BASE_URL}/complaints", data=data1, files=files1, headers=headers)
        assert res1.status_code == 201, f"Complaint #1 creation failed: {res1.text}"
        c1 = res1.json()
        c1_id = c1["id"]
        print(f"✓ Complaint #{c1_id} created successfully.")
        print(f"  - Stored English Description: '{c1['description']}'")
        print(f"  - Category: '{c1['category_name']}'")

        # 3. File Complaint #2 in HINGLISH / KANGLISH nearby
        hinglish_text = "Indiranagar 100 feet road mein bahut bada gaddha hai, bahut khatarnak hai"
        print(f"\n[Step 3] Submitting Complaint #2 in HINGLISH / KANGLISH nearby...")
        print(f"  - Raw Input Text: '{hinglish_text}'")

        lat2 = round(lat + 0.0001, 6)  # ~11m away
        lon2 = round(lon + 0.0001, 6)

        files2 = {"file": ("test_hinglish.jpg", img_bytes_2, "image/jpeg")}
        data2 = {
            "description": hinglish_text,
            "language": "English",  # Often submitted as English in UI dropdown despite being Hinglish
            "location_latitude": lat2,
            "location_longitude": lon2,
            "location_address": "Indiranagar 100ft Road, Bengaluru"
        }

        res2 = client.post(f"{BASE_URL}/complaints", data=data2, files=files2, headers=headers)
        assert res2.status_code == 201, f"Complaint #2 creation failed: {res2.text}"
        c2 = res2.json()
        c2_id = c2["id"]

        print(f"\n[Step 4] Verifying Translation & Duplicate Auto-linking Results for Complaint #{c2_id}:")
        print(f"  - Raw Original Input: '{c2['original_description']}'")
        print(f"  - Translated Description (c2['description']): '{c2['description']}'")
        print(f"  - Detected Language: '{c2['detected_language']}'")
        print(f"  - Is Duplicate: {c2['is_duplicate']}")
        print(f"  - Linked Parent Complaint ID: {c2['duplicate_of_complaint_id']}")
        print(f"  - Parent Status: {c2['parent_status']}")
        print(f"  - Impact Count on Parent #{c1_id}: {c2['impact_count']}")

        # Assertions
        # A. Check that translated_text is NOT raw Hinglish
        assert c2["description"].strip() != hinglish_text.strip(), f"Expected translated text to be normalized English, but got raw text: {c2['description']}"
        assert any(word in c2["description"].lower() for word in ["pothole", "crater", "dangerous", "hazard"]), f"Expected translated text to contain English keywords, got: {c2['description']}"

        # B. Check that duplicate detection linked to c1
        assert c2["is_duplicate"] == True, f"Expected is_duplicate to be True, got {c2['is_duplicate']}"
        assert c2["duplicate_of_complaint_id"] == c1_id, f"Expected duplicate_of_complaint_id to be {c1_id}, got {c2['duplicate_of_complaint_id']}"
        assert c2["impact_count"] >= 2, f"Expected impact_count >= 2, got {c2['impact_count']}"

        # 5. Test direct /check-duplicate endpoint with Kanglish text
        kanglish_text = "Indiranagar 100ft rasteyalli doddha gundi ide, raste haalagide"
        print(f"\n[Step 5] Testing /check-duplicate endpoint with raw Kanglish text ('{kanglish_text}')...")
        check_dup_res = client.post(f"{BASE_URL}/complaints/check-duplicate", data={
            "latitude": lat2,
            "longitude": lon2,
            "description": kanglish_text,
            "category_name": c1["category_name"]
        }, headers=headers)

        assert check_dup_res.status_code == 200, f"Check duplicate failed: {check_dup_res.text}"
        dup_info = check_dup_res.json()
        print(f"✓ /check-duplicate Response:")
        print(f"  - is_duplicate: {dup_info['is_duplicate']}")
        print(f"  - parent_complaint_id: {dup_info['parent_complaint_id']}")
        print(f"  - similarity_score: {dup_info['similarity_score']}")

        assert dup_info["is_duplicate"] == True, f"Expected check-duplicate to return True, got {dup_info['is_duplicate']}"
        assert dup_info["similarity_score"] >= 0.85, f"Expected similarity_score >= 0.85, got {dup_info['similarity_score']}"

        print("\n" + "=" * 80)
        print("🎉 KANGLISH/HINGLISH TRANSLATION & DUPLICATE TEST PASSED SUCCESSFULLY!")
        print("=" * 80)


def test_live_translation_kanglish():
    print("\n" + "=" * 80)
    print("LIVE TRANSLATION SUITE (EXPLICIT OPT-IN VIA RUN_LIVE_TRANSLATION=1)")
    print("=" * 80)
    if os.environ.get("RUN_LIVE_TRANSLATION") != "1":
        print("  [SKIP] Skipping live translation test: RUN_LIVE_TRANSLATION != 1 (skipping external Gemini/Google network call).")
        return

    print("  [LIVE] Running live translation pipeline via translate_text...")
    from backend.app.services.ai import translate_text
    hinglish_text = "Indiranagar 100 feet road mein bahut bada gaddha hai, bahut khatarnak hai"
    translated, detected_lang, latency = translate_text(hinglish_text)
    print(f"  Live Translated: '{translated}' (lang: {detected_lang}, latency: {latency:.2f}s)")
    assert translated.strip() != hinglish_text.strip(), "Live translated text must not equal raw Hinglish"
    assert any(w in translated.lower() for w in ["pothole", "crater", "hole", "danger", "hazard", "severe"]), (
        f"Expected keywords in translated text, got: {translated}"
    )
    print("  ✓ PASS: Live translation verified successfully.")


if __name__ == "__main__":
    try:
        test_kanglish_hinglish_duplicate_detection()
        test_live_translation_kanglish()
    finally:
        cleanup_temp_images()
