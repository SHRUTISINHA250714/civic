import sys
import os
import requests
import json
import random

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_kanglish_hinglish_duplicate_detection():
    print("=" * 80)
    print("KANGLISH / HINGLISH TRANSLATION & DUPLICATE DETECTION VERIFICATION TEST")
    print("=" * 80)

    # 1. Login as Citizen
    print("\n[Step 1] Logging in as Citizen...")
    login_res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "citizen@gmail.com",
        "password": "citizenpassword"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate isolated test location in Indiranagar
    offset = random.uniform(0.01, 0.05)
    lat = round(12.9784 + offset, 6)
    lon = round(77.6408 + offset, 6)

    dummy_img = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9'

    # 2. File Complaint #1 in ENGLISH
    english_text = "Dangerous open pothole on Indiranagar 100ft road"
    print(f"\n[Step 2] Submitting Complaint #1 in ENGLISH...")
    print(f"  - Raw Input Text: '{english_text}'")

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
    print(f"  - Category: '{c1['category_name']}'")

    # 3. File Complaint #2 in HINGLISH / KANGLISH nearby
    hinglish_text = "Indiranagar 100 feet road mein bahut bada gaddha hai, bahut khatarnak hai"
    print(f"\n[Step 3] Submitting Complaint #2 in HINGLISH / KANGLISH nearby...")
    print(f"  - Raw Input Text: '{hinglish_text}'")

    lat2 = round(lat + 0.0001, 6)  # ~11m away
    lon2 = round(lon + 0.0001, 6)

    files2 = {"file": ("test_hinglish.jpg", dummy_img, "image/jpeg")}
    data2 = {
        "description": hinglish_text,
        "language": "English",  # Often submitted as English in UI dropdown despite being Hinglish
        "location_latitude": lat2,
        "location_longitude": lon2,
        "location_address": "Indiranagar 100ft Road, Bengaluru"
    }

    res2 = requests.post(f"{BASE_URL}/complaints", data=data2, files=files2, headers=headers)
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
    check_dup_res = requests.post(f"{BASE_URL}/complaints/check-duplicate", data={
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

if __name__ == "__main__":
    test_kanglish_hinglish_duplicate_detection()
