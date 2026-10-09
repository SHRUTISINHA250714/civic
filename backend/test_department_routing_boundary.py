"""
Comprehensive Boundary Regression Test Suite for CivicAI Department Routing:
Validates contextual resolution of overlapping civic categories across Karnataka civic bodies:
1. BBMP: Municipal roads, potholes, footpaths, stormwater drains, lighting fixtures, parks, trees
2. BESCOM: Electricity distribution, power cuts, voltage fluctuations, wires/poles, transformers, feeder faults
3. BWSSB: Drinking-water supply, pipeline bursts, sewer lines, sewage overflow, official tankers
4. BSWML: Solid-waste collection, dumping, blackspots, garbage burning, C&D waste

Boundary Scenarios Tested:
- Boundary 1: Rainwater flooding & stormwater drains (BBMP, not BWSSB)
- Boundary 2: Sewage overflow & sewer lines (BWSSB)
- Boundary 3: Garbage blocking drain (BSWML primary with BBMP secondary vs BBMP desilting with BSWML secondary)
- Boundary 4: Streetlight fixture (BBMP) vs power supply fault (BESCOM)
- Boundary 5: Tree branches touching power lines (BESCOM electrical hazard with BBMP Forest Cell secondary)
- Boundary 6: Foul smell: decomposing garbage (BSWML) vs sewage (BWSSB) vs drinking water (BWSSB)
- Boundary 7: Water tanker: BWSSB official tanker (BWSSB) vs private commercial tanker dispute (BBMP)
- Boundary 8: C&D debris dumping (BSWML) vs road cave-in/sinkhole (BBMP)
- Boundary 9: Conflicting cross-department emergency signals (routed to manual review)
- Boundary 10: Inconclusive text (clean SentenceTransformer AI fallback)
- Boundary 11: Core regression cases for all 4 authorities
- Boundary 12: Officer assignment workflow with secondary coordination remarks
"""
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.routing import (
    resolve_department_routing,
    assign_officer_to_complaint,
    AGENCY_METADATA,
    CATEGORY_TO_DEPARTMENT,
    SECONDARY_COORDINATION_RULES
)
from backend.app.services.ai import classify_complaint, classify_complaint_structured
from backend.app.core.database import SessionLocal
from backend.app.models.complaint import Complaint, ComplaintCategory, ComplaintStatusHistory, Notification
from backend.app.models.department import Department
from backend.app.models.user import Officer, User


def test_boundary_1_stormwater_vs_sewage():
    print("\n[TEST 1] Boundary 1: Rainwater Flooding & Stormwater Drains (BBMP vs BWSSB)...")
    
    # 1. Rainwater flooding / stormwater drain MUST route to BBMP (NOT BWSSB)
    cases_bbmp = [
        "Heavy rain caused severe waterlogging and blocked stormwater drain on 100 feet road",
        "Road completely flooded after monsoon downpour due to choked rajakaluve storm drain",
        "Rainwater entered compound because culvert and municipal storm drain are overflowing",
        "Water logging on underpass due to heavy rainfall and blocked municipal drainage"
    ]
    for text in cases_bbmp:
        res = classify_complaint_structured(text)
        assert res["agency"] == "BBMP", f"Expected BBMP for stormwater text, got {res['agency']}: '{text}'"
        assert res["category_name"] == "Blocked Stormwater Drains & Waterlogging", f"Unexpected category: {res['category_name']}"
        print(f"  ✓ Rainwater/Stormwater -> {res['agency']} [{res['category_name']}]: '{text[:45]}...'")

    # 2. Sewage overflow MUST route to BWSSB
    cases_bwssb = [
        "Underground sewer line blocked and dirty sewage overflow onto residential street",
        "Foul sewage and toilet wastewater bubbling out of open manhole on 4th cross",
        "Blocked UGD pipeline causing blackwater sewage overflow into front yards"
    ]
    for text in cases_bwssb:
        res = classify_complaint_structured(text)
        assert res["agency"] == "BWSSB", f"Expected BWSSB for sewage overflow, got {res['agency']}: '{text}'"
        assert res["category_name"] in ["Sewage Overflow & Gutter Water", "Blocked Sewer Line & Manhole Overflow", "Damaged Manhole Cover & Missing Lid"]
        print(f"  ✓ Sewage/Sewer -> {res['agency']} [{res['category_name']}]: '{text[:45]}...'")


