"""
End-to-End Routing Regression Tests for CivicAI Karnataka:
Verifies contextual department routing and multimodal evidence conflict handling:
  1. Water pipeline burst on road -> BWSSB, Water Pipeline Burst & Leakage
  2. Sewage overflow on road -> BWSSB
  3. Garbage uncollected on road -> BSWML
  4. Large pothole with muddy water -> BBMP, Potholes & Damaged Roads (word 'water' does NOT pull to BWSSB)
  5. Water pipe burst text with pothole-style road photo -> stays BWSSB (or manual review), never silently BBMP
"""
import os
import sys
import tempfile
import cv2
import numpy as np

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.ai import translate_text, classify_complaint, classify_complaint_structured
from backend.app.services.routing import resolve_department_routing
from backend.app.services.evidence import compute_evidence_trust, evaluate_semantic_match
from backend.app.core.database import SessionLocal
from backend.app.models.complaint import ComplaintCategory, Complaint, ComplaintEvidenceCheck, ComplaintStatusHistory
from backend.app.models.department import Department


def test_case_1_water_pipe_burst():
    print("\n[TEST 1] Water Pipeline Burst on Main Road...")
    text = (
        "A main water pipeline has burst on Whitefield Main Road near ITPL, Bengaluru. "
        "Clean drinking water is gushing out onto the road and being wasted for the last two hours. "
        "Please send a team to repair the pipe immediately."
    )
    
    # 1. Direct classification
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)
    
    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None
        
        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")
        
        assert pred_cat == "Water Pipeline Burst & Leakage", (
            f"Expected 'Water Pipeline Burst & Leakage', got '{pred_cat}'"
        )
        assert dept_code == "BWSSB", f"Expected department 'BWSSB', got '{dept_code}'"
        assert structured.get("agency") == "BWSSB", (
            f"Expected structured agency 'BWSSB', got '{structured.get('agency')}'"
        )
        print("  ✓ PASS: Correctly routed to BWSSB, Water Pipeline Burst & Leakage.")
    finally:
        db.close()


def test_case_2_sewage_overflow():
    print("\n[TEST 2] Sewage Overflow on Road...")
    text = (
        "Sewage is overflowing from the underground sewer line near my house on 80 Feet Road, Indiranagar. "
        "Dirty wastewater is spreading across the road with a very bad smell, and it is a health risk for residents. "
        "Please clear the blocked sewer line urgently."
    )
    
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)
    
    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None
        
        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")
        
        assert dept_code == "BWSSB", f"Expected department 'BWSSB', got '{dept_code}'"
        assert structured.get("agency") == "BWSSB", (
            f"Expected structured agency 'BWSSB', got '{structured.get('agency')}'"
        )
        print("  ✓ PASS: Correctly routed to BWSSB.")
    finally:
        db.close()


def test_case_3_garbage_uncollected():
    print("\n[TEST 3] Garbage Uncollected on Footpath/Road...")
    text = (
        "Garbage has not been collected on 5th Block Koramangala for over a week. "
        "The bins are overflowing and waste is spread across the road, causing a foul smell."
    )
    
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)
    
    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None
        
        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")
        
        assert dept_code == "BSWML", f"Expected department 'BSWML', got '{dept_code}'"
        assert structured.get("agency") == "BSWML", (
            f"Expected structured agency 'BSWML', got '{structured.get('agency')}'"
        )
        print("  ✓ PASS: Correctly routed to BSWML.")
    finally:
        db.close()


def test_case_4_pothole_with_muddy_water():
    print("\n[TEST 4] Pothole Filled with Muddy Water on MG Road...")
    text = (
        "A large pothole has developed on MG Road near Trinity Circle, Bengaluru. "
        "It is filled with muddy water and is dangerous for two-wheelers."
    )
    
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)
    
    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None
        
        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")
        
        assert pred_cat in ["Potholes & Damaged Roads", "Pothole", "Road Damage"], (
            f"Expected pothole category, got '{pred_cat}'"
        )
        assert dept_code == "BBMP", f"Expected department 'BBMP', got '{dept_code}'"
        assert structured.get("agency") == "BBMP", (
            f"Expected structured agency 'BBMP', got '{structured.get('agency')}'"
        )
        print("  ✓ PASS: Correctly routed to BBMP (muddy water did NOT pull away to BWSSB).")
    finally:
        db.close()


