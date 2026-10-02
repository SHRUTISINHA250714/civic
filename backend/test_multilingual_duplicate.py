import sys
import os
import requests
import json
import random

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_multilingual_duplicate_detection():
    print("=" * 75)
    print("MULTILINGUAL DUPLICATE DETECTION VERIFICATION TEST")
    print("=" * 75)

    # 1. Login as Citizen
    print("\n[Step 1] Logging in as Citizen...")
    login_res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "citizen@gmail.com",
        "password": "citizenpassword"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate fresh random test location in Indiranagar, Bengaluru to avoid old test DB rows
    offset = random.uniform(0.01, 0.05)
    lat = round(12.9784 + offset, 6)
    lon = round(77.6408 + offset, 6)

    # Dummy image header
    dummy_img = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9'

    # 2. File Complaint #1 in ENGLISH
    english_text = "Dangerous open pothole and severe road crater near Indiranagar 100ft road causing heavy traffic hazard"
    print(f"\n[Step 2] Submitting Complaint #1 in ENGLISH...")
    print(f"  - Raw Text: '{english_text}'")
    
    files1 = {"file": ("test_en.jpg", dummy_img, "image/jpeg")}
    data1 = {
        "description": english_text,
        "language": "English",
        "location_latitude": lat,
        "location_longitude": lon,
        "location_address": "Indiranagar 100ft Road, Bengaluru"
    }

    res1 = requests.post(f"{BASE_URL}/complaints", data=data1, files=files1, headers=headers)
    assert res1.status_code == 201, f"Complaint #1 creation failed: {res1.text}"
    c1 = res1.json()
    c1_id = c1["id"]
    print(f"✓ Complaint #{c1_id} created successfully.")
    print(f"  - Stored English Description: '{c1['description']}'")
    print(f"  - Stored Original Description: '{c1['original_description']}'")
    print(f"  - Category: '{c1['category_name']}'")

    # 3. File Complaint #2 in KANNADA about the EXACT same issue at nearby location
    kannada_text = "ಇಂದಿರಾ ನಗರ 100 ಅಡಿ ರಸ್ತೆಯಲ್ಲಿ ದೊಡ್ಡ ಗುಂಡಿ ಬಿದ್ದಿದೆ ಮತ್ತು ರಸ್ತೆ ಹಾಳಾಗಿದೆ ಅಪಾಯಕಾರಿ"
    print(f"\n[Step 3] Submitting Complaint #2 in KANNADA about the SAME issue nearby...")
    print(f"  - Raw Text: '{kannada_text}'")

    lat2 = round(lat + 0.0001, 6) # ~11m offset (well within 100m radius)
    lon2 = round(lon + 0.0001, 6)

    files2 = {"file": ("test_kn.jpg", dummy_img, "image/jpeg")}
    data2 = {
        "description": kannada_text,
        "language": "Kannada",
        "location_latitude": lat2,
        "location_longitude": lon2,
        "location_address": "Indiranagar 100ft Road, Bengaluru"
    }

    res2 = requests.post(f"{BASE_URL}/complaints", data=data2, files=files2, headers=headers)
    assert res2.status_code == 201, f"Complaint #2 creation failed: {res2.text}"
    c2 = res2.json()
    c2_id = c2["id"]

    print(f"\n[Step 4] Verifying Duplicate Auto-linking Results for Complaint #{c2_id}:")
    print(f"  - Translated Description of C2: '{c2['description']}'")
    print(f"  - Is Duplicate: {c2['is_duplicate']}")
    print(f"  - Linked Parent Complaint ID: {c2['duplicate_of_complaint_id']}")
    print(f"  - Parent Complaint Status: {c2['parent_status']}")
    print(f"  - Impact Count on Parent #{c1_id}: {c2['impact_count']}")

    # 5. Assertions
    assert c2["is_duplicate"] == True, f"Expected is_duplicate to be True, got {c2['is_duplicate']}"
    assert c2["duplicate_of_complaint_id"] == c1_id, f"Expected duplicate_of_complaint_id to be {c1_id}, got {c2['duplicate_of_complaint_id']}"
    assert c2["impact_count"] >= 2, f"Expected impact_count >= 2, got {c2['impact_count']}"

    # 6. Test direct /check-duplicate endpoint with raw Kannada text
    print(f"\n[Step 5] Testing /check-duplicate endpoint with raw Kannada text...")
    check_dup_res = requests.post(f"{BASE_URL}/complaints/check-duplicate", data={
        "latitude": lat2,
        "longitude": lon2,
        "description": kannada_text,
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

    print("\n" + "=" * 75)
    print("🎉 MULTILINGUAL DUPLICATE DETECTION TEST COMPLETED & PASSED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    test_multilingual_duplicate_detection()