def test_boundary_2_garbage_blocking_drain():
    print("\n[TEST 2] Boundary 2: Garbage Blocking Drain (Solid-Waste vs Drainage Maintenance)...")

    # A. Dumping garbage into drain: primary = BSWML (waste removal), secondary = BBMP
    waste_in_drain = "Plastic bags and domestic trash dumped in drain blocking flow, auto tipper needed to clear waste"
    res_waste = classify_complaint_structured(waste_in_drain)
    assert res_waste["agency"] == "BSWML", f"Expected BSWML primary, got {res_waste['agency']}"
    assert res_waste["secondary_agency"] == "BBMP", f"Expected BBMP secondary, got {res_waste['secondary_agency']}"
    assert "clearance" in res_waste["coordination_reason"].lower() or "drain" in res_waste["coordination_reason"].lower()
    print(f"  ✓ Garbage dumped in drain -> Primary: {res_waste['agency']}, Secondary: {res_waste['secondary_agency']}")

    # B. Storm drain choked with silt: primary = BBMP (desilting), secondary = BSWML
    silt_drain = "Stormwater drain blocked by silt and debris causing road overflow, municipal desilting needed"
    res_silt = classify_complaint_structured(silt_drain)
    assert res_silt["agency"] == "BBMP", f"Expected BBMP primary, got {res_silt['agency']}"
    assert res_silt["secondary_agency"] == "BSWML", f"Expected BSWML secondary, got {res_silt['secondary_agency']}"
    assert res_silt["category_name"] == "Blocked Stormwater Drains & Waterlogging"
    print(f"  ✓ Drain desilting/waterlogging -> Primary: {res_silt['agency']}, Secondary: {res_silt['secondary_agency']}")


def test_boundary_3_streetlight_fixture_vs_power_supply():
    print("\n[TEST 3] Boundary 3: Streetlight Fixture (BBMP) vs Power Supply Fault (BESCOM)...")

    # A. Municipal fixture / bulb damaged -> BBMP
    fixture_cases = [
        "Streetlight fixture bulb is broken and dark on 5th cross",
        "Street light lamp post glass is damaged and bulb fused near park gate",
        "Broken streetlight lamp hanging dangerously from bracket"
    ]
    for text in fixture_cases:
        res = classify_complaint_structured(text)
        assert res["agency"] == "BBMP", f"Expected BBMP for fixture fault, got {res['agency']}"
        assert res["category_name"] == "Damaged Streetlights"
        print(f"  ✓ Streetlight fixture -> {res['agency']} [{res['category_name']}]: '{text[:45]}...'")

    # B. Electrical power supply fault / feeder line -> BESCOM
    power_cases = [
        "Streetlight feeder line power supply fault, no current reaching entire road stretch",
        "Streetlight circuit trip and feeder pillar power failure on 80 feet road",
        "No power to streetlight due to underground cable fault and phase problem"
    ]
    for text in power_cases:
        res = classify_complaint_structured(text)
        assert res["agency"] == "BESCOM", f"Expected BESCOM for power supply fault, got {res['agency']}"
        assert res["category_name"] == "Streetlight Power Supply Fault"
        print(f"  ✓ Streetlight power fault -> {res['agency']} [{res['category_name']}]: '{text[:45]}...'")


def test_boundary_4_trees_touching_power_lines():
    print("\n[TEST 4] Boundary 4: Trees Touching Power Lines (BESCOM Hazard + BBMP Tree Cell)...")

    tree_line_cases = [
        "Overgrown tree branches touching high tension power lines with sparking danger",
        "Large tree branch fell on electric wire and tilted electric pole on 2nd main",
        "Tree limbs tangled on BESCOM power line causing sparks whenever wind blows"
    ]
    for text in tree_line_cases:
        res = classify_complaint_structured(text)
        assert res["agency"] == "BESCOM", f"Expected BESCOM primary hazard, got {res['agency']}"
        assert res["secondary_agency"] == "BBMP", f"Expected BBMP secondary, got {res['secondary_agency']}"
        assert "BBMP Forest Cell" in res["coordination_reason"] or "tree trimming" in res["coordination_reason"]
        print(f"  ✓ Tree touching power lines -> Primary: {res['agency']} [{res['category_name']}], Secondary: {res['secondary_agency']}")