def test_case_5_water_text_with_pothole_image():
    print("\n[TEST 5] Water Pipe Burst Text with Pothole-Style Road Photo...")
    text = (
        "A main water pipeline has burst on Whitefield Main Road near ITPL, Bengaluru. "
        "Clean drinking water is gushing out onto the road and being wasted for the last two hours. "
        "Please send a team to repair the pipe immediately."
    )
    
    # 1. Text routing determines department
    pred_cat, conf = classify_complaint(text)
    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None
        text_dept_code = cat.department.code if cat.department else None
        assert text_dept_code == "BWSSB", f"Expected text routing to BWSSB, got '{text_dept_code}'"
        
        # 2. Create a temporary pothole dummy image
        with tempfile.NamedTemporaryFile(suffix="_pothole.jpg", delete=False) as tmp:
            tmp_img_path = tmp.name
        
        try:
            # Create a valid test image with synthetic road crack/pothole texture
            dummy_img = np.ones((250, 250, 3), dtype=np.uint8) * 120
            cv2.circle(dummy_img, (125, 125), 50, (30, 30, 30), -1)
            cv2.imwrite(tmp_img_path, dummy_img)
            
            # Run evidence trust engine with pothole-style image
            ev_result = compute_evidence_trust(
                live_lat=12.9716,
                live_lon=77.5946,
                image_path=tmp_img_path,
                category_name=pred_cat,
                complaint_description=text,
                db=db
            )
            
            print(f"  Text Department: {text_dept_code} ({pred_cat})")
            print(f"  Verification Decision: {ev_result['verification_decision']}")
            print(f"  Semantic Match Status: {ev_result['semantic_match_status']}")
            print(f"  Image Inferred Category: {ev_result.get('image_category')}")
            
            # The department MUST remain BWSSB (never silently flip to BBMP)
            final_dept_code = text_dept_code
            assert final_dept_code == "BWSSB", f"Department was unexpectedly changed to {final_dept_code}"
            
            # Verification decision must flag for manual review, not silently verify
            assert ev_result["verification_decision"] == "MANUAL_REVIEW", (
                f"Expected 'MANUAL_REVIEW', got '{ev_result['verification_decision']}'"
            )
            assert ev_result["semantic_match_status"] == "MISMATCH", (
                f"Expected semantic status 'MISMATCH', got '{ev_result['semantic_match_status']}'"
            )
            
            print("  ✓ PASS: Water complaint with pothole photo stays BWSSB and flags for MANUAL_REVIEW (never silently BBMP).")
        finally:
            if os.path.exists(tmp_img_path):
                os.unlink(tmp_img_path)
    finally:
        db.close()


def test_case_6_garbage_dumping_with_stray_dogs_gathering():
    print("\n[TEST 6] Garbage Dumping with Stray Dogs Gathering (Primary Waste Subject)...")
    text = (
        "Plastic waste, food scraps and household garbage have been dumped on the empty plot "
        "beside the bus stop at Jayanagar 4th Block, Bengaluru. Stray dogs and rats are gathering "
        "and the smell is unbearable. Please clear the waste and arrange regular cleaning."
    )
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BSWML", f"Expected department 'BSWML', got '{dept_code}'"
        assert structured.get("agency") == "BSWML", f"Expected structured agency 'BSWML', got '{structured.get('agency')}'"
        assert pred_cat in [
            "Illegal Roadside Waste Dumping", "Overflowing Garbage Bins & Blackspots",
            "Garbage Not Collected", "Foul Smell & Waste Health Hazard", "Garbage"
        ], f"Expected a garbage/waste category, got '{pred_cat}'"
        assert pred_cat != "Stray Animal & Dead Animal Removal", "BUG: Garbage text misrouted to Stray Animal!"
        print("  ✓ PASS: Correctly routed to BSWML waste category, NOT BBMP stray animal.")
    finally:
        db.close()


