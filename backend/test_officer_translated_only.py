import sys
import os
import requests
import json
import random
import re

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_officer_translated_only():
    print("=" * 75)
    print("OFFICER DASHBOARD TRANSLATED-ONLY TEXT VERIFICATION TEST")
    print("=" * 75)

    # 1. Login as Citizen
    print("\n[Step 1] Logging in as Citizen...")
    login_res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "citizen@gmail.com",
        "password": "citizenpassword"
    })
    assert login_res.status_code == 200, f"Citizen login failed: {login_res.text}"
    citizen_token = login_res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("✓ Citizen login successful.")

    # 2. Login as Officer
    print("\n[Step 2] Logging in as Officer...")
    officer_login_res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "officer.bbmp@civicai.gov.in",
        "password": "officerpassword"
    })
    assert officer_login_res.status_code == 200, f"Officer login failed: {officer_login_res.text}"
    officer_token = officer_login_res.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    print("✓ Officer login successful.")

    # Generate random test location
    lat = round(12.9784 + random.uniform(0.1, 0.5), 6)
    lon = round(77.6408 + random.uniform(0.1, 0.5), 6)
    dummy_img = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xd9'

    # 3. Submit a Kannada complaint
    kannada_text = "ಇಂದಿರಾ ನಗರ ರಸ್ತೆಯಲ್ಲಿ ದೊಡ್ಡ ಗುಂಡಿ ಬಿದ್ದಿದೆ"
    print(f"\n[Step 3] Submitting Kannada complaint as Citizen: '{kannada_text}'...")
    files1 = {"file": ("test_kn.jpg", dummy_img, "image/jpeg")}
    data1 = {
        "description": kannada_text,
        "language": "Kannada",
        "location_latitude": lat,
        "location_longitude": lon,
        "location_address": "Indiranagar, Bengaluru"
    }
    c_res = requests.post(f"{BASE_URL}/complaints", data=data1, files=files1, headers=citizen_headers)
    assert c_res.status_code == 201, f"Complaint creation failed: {c_res.text}"
    c1 = c_res.json()
    c1_id = c1["id"]
    print(f"✓ Complaint #{c1_id} created.")
    print(f"  - Citizen API payload description: '{c1.get('description')}'")
    print(f"  - Citizen API payload original_description: '{c1.get('original_description')}'")
    
    # Assert Citizen API preserves original_description
    assert c1.get("original_description") == kannada_text, f"Citizen original_description mismatch: {c1.get('original_description')}"

    # 4. Fetch complaints as Officer
    print(f"\n[Step 4] Fetching complaint #{c1_id} as Officer...")
    off_c_res = requests.get(f"{BASE_URL}/complaints/{c1_id}", headers=officer_headers)
    assert off_c_res.status_code == 200, f"Officer GET complaint failed: {off_c_res.text}"
    off_c1 = off_c_res.json()

    print(f"  - Officer API payload description: '{off_c1.get('description')}'")
    print(f"  - Officer API payload original_description: {off_c1.get('original_description')}")

    # VERIFY OFFICER REQUIREMENTS:
    # 1. original_description MUST BE None for Officer
    assert off_c1.get("original_description") is None, (
        f"Security Failure: original_description exposed to officer! Value: {off_c1.get('original_description')}"
    )

    # 2. description MUST NOT contain raw Kannada script characters (\u0C80-\u0CFF)
    desc_val = off_c1.get("description", "")
    has_kannada_script = bool(re.search(r'[\u0C80-\u0CFF]', desc_val))
    assert not has_kannada_script, (
        f"Validation Failure: Raw Kannada script exposed in officer description: '{desc_val}'"
    )

    # 3. description must either be translated English or fallback to 'Translation unavailable'
    assert desc_val != "", "Description should not be empty"
    print(f"✓ VERIFIED: Officer receives translated text / fallback without raw script or original_description.")

    # 5. Fetch Officer Complaint List
    print(f"\n[Step 5] Fetching GET /complaints list as Officer...")
    off_list_res = requests.get(f"{BASE_URL}/complaints", headers=officer_headers)
    assert off_list_res.status_code == 200, f"Officer list failed: {off_list_res.text}"
    off_list = off_list_res.json()
    
    # Check all complaints in officer list
    for comp in off_list:
        assert comp.get("original_description") is None, f"Complaint #{comp['id']} exposed original_description to officer"
        d = comp.get("description", "")
        assert not re.search(r'[\u0C80-\u0CFF]', d), f"Complaint #{comp['id']} exposed raw Kannada script to officer"

    print("✓ VERIFIED: Entire officer list contains zero raw script and zero original_description.")
    print("\n" + "=" * 75)
    print("ALL TEST CASES PASSED SUCCESSFULLY! 🚀")
    print("=" * 75)

if __name__ == "__main__":
    test_officer_translated_only()