def test_boundary_5_foul_smell_disambiguation():
    print("\n[TEST 5] Boundary 5: Foul Smell Disambiguation (Garbage vs Sewage vs Water)...")

    # A. Rotten garbage foul smell -> BSWML
    smell_garbage = "Terrible foul smell coming from decomposing garbage and rotting food waste blackspot"
    res_g = classify_complaint_structured(smell_garbage)
    assert res_g["agency"] == "BSWML", f"Expected BSWML for garbage smell, got {res_g['agency']}"
    assert res_g["category_name"] == "Foul Smell & Waste Health Hazard"
    print(f"  ✓ Garbage foul smell -> {res_g['agency']} [{res_g['category_name']}]")

    # B. Sewage leakage foul smell -> BWSSB
    smell_sewage = "Severe foul smell and stink coming from open sewer line and leaking sewage"
    res_s = classify_complaint_structured(smell_sewage)
    assert res_s["agency"] == "BWSSB", f"Expected BWSSB for sewer smell, got {res_s['agency']}"
    assert res_s["category_name"] == "Sewage Overflow & Gutter Water"
    print(f"  ✓ Sewage foul smell -> {res_s['agency']} [{res_s['category_name']}]")

    # C. Drinking water foul smell -> BWSSB
    smell_water = "Tap drinking water has terrible bad smell and brown mud contamination"
    res_w = classify_complaint_structured(smell_water)
    assert res_w["agency"] == "BWSSB", f"Expected BWSSB for water smell, got {res_w['agency']}"
    assert res_w["category_name"] == "Contaminated Drinking Water"
    print(f"  ✓ Water foul smell -> {res_w['agency']} [{res_w['category_name']}]")

    # D. Dead animal carcass foul smell -> BSWML
    smell_carcass = "Bad smell due to dead animal carcass of a dog lying on the road"
    res_c = classify_complaint_structured(smell_carcass)
    assert res_c["agency"] == "BSWML", f"Expected BSWML for animal carcass, got {res_c['agency']}"
    assert res_c["category_name"] == "Dead Animal Waste on Road"
    print(f"  ✓ Dead animal foul smell -> {res_c['agency']} [{res_c['category_name']}]")


def test_boundary_6_water_tanker_bwssb_vs_private():
    print("\n[TEST 6] Boundary 6: Water Tanker Complaints (BWSSB Official vs Private Service)...")

    # A. Official BWSSB Kaveri water tanker delay/meter -> BWSSB
    bwssb_tanker = "Booked official BWSSB water tanker through portal 3 days ago but Kaveri supply tanker not arrived"
    res_b = classify_complaint_structured(bwssb_tanker)
    assert res_b["agency"] == "BWSSB", f"Expected BWSSB for official tanker, got {res_b['agency']}"
    assert res_b["category_name"] == "Water Meter & Tanker Issues"
    print(f"  ✓ Official BWSSB tanker -> {res_b['agency']} [{res_b['category_name']}]")

    # B. Private commercial tanker nuisance/overcharging -> BBMP (Others / municipal regulation)
    private_tanker = "Private tanker mafia overcharging exorbitant commercial rate and reckless speeding on street"
    res_p = classify_complaint_structured(private_tanker)
    assert res_p["agency"] == "BBMP", f"Expected BBMP for private tanker regulation, got {res_p['agency']}"
    assert res_p["category_name"] == "Others"
    print(f"  ✓ Private tanker commercial dispute -> {res_p['agency']} [{res_p['category_name']}]")