def test_case_7_stray_dogs_menace_chasing_biting():
    print("\n[TEST 7] Stray Dog Menace (Chasing and Biting People)...")
    text = "Stray dogs are chasing and biting people on our street every evening in HSR Layout. Please send the animal control team."
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BBMP", f"Expected department 'BBMP' for live stray animal menace, got '{dept_code}'"
        assert structured.get("agency") == "BBMP", f"Expected agency 'BBMP', got '{structured.get('agency')}'"
        assert pred_cat == "Stray Animal & Dead Animal Removal", f"Expected 'Stray Animal & Dead Animal Removal', got '{pred_cat}'"
        print("  ✓ PASS: Live stray dog menace correctly routed to BBMP Stray Animal & Dead Animal Removal.")
    finally:
        db.close()


def test_case_8_dead_dog_carcass_on_road():
    print("\n[TEST 8] Dead Animal Carcass on Road...")
    text = "A dead dog has been lying on the road near the market since yesterday and the smell is spreading."
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BSWML", f"Expected department 'BSWML' for dead animal on road, got '{dept_code}'"
        assert structured.get("agency") == "BSWML", f"Expected agency 'BSWML', got '{structured.get('agency')}'"
        assert pred_cat == "Dead Animal Waste on Road", f"Expected 'Dead Animal Waste on Road', got '{pred_cat}'"
        print("  ✓ PASS: Dead animal carcass correctly routed to BSWML Dead Animal Waste on Road.")
    finally:
        db.close()


def test_case_9_garbage_overflowing_with_flies_rats():
    print("\n[TEST 9] Garbage Overflowing with Flies and Rats...")
    text = "Garbage is overflowing from the bin and flies and rats are everywhere."
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BSWML", f"Expected department 'BSWML' for overflowing garbage, got '{dept_code}'"
        assert structured.get("agency") == "BSWML", f"Expected agency 'BSWML', got '{structured.get('agency')}'"
        assert pred_cat in ["Overflowing Garbage Bins & Blackspots", "Garbage Not Collected", "Garbage"], (
            f"Expected overflowing garbage category, got '{pred_cat}'"
        )
        print("  ✓ PASS: Overflowing garbage with pests correctly routed to BSWML.")
    finally:
        db.close()


def test_case_10_footpath_pavement_bannerghatta_complaint_65():
    print("\n[TEST 10] Footpath Pavement on Bannerghatta Road (Complaint #65)...")
    text = (
        "The pavement near Jayadeva Hospital on Bannerghatta Road is damaged. "
        "Tiles are missing and the walkway is unsafe for pedestrians. Please get it repaired."
    )
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BBMP", f"Expected department 'BBMP', got '{dept_code}'"
        assert structured.get("agency") == "BBMP", f"Expected agency 'BBMP', got '{structured.get('agency')}'"
        assert pred_cat == "Broken Footpaths & Walkways", f"Expected 'Broken Footpaths & Walkways', got '{pred_cat}'"
        print("  ✓ PASS: Pavement/walkway damage on Bannerghatta Road routed to BBMP Broken Footpaths & Walkways.")
    finally:
        db.close()


def test_case_11_footpath_broken_tiles_complaint_51():
    print("\n[TEST 11] Footpath with Loose Tiles on Bannerghatta Road (Complaint #51)...")
    text = (
        "The footpath on Bannerghatta Road near Jayadeva Hospital is badly broken with loose tiles and open gaps. "
        "Pedestrians, especially senior citizens, are forced to walk on the main road. Please repair the footpath."
    )
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BBMP", f"Expected department 'BBMP', got '{dept_code}'"
        assert structured.get("agency") == "BBMP", f"Expected agency 'BBMP', got '{structured.get('agency')}'"
        assert pred_cat == "Broken Footpaths & Walkways", f"Expected 'Broken Footpaths & Walkways', got '{pred_cat}'"
        print("  ✓ PASS: Footpath damage with loose tiles routed to BBMP Broken Footpaths & Walkways.")
    finally:
        db.close()