def test_boundary_7_cd_debris_vs_road_cavein():
    print("\n[TEST 7] Boundary 7: C&D Debris (BSWML) vs Road Cave-In (BBMP)...")

    # A. Construction & demolition debris dumping -> BSWML
    cd_dumping = "Huge pile of construction waste and demolition debris dumped on roadside by builder"
    res_cd = classify_complaint_structured(cd_dumping)
    assert res_cd["agency"] == "BSWML", f"Expected BSWML for C&D dumping, got {res_cd['agency']}"
    assert res_cd["category_name"] == "Bulk & Construction Waste Dumping"
    print(f"  ✓ C&D waste dumping -> {res_cd['agency']} [{res_cd['category_name']}]")

    # B. Road cave-in / sinkhole from excavation -> BBMP with BSWML secondary
    road_cavein = "Excavation trench collapsed resulting in road cave-in and sinkhole with asphalt destroyed"
    res_cavein = classify_complaint_structured(road_cavein)
    assert res_cavein["agency"] == "BBMP", f"Expected BBMP for road cave-in, got {res_cavein['agency']}"
    assert res_cavein["category_name"] == "Construction Debris & Road Cave-in"
    assert res_cavein["secondary_agency"] == "BSWML"
    print(f"  ✓ Road cave-in / sinkhole -> Primary: {res_cavein['agency']}, Secondary: {res_cavein['secondary_agency']}")


def test_boundary_8_conflicting_signals_and_manual_review():
    print("\n[TEST 8] Boundary 8: Conflicting Cross-Department Signals (Manual Review)...")

    # A. Disjoint cross-department emergency collision (e.g. BESCOM power + BWSSB sewage)
    conflict_text = "Live wire snapped and sparking on pole, and sewage overflow from sewer line entering houses"
    res_conf = classify_complaint_structured(conflict_text)
    assert res_conf["is_conflict"] is True, f"Expected is_conflict=True, got {res_conf['is_conflict']}"
    assert res_conf["needs_manual_review"] is True, f"Expected needs_manual_review=True"
    assert res_conf["category_name"] == "Others"
    print(f"  ✓ Disjoint emergency collision -> is_conflict={res_conf['is_conflict']}, needs_manual_review={res_conf['needs_manual_review']}")

    # B. Explicit conflict phrasing
    explicit_conflict = "Conflicting report from residents: not sure which agency is responsible for this junction mess"
    res_exp = classify_complaint_structured(explicit_conflict)
    assert res_exp["is_conflict"] is True
    assert res_exp["needs_manual_review"] is True
    print(f"  ✓ Explicit conflict wording -> is_conflict={res_exp['is_conflict']}, needs_manual_review={res_exp['needs_manual_review']}")


def test_boundary_9_inconclusive_ai_fallback():
    print("\n[TEST 9] Boundary 9: Inconclusive Text AI Fallback...")

    unclear_text = "Something unusual is happening near the corner of our street"
    routing_raw = resolve_department_routing(unclear_text)
    assert routing_raw["category_name"] is None, "Deterministic rules should be inconclusive"

    # AI classifier falls back gracefully without crash
    cat, conf = classify_complaint(unclear_text)
    assert cat in CATEGORY_TO_DEPARTMENT, f"Fallback category '{cat}' must be in canonical taxonomy"
    assert 0.0 <= conf <= 1.0
    print(f"  ✓ Inconclusive query safely fell back to SentenceTransformer -> '{cat}' (conf: {conf:.2f})")


def test_boundary_10_core_regression_all_agencies():
    print("\n[TEST 10] Boundary 10: Core Regression Across All 4 Agencies...")

    test_matrix = [
        ("Severe pothole on MG Road near Trinity circle damaging cars", "BBMP", "Potholes & Damaged Roads"),
        ("Footpath tiles broken and missing on Brigade road", "BBMP", "Broken Footpaths & Walkways"),
        ("Public park benches broken and weeds overgrown in playground", "BBMP", "Park Maintenance & Public Gardens"),
        ("Power cut and total electricity blackout in Indiranagar", "BESCOM", "Power Outage & Blackout"),
        ("Distribution transformer sparking and smoking heavily on 12th main", "BESCOM", "Transformer Failure & Sparks"),
        ("Severe voltage fluctuation damaging household appliances", "BESCOM", "Voltage Fluctuation (Low/High)"),
        ("No drinking water supply for 3 consecutive days in Koramangala", "BWSSB", "No Water Supply"),
        ("Underground drinking water pipeline burst wasting clean water on road", "BWSSB", "Water Pipeline Burst & Leakage"),
        ("Missing manhole cover on dark road creating fatal accident hazard", "BWSSB", "Damaged Manhole Cover & Missing Lid"),
        ("Garbage not collected by door to door auto tipper for past 4 days", "BSWML", "Garbage Not Collected"),
        ("Toxic smoke from illegal garbage burning on empty plot", "BSWML", "Garbage Burning & Air Pollution"),
        ("Overflowing garbage bins with black spot and scattered trash on road", "BSWML", "Overflowing Garbage Bins & Blackspots"),
    ]

    for text, expected_agency, expected_category in test_matrix:
        res = classify_complaint_structured(text)
        assert res["agency"] == expected_agency, f"For '{text}', expected {expected_agency}, got {res['agency']}"
        assert res["category_name"] == expected_category, f"For '{text}', expected category {expected_category}, got {res['category_name']}"
        print(f"  ✓ Verified: {expected_agency} -> {expected_category}")


def test_boundary_11_officer_assignment_secondary_coordination():
    print("\n[TEST 11] Boundary 11: Officer Assignment Workflow & Secondary Coordination Audit...")

    db = SessionLocal()
    try:
        # Find an existing category and on-duty officer
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == "Exposed Wires & Electrical Hazards").first()
        if not cat:
            cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == "Power Outage & Blackout").first()
        assert cat is not None, "Test requires at least one seeded category in DB"

        # Check officer assignment
        dummy_complaint = Complaint(
            citizen_id=1,
            category_id=cat.id,
            description="Tree branches touching high tension power lines with sparking danger",
            location_latitude=12.9716,
            location_longitude=77.5946,
            location_address="100 Feet Road, Indiranagar, Bengaluru",
            status="Registered",
            priority="Critical",
            reopen_count=0
        )
        db.add(dummy_complaint)
        db.flush()

        officer = assign_officer_to_complaint(db, dummy_complaint)
        if officer:
            assert dummy_complaint.assigned_officer_id == officer.id
            # Verify status history audit remarks include secondary agency coordination
            history = db.query(ComplaintStatusHistory).filter(
                ComplaintStatusHistory.complaint_id == dummy_complaint.id
            ).order_by(ComplaintStatusHistory.created_at.desc()).first()

            assert history is not None
            assert "BBMP" in history.remarks or "coordination" in history.remarks.lower()
            print(f"  ✓ Officer assigned: {officer.id} (Dept: {officer.department_id})")
            print(f"  ✓ Cross-agency coordination logged in ComplaintStatusHistory: '{history.remarks}'")
        else:
            print("  Note: No active officers seeded in database for this department; fallback passed safely.")

        db.rollback()
    finally:
        db.close()


def run_all_boundary_tests():
    print("=" * 80)
    print("CIVICAI DEPARTMENT ROUTING ENHANCEMENT: BOUNDARY TEST SUITE")
    print("=" * 80)
    test_boundary_1_stormwater_vs_sewage()
    test_boundary_2_garbage_blocking_drain()
    test_boundary_3_streetlight_fixture_vs_power_supply()
    test_boundary_4_trees_touching_power_lines()
    test_boundary_5_foul_smell_disambiguation()
    test_boundary_6_water_tanker_bwssb_vs_private()
    test_boundary_7_cd_debris_vs_road_cavein()
    test_boundary_8_conflicting_signals_and_manual_review()
    test_boundary_9_inconclusive_ai_fallback()
    test_boundary_10_core_regression_all_agencies()
    test_boundary_11_officer_assignment_secondary_coordination()
    print("=" * 80)
    print("ALL 11 BOUNDARY & REGRESSION TEST SUITES PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_boundary_tests()