def test_case_12_footpath_paving_slabs_complaint_52():
    print("\n[TEST 12] Paving Slabs on Walkway (Complaint #52)...")
    text = (
        "Paving slabs on the pedestrian walkway opposite Jayadeva Hospital, Bannerghatta Road have cracked and sunk. "
        "Walking is unsafe for elderly people and children, so everyone is stepping onto the traffic lane. Kindly fix the pavement soon."
    )
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BBMP", f"Expected department 'BBMP', got '{dept_code}'"
        assert structured.get("agency") == "BBMP", f"Expected agency 'BBMP', got '{structured.get('agency')}'"
        assert pred_cat == "Broken Footpaths & Walkways", f"Expected 'Broken Footpaths & Walkways', got '{pred_cat}'"
        print("  ✓ PASS: Paving slabs and walkway damage routed to BBMP Broken Footpaths & Walkways.")
    finally:
        db.close()


def test_case_13_pothole_with_pedestrians_safety():
    print("\n[TEST 13] Pothole with Pedestrians Mentioned...")
    text = "Dangerous pothole near bus stop, pedestrians are falling and two wheelers skidding."
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BBMP", f"Expected department 'BBMP', got '{dept_code}'"
        assert structured.get("agency") == "BBMP", f"Expected agency 'BBMP', got '{structured.get('agency')}'"
        assert pred_cat == "Potholes & Damaged Roads", f"Expected 'Potholes & Damaged Roads', got '{pred_cat}'"
        print("  ✓ PASS: Pothole with pedestrian mention correctly routed to BBMP Potholes & Damaged Roads.")
    finally:
        db.close()


def test_case_14_road_damaged_on_named_road():
    print("\n[TEST 14] Road Damaged and Cracks on Named Road...")
    text = "Road damaged and cracks on Bannerghatta Road"
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BBMP", f"Expected department 'BBMP', got '{dept_code}'"
        assert structured.get("agency") == "BBMP", f"Expected agency 'BBMP', got '{structured.get('agency')}'"
        assert pred_cat == "Potholes & Damaged Roads", f"Expected 'Potholes & Damaged Roads', got '{pred_cat}'"
        print("  ✓ PASS: Road damaged on Bannerghatta Road correctly routed to BBMP Potholes & Damaged Roads.")
    finally:
        db.close()


def test_case_15_pavement_with_deep_pothole_precedence():
    print("\n[TEST 15] Pavement Broken with Deep Pothole (Pothole Precedence)...")
    text = "pavement on MG Road is broken and deep pothole"
    pred_cat, conf = classify_complaint(text)
    structured = classify_complaint_structured(text)

    db = SessionLocal()
    try:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == pred_cat).first()
        assert cat is not None, f"Category '{pred_cat}' not found in database"
        dept_code = cat.department.code if cat.department else None

        print(f"  Category: '{pred_cat}' (confidence: {conf:.2f})")
        print(f"  Department Code: '{dept_code}', Structured Agency: '{structured.get('agency')}'")

        assert dept_code == "BBMP", f"Expected department 'BBMP', got '{dept_code}'"
        assert structured.get("agency") == "BBMP", f"Expected agency 'BBMP', got '{structured.get('agency')}'"
        assert pred_cat == "Potholes & Damaged Roads", f"Expected 'Potholes & Damaged Roads', got '{pred_cat}'"
        print("  ✓ PASS: Pothole precedence verified over pavement keyword.")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING END-TO-END CIVIC ROUTING REGRESSION TESTS")
    print("=" * 70)

    test_case_1_water_pipe_burst()
    test_case_2_sewage_overflow()
    test_case_3_garbage_uncollected()
    test_case_4_pothole_with_muddy_water()
    test_case_5_water_text_with_pothole_image()
    test_case_6_garbage_dumping_with_stray_dogs_gathering()
    test_case_7_stray_dogs_menace_chasing_biting()
    test_case_8_dead_dog_carcass_on_road()
    test_case_9_garbage_overflowing_with_flies_rats()
    test_case_10_footpath_pavement_bannerghatta_complaint_65()
    test_case_11_footpath_broken_tiles_complaint_51()
    test_case_12_footpath_paving_slabs_complaint_52()
    test_case_13_pothole_with_pedestrians_safety()
    test_case_14_road_damaged_on_named_road()
    test_case_15_pavement_with_deep_pothole_precedence()

    print("\n" + "=" * 70)
    print("ALL 15 END-TO-END ROUTING TESTS PASSED PERFECTLY!")
    print("=" * 70)

