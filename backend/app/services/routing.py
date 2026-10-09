import re
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.user import User, Officer
from backend.app.models.complaint import Complaint, ComplaintCategory, Notification, ComplaintStatusHistory

# ─────────────────────────────────────────────────────────────────────────────
# Centralized Master Taxonomy & Authority Metadata for Karnataka Civic Bodies
# 1. BBMP: Roads, Footpaths, Stormwater Drains, Streetlights, Parks, Trees
# 2. BESCOM: Power Supply, Voltage, Lines, Transformers, Electric Poles, Meters
# 3. BWSSB: Drinking Water, Water Mains, Sanitary Sewerage, Manholes
# 4. BSWML: Solid Waste Collection, Segregation, Dumping, C&D Waste, Burning
# ─────────────────────────────────────────────────────────────────────────────

AGENCY_METADATA: Dict[str, Dict[str, str]] = {
    "BBMP": {
        "name": "Bruhat Bengaluru Mahanagara Palike",
        "code": "BBMP",
        "domain": "Roads, Drains, Street Lighting & Civic Services",
        "description": "Municipal civic services: roads, footpaths, stormwater drains, street lighting fixtures, parks, public health, lakes, trees, civic amenities."
    },
    "BESCOM": {
        "name": "Bangalore Electricity Supply Company Limited",
        "code": "BESCOM",
        "domain": "Electricity Distribution & Consumer Services",
        "description": "Electricity distribution, power outages, electrical faults, meters, poles/lines, feeder lines, transformers, billing."
    },
    "BWSSB": {
        "name": "Bangalore Water Supply and Sewerage Board",
        "code": "BWSSB",
        "domain": "Water Supply & Underground Drainage/Sewerage",
        "description": "Drinking water supply, pipeline leakage, water quality, sanitary sewer lines, manholes, UGD network, official water tankers."
    },
    "BSWML": {
        "name": "Bengaluru Solid Waste Management Limited",
        "code": "BSWML",
        "domain": "Solid-Waste & C&D-Waste Management",
        "description": "Solid-waste and C&D-waste management, door-to-door collection, roadside dumping, black spots, waste burning, waste transportation, C&D disposal."
    }
}

# Centralized 47-Category to Department Mapping
CATEGORY_TO_DEPARTMENT: Dict[str, str] = {
    # BBMP (16)
    "Potholes & Damaged Roads": "BBMP",
    "Pothole": "BBMP",
    "Road Damage": "BBMP",
    "Broken Footpaths & Walkways": "BBMP",
    "Blocked Stormwater Drains & Waterlogging": "BBMP",
    "Damaged Streetlights": "BBMP",
    "Streetlight": "BBMP",
    "Park Maintenance & Public Gardens": "BBMP",
    "Lakes & Water Bodies": "BBMP",
    "Public Toilet & Civic Amenities": "BBMP",
    "Road & Footpath Encroachment": "BBMP",
    "Tree Fall & Dangerous Branches": "BBMP",
    "Tree Fall": "BBMP",
    "Construction Debris & Road Cave-in": "BBMP",
    "Stray Animal & Dead Animal Removal": "BBMP",
    "Others": "BBMP",

    # BESCOM (10)
    "Power Outage & Blackout": "BESCOM",
    "Power Outage": "BESCOM",
    "Frequent Power Cuts": "BESCOM",
    "Voltage Fluctuation (Low/High)": "BESCOM",
    "Transformer Failure & Sparks": "BESCOM",
    "Damaged Electric Poles & Broken Wires": "BESCOM",
    "Fallen Electric Wire": "BESCOM",
    "Exposed Wires & Electrical Hazards": "BESCOM",
    "Streetlight Power Supply Fault": "BESCOM",
    "Electricity Meter & Billing Issues": "BESCOM",

    # BWSSB (10)
    "No Water Supply": "BWSSB",
    "Low Water Pressure": "BWSSB",
    "Water Pipeline Burst & Leakage": "BWSSB",
    "Water Leakage": "BWSSB",
    "Contaminated Drinking Water": "BWSSB",
    "Sewage Overflow & Gutter Water": "BWSSB",
    "Sewage Overflow": "BWSSB",
    "Blocked Sewer Line & Manhole Overflow": "BWSSB",
    "Damaged Manhole Cover & Missing Lid": "BWSSB",
    "Water Meter & Tanker Issues": "BWSSB",

    # BSWML (11)
    "Garbage Not Collected": "BSWML",
    "Garbage": "BSWML",
    "Irregular Garbage Collection": "BSWML",
    "Overflowing Garbage Bins & Blackspots": "BSWML",
    "Illegal Roadside Waste Dumping": "BSWML",
    "Illegal Dumping": "BSWML",
    "Foul Smell & Waste Health Hazard": "BSWML",
    "Garbage Burning & Air Pollution": "BSWML",
    "Wet & Dry Waste Segregation Issues": "BSWML",
    "Bulk & Construction Waste Dumping": "BSWML",
    "Dead Animal Waste on Road": "BSWML",
}

# Secondary Agency Coordination Rules
SECONDARY_COORDINATION_RULES: Dict[str, Dict[str, str]] = {
    "tree_power_line": {
        "secondary_agency": "BBMP",
        "reason": "Tree branches interfering with electrical power lines/poles require electrical safety mitigation by BESCOM and tree trimming clearance by BBMP Forest Cell."
    },
    "garbage_in_drain": {
        "secondary_agency": "BBMP",
        "reason": "Solid waste dumped in municipal drain requires clearance by BSWML and drainage structural inspection by BBMP Stormwater Drains."
    },
    "drain_waste_choke": {
        "secondary_agency": "BSWML",
        "reason": "Stormwater drain blockage requiring municipal desilting by BBMP with solid waste clearance coordination by BSWML."
    },
    "pipe_burst_road_damage": {
        "secondary_agency": "BBMP",
        "reason": "Water pipeline burst requires utility repair by BWSSB and road asphalt restoration by BBMP."
    },
    "road_cavein_utility": {
        "secondary_agency": "BWSSB",
        "reason": "Road cave-in near underground utility trench requires joint inspection with BWSSB."
    }
}


def resolve_department_routing(
    text: str,
    location_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Context-aware deterministic routing engine resolving overlapping civic categories
    across BBMP, BESCOM, BWSSB, and BSWML based on contextual multi-token phrases.

    Returns:
        Dict with keys:
        - category_name: Standardized category name
        - agency: Responsible department code (BBMP, BESCOM, BWSSB, BSWML)
        - confidence: Routing confidence score (0.0 - 1.0)
        - secondary_agency: Optional secondary agency requiring coordination
        - coordination_reason: Reason for secondary agency coordination
        - is_conflict: Boolean indicating whether conflicting signals were found
        - needs_manual_review: Boolean indicating if manual triage is recommended
        - routing_reason: Explainable description of the routing rationale
    """
    if not text or not text.strip():
        return {
            "category_name": "Others",
            "agency": "BBMP",
            "confidence": 0.50,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": True,
            "routing_reason": "Empty complaint text provided; flagged for manual review."
        }

    text_lower = text.lower()
    loc_lower = (location_address or "").lower()

    # ─────────────────────────────────────────────────────────────────────────
    # 0. Emergency Conflicting Signals Check (Cross-Department Multi-Incident)
    # ─────────────────────────────────────────────────────────────────────────
    major_signals = set()
    if any(w in text_lower for w in ["pothole", "crater", "road cave-in", "broken road"]):
        major_signals.add("BBMP_ROAD")
    if any(w in text_lower for w in ["power outage", "transformer fire", "transformer blast", "live wire", "snapped wire"]):
        major_signals.add("BESCOM_POWER")
    if any(w in text_lower for w in ["pipeline burst", "contaminated water", "sewage overflow", "sewer line blocked"]):
        major_signals.add("BWSSB_WATER")
    if any(w in text_lower for w in ["garbage burning", "plastic burning", "toxic smoke from waste"]):
        major_signals.add("BSWML_WASTE")

    # If 3 or more completely distinct major emergency sectors appear in text,
    # or disjoint emergency sectors without a defined coordination link (e.g. BESCOM power + BWSSB sewage),
    # it indicates conflicting multi-incident text that cannot be resolved safely to a single department.
    is_disjoint_collision = (
        ("BESCOM_POWER" in major_signals and "BWSSB_WATER" in major_signals) or
        ("BESCOM_POWER" in major_signals and "BSWML_WASTE" in major_signals) or
        len(major_signals) >= 3
    )
    is_explicit_conflict_phrasing = any(p in text_lower for p in [
        "conflicting report", "unclear department", "not sure which agency",
        "multiple unrelated issues", "both electricity and water supply failed",
        "both power cut and sewage overflow"
    ])

    if is_disjoint_collision or is_explicit_conflict_phrasing:
        return {
            "category_name": "Others",
            "agency": "BBMP",
            "confidence": 0.50,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": True,
            "needs_manual_review": True,
            "routing_reason": "Conflicting multi-department emergency signals detected across unrelated civic domains. Routed for manual operational review."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Boundary Case: Trees Touching Power Lines / Electric Hazards
    # ─────────────────────────────────────────────────────────────────────────
    has_tree = any(w in text_lower for w in [
        "tree", "branch", "branches", "tree branch", "overgrown branch", "mara", "marada", "kombe"
    ])
    has_electric_wire = any(w in text_lower for w in [
        "electric wire", "power line", "high tension", "ht line", "electric line", "live wire",
        "wire", "wires", "cable", "cables", "electric pole", "power pole", "transformer",
        "current line", "bescom line"
    ])
    has_interference = any(w in text_lower for w in [
        "touch", "touching", "tangled", "fell on", "fallen on", "spark", "sparking",
        "dangling on", "near ht", "near power", "near wire", "on wire", "on pole", "snapped"
    ])

    if has_tree and has_electric_wire and has_interference:
        cat = "Damaged Electric Poles & Broken Wires" if any(w in text_lower for w in ["pole", "snapped", "broken"]) else "Exposed Wires & Electrical Hazards"
        return {
            "category_name": cat,
            "agency": "BESCOM",
            "confidence": 0.98,
            "secondary_agency": "BBMP",
            "coordination_reason": SECONDARY_COORDINATION_RULES["tree_power_line"]["reason"],
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Tree branches interfering with electrical power lines/poles: prioritized as BESCOM electrical hazard with BBMP Forest Cell coordination."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Boundary Case: Streetlight (Fixture vs. Power Supply Fault)
    # ─────────────────────────────────────────────────────────────────────────
    is_streetlight_term = any(w in text_lower for w in [
        "streetlight", "street light", "street lamp", "streetlamp", "lamp post", "beedi deepa", "bidi dipa"
    ])
    is_power_supply_fault = any(w in text_lower for w in [
        "power supply", "feeder", "feeder line", "feeder pillar", "circuit trip", "no power to streetlight",
        "power failure to streetlight", "line fault", "cable power fault", "supply fault", "phase problem",
        "no current in streetlight", "cable fault", "feeder fault"
    ])

    if is_streetlight_term and is_power_supply_fault:
        return {
            "category_name": "Streetlight Power Supply Fault",
            "agency": "BESCOM",
            "confidence": 0.97,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Streetlight electrical feed / power supply failure routed to BESCOM."
        }
    elif is_streetlight_term:
        return {
            "category_name": "Damaged Streetlights",
            "agency": "BBMP",
            "confidence": 0.97,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Streetlight municipal fixture / lamp fault routed to BBMP."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Boundary Case: Garbage Blocking a Drain (Solid Waste vs Drainage Maintenance)
    # Evaluated before general stormwater drainage to properly isolate waste-in-drain issues.
    # ─────────────────────────────────────────────────────────────────────────
    has_waste_words = any(w in text_lower for w in ["garbage", "trash", "waste", "kachra", "plastic", "debris"])
    has_drain_words = any(w in text_lower for w in ["drain", "storm drain", "stormwater", "gutter", "rajakaluve", "culvert", "ditch"])

    if has_waste_words and has_drain_words:
        is_waste_dumping_focus = any(w in text_lower for w in [
            "dumped in drain", "thrown in drain", "plastic waste in drain", "clear the garbage from drain",
            "garbage accumulating in drain", "trash inside drain", "garbage pile in drain", "waste tipper needed",
            "people throwing trash in drain", "plastic bags in drain", "garbage in drain", "trash in drain",
            "waste in drain", "clear waste", "auto tipper"
        ])
        if is_waste_dumping_focus:
            return {
                "category_name": "Overflowing Garbage Bins & Blackspots" if "bin" in text_lower else "Illegal Roadside Waste Dumping",
                "agency": "BSWML",
                "confidence": 0.96,
                "secondary_agency": "BBMP",
                "coordination_reason": SECONDARY_COORDINATION_RULES["garbage_in_drain"]["reason"],
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Solid waste dumped in drain routed to BSWML for waste clearance with BBMP Stormwater Drains coordination."
            }
        else:
            return {
                "category_name": "Blocked Stormwater Drains & Waterlogging",
                "agency": "BBMP",
                "confidence": 0.96,
                "secondary_agency": "BSWML",
                "coordination_reason": SECONDARY_COORDINATION_RULES["drain_waste_choke"]["reason"],
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Stormwater drain blockage requiring municipal desilting by BBMP with solid waste clearance coordination by BSWML."
            }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Boundary Case: Rainwater Flooding / Stormwater Drains vs. Sewage Overflow
    # ─────────────────────────────────────────────────────────────────────────
    has_pothole_crater = any(w in text_lower for w in ["pothole", "potholes", "crater", "craters", "gundi", "road damage", "damaged road"])
    has_flooding_drainage = any(w in text_lower for w in [
        "waterlogging", "water logging", "water logged", "flooded", "flooding",
        "stormwater", "storm drain", "rajakaluve", "culvert", "surface runoff",
        "drain overflow", "desilting", "silt in drain", "blocked drain", "drain blocked"
    ])
    has_rain_stormwater = has_flooding_drainage and not (
        has_pothole_crater and not any(w in text_lower for w in [
            "waterlogging", "water logging", "water logged", "storm drain", "rajakaluve", "culvert"
        ])
    )
    has_sewage = any(w in text_lower for w in [
        "sewage", "sewer", "sewer line", "underground drainage", "ugd", "manhole",
        "toilet waste", "blackwater", "fecal", "sewerage", "septic", "sewage overflow"
    ])

    # If sanitary sewage / sewer line is explicitly reported:
    if has_sewage:
        if any(w in text_lower for w in ["manhole", "cover", "lid", "open manhole", "missing lid"]):
            cat = "Damaged Manhole Cover & Missing Lid"
            conf = 0.98
        elif any(w in text_lower for w in ["block", "chok", "clog"]):
            cat = "Blocked Sewer Line & Manhole Overflow"
            conf = 0.97
        else:
            cat = "Sewage Overflow & Gutter Water"
            conf = 0.97
        return {
            "category_name": cat,
            "agency": "BWSSB",
            "confidence": conf,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Sanitary sewerage / sewer line / manhole overflow routed to BWSSB."
        }

    # If rainwater flooding / stormwater drains (without sanitary sewage):
    if has_rain_stormwater:
        return {
            "category_name": "Blocked Stormwater Drains & Waterlogging",
            "agency": "BBMP",
            "confidence": 0.97,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Rainwater flooding / stormwater drain waterlogging routed to BBMP municipal drainage authority."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Boundary Case: Foul Smell (Decomposing Garbage vs Sewage Leakage)
    # ─────────────────────────────────────────────────────────────────────────
    has_foul_smell = any(w in text_lower for w in [
        "foul smell", "bad smell", "stink", "stinking", "bad odor", "foul odor", "terrible smell"
    ])
    if has_foul_smell:
        # If foul smell is associated with sewer, sewage, manhole, or drinking water:
        if any(w in text_lower for w in ["sewer", "sewage", "manhole", "toilet", "gutter", "drainage"]):
            return {
                "category_name": "Sewage Overflow & Gutter Water",
                "agency": "BWSSB",
                "confidence": 0.96,
                "secondary_agency": None,
                "coordination_reason": None,
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Foul smell originating from sanitary sewer / sewage overflow routed to BWSSB."
            }
        if any(w in text_lower for w in ["drinking water", "tap water", "kaveri water", "water pipe", "water smell"]):
            return {
                "category_name": "Contaminated Drinking Water",
                "agency": "BWSSB",
                "confidence": 0.97,
                "secondary_agency": None,
                "coordination_reason": None,
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Foul smell from drinking water supply routed to BWSSB."
            }
        # If dead animal carcass:
        if any(w in text_lower for w in ["dead animal", "carcass", "dead dog", "dead cat", "dead bird"]):
            return {
                "category_name": "Dead Animal Waste on Road",
                "agency": "BSWML",
                "confidence": 0.96,
                "secondary_agency": None,
                "coordination_reason": None,
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Dead animal carcass causing foul smell routed to BSWML."
            }
        # If decomposing garbage / waste blackspot:
        return {
            "category_name": "Foul Smell & Waste Health Hazard",
            "agency": "BSWML",
            "confidence": 0.96,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Foul smell from decomposing solid waste routed to BSWML."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Boundary Case: Water-Tanker Complaints (BWSSB Official vs Private Service)
    # ─────────────────────────────────────────────────────────────────────────
    has_tanker = "tanker" in text_lower
    if has_tanker:
        is_private_tanker = any(w in text_lower for w in [
            "private tanker", "commercial tanker", "private water tanker", "tanker mafia",
            "overcharging", "exorbitant", "reckless driving", "speeding", "illegal borewell", "commercial rate"
        ])
        if is_private_tanker and not any(w in text_lower for w in ["bwssb", "kaveri", "official", "government"]):
            return {
                "category_name": "Others",
                "agency": "BBMP",
                "confidence": 0.92,
                "secondary_agency": None,
                "coordination_reason": None,
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Private commercial tanker operational or pricing dispute routed to BBMP municipal regulation rather than BWSSB utility dispatch."
            }
        if any(w in text_lower for w in ["bwssb", "kaveri", "official", "booked", "booking", "water board", "supply delay", "tanker not arrived", "water tanker"]):
            return {
                "category_name": "Water Meter & Tanker Issues",
                "agency": "BWSSB",
                "confidence": 0.96,
                "secondary_agency": None,
                "coordination_reason": None,
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Official BWSSB water tanker supply issue routed to BWSSB."
            }

    # ─────────────────────────────────────────────────────────────────────────
    # 7. Boundary Case: C&D Debris vs. Road Cave-In
    # ─────────────────────────────────────────────────────────────────────────
    is_cd_waste = any(w in text_lower for w in [
        "c&d", "c and d", "construction waste", "demolition waste", "building debris",
        "debris dumped", "concrete rubble", "tiles waste", "construction material dumped", "building waste",
        "construction debris", "excavation debris", "debris"
    ])
    is_cavein = any(w in text_lower for w in [
        "cave-in", "cave in", "sinkhole", "trench collapsed", "road cave-in", "road collapsed"
    ])

    if is_cd_waste or is_cavein:
        if is_cavein or any(w in text_lower for w in ["trench", "asphalt destroyed", "road pit"]):
            return {
                "category_name": "Construction Debris & Road Cave-in",
                "agency": "BBMP",
                "confidence": 0.96,
                "secondary_agency": "BSWML",
                "coordination_reason": "Road structural damage requires BBMP engineering inspection with BSWML C&D waste clearance.",
                "is_conflict": False,
                "needs_manual_review": False,
                "routing_reason": "Construction excavation and road cave-in routed to BBMP."
            }
        return {
            "category_name": "Bulk & Construction Waste Dumping",
            "agency": "BSWML",
            "confidence": 0.96,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Construction & Demolition debris dumped on roadside routed to BSWML."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 8. Core BBMP Specific Facilities (Footpaths, Parks, Lakes, Trees, Amenities)
    # Evaluated prior to general road defect keywords to prevent false pothole triggers.
    # ─────────────────────────────────────────────────────────────────────────
    has_pothole_or_crater = any(w in text_lower for w in ["pothole", "potholes", "gundi", "gundigalu", "crater", "craters", "road hole"])
    if not has_pothole_or_crater and any(w in text_lower for w in ["footpath", "sidewalk", "broken footpath", "paving", "curb", "pedestrian path", "foot path"]):
        return {
            "category_name": "Broken Footpaths & Walkways",
            "agency": "BBMP",
            "confidence": 0.96,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Pedestrian footpath / sidewalk damage routed to BBMP."
        }
    if any(w in text_lower for w in ["tree fall", "tree fallen", "branch broken", "storm damage tree", "dangerous tree", "dead tree", "overgrown branch"]):
        return {
            "category_name": "Tree Fall & Dangerous Branches",
            "agency": "BBMP",
            "confidence": 0.96,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Fallen tree or dangerous branches routed to BBMP Forest Cell."
        }
    if any(w in text_lower for w in ["lake", "kere", "lake waste", "lake pollution", "lake sewage"]):
        return {
            "category_name": "Lakes & Water Bodies",
            "agency": "BBMP",
            "confidence": 0.95,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Lake conservation and water body maintenance routed to BBMP Lakes Cell."
        }
    if any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in ["park", "parks", "garden", "playground", "park bench"]):
        return {
            "category_name": "Park Maintenance & Public Gardens",
            "agency": "BBMP",
            "confidence": 0.95,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Public park / garden maintenance routed to BBMP Horticulture."
        }
    if any(w in text_lower for w in ["public toilet", "urinal", "public restroom"]):
        return {
            "category_name": "Public Toilet & Civic Amenities",
            "agency": "BBMP",
            "confidence": 0.95,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Public toilet / sanitation amenity routed to BBMP."
        }
    if any(w in text_lower for w in ["stray dog", "dog bite", "dead animal carcass", "animal removal"]):
        return {
            "category_name": "Stray Animal & Dead Animal Removal",
            "agency": "BBMP",
            "confidence": 0.95,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Stray animal menace / animal removal routed to BBMP Animal Control."
        }
    if any(w in text_lower for w in ["encroachment", "vendors blocking", "illegal shop", "footpath blocked"]):
        return {
            "category_name": "Road & Footpath Encroachment",
            "agency": "BBMP",
            "confidence": 0.94,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Public right-of-way encroachment routed to BBMP."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 9. Core BBMP Roads & Potholes
    # ─────────────────────────────────────────────────────────────────────────
    is_pothole = any(w in text_lower for w in [
        "pothole", "potholes", "gundi", "gundigalu", "crater", "craters", "road pit", "road hole",
        "broken asphalt", "road cracks", "road damage", "road repair",
        "damaged road", "fill pothole", "pothole na", "bad road", "road broken",
        "pothole aagide", "asphalt damaged", "tar road", "uneven road"
    ]) or ("road" in text_lower and any(w in text_lower for w in [
        "damage", "repair", "broken", "cave", "hole", "crater", "asphalt", "fill", "mg road", "severe", "danger", "hazard", "two-wheeler", "vehicles"
    ]))
    if is_pothole:
        return {
            "category_name": "Potholes & Damaged Roads",
            "agency": "BBMP",
            "confidence": 0.98,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Road surface defects, craters, and potholes strictly routed to BBMP Roads."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 9. Core BSWML Solid Waste Management
    # ─────────────────────────────────────────────────────────────────────────
    is_garbage = any(w in text_lower for w in [
        "garbage", "trash", "waste", "kachra", "kasa", "dustbin", "waste collection",
        "illegal dumping", "dumping", "sweeping", "segregation", "black spot", "blackspot",
        "auto tipper", "bswml", "solid waste", "litter"
    ])
    if is_garbage:
        if any(w in text_lower for w in ["burn", "smoke", "fire", "plastic"]):
            cat = "Garbage Burning & Air Pollution"
            conf = 0.98
        elif any(w in text_lower for w in ["not collected", "missed", "van not", "auto tipper"]):
            cat = "Garbage Not Collected"
            conf = 0.96
        elif any(w in text_lower for w in ["irregular", "delay", "late", "timing"]):
            cat = "Irregular Garbage Collection"
            conf = 0.95
        elif any(w in text_lower for w in ["segregat", "wet", "dry"]):
            cat = "Wet & Dry Waste Segregation Issues"
            conf = 0.95
        elif any(w in text_lower for w in ["dump", "roadside", "empty plot", "vacant"]):
            cat = "Illegal Roadside Waste Dumping"
            conf = 0.96
        else:
            cat = "Overflowing Garbage Bins & Blackspots"
            conf = 0.96
        return {
            "category_name": cat,
            "agency": "BSWML",
            "confidence": conf,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Solid waste management issue strictly routed to BSWML."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 10. Core BESCOM Electrical Grid & Power
    # ─────────────────────────────────────────────────────────────────────────
    is_power = any(w in text_lower for w in [
        "power cut", "power outage", "blackout", "no current", "current illa",
        "load shedding", "electricity failure", "power failure", "intermittent power"
    ])
    is_voltage = any(w in text_lower for w in [
        "voltage", "low voltage", "high voltage", "voltage fluctuation", "power surge"
    ])
    is_electric_hazard = any(w in text_lower for w in [
        "electric wire", "live wire", "sparking", "transformer", "electric pole",
        "shock hazard", "bescom", "snapped wire", "tilted pole", "spark", "transformer blast", "exploded"
    ])
    is_electric_billing = any(w in text_lower for w in [
        "electric bill", "electricity bill", "meter reading", "faulty meter", "meter burnt", "tariff"
    ])

    if is_electric_hazard:
        if any(w in text_lower for w in ["transformer", "blast", "explosion"]):
            cat = "Transformer Failure & Sparks"
        elif any(w in text_lower for w in ["wire", "pole", "snapped", "dangling"]):
            cat = "Damaged Electric Poles & Broken Wires"
        else:
            cat = "Exposed Wires & Electrical Hazards"
        return {
            "category_name": cat,
            "agency": "BESCOM",
            "confidence": 0.97,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Electrical hazard / equipment fault routed to BESCOM."
        }
    if is_voltage:
        return {
            "category_name": "Voltage Fluctuation (Low/High)",
            "agency": "BESCOM",
            "confidence": 0.96,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Power voltage fluctuation routed to BESCOM."
        }
    if is_power:
        cat = "Frequent Power Cuts" if any(w in text_lower for w in ["frequent", "repeated", "again"]) else "Power Outage & Blackout"
        return {
            "category_name": cat,
            "agency": "BESCOM",
            "confidence": 0.96,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Electricity outage / power disruption routed to BESCOM."
        }
    if is_electric_billing:
        return {
            "category_name": "Electricity Meter & Billing Issues",
            "agency": "BESCOM",
            "confidence": 0.95,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Electricity meter / billing dispute routed to BESCOM."
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 11. Core BWSSB Drinking Water & Pipelines
    # ─────────────────────────────────────────────────────────────────────────
    is_water_quality = any(w in text_lower for w in [
        "dirty water", "contaminated", "contamination", "muddy", "discoloured", "discolored",
        "bad taste water", "smelly water", "mud in water"
    ])
    is_water_leak = any(w in text_lower for w in [
        "pipeline burst", "pipe leak", "water pipe burst", "pipeline leakage", "water main leak"
    ])
    is_water_supply = any(w in text_lower for w in [
        "no water supply", "water not coming", "dry tap", "drinking water",
        "low water pressure", "neeru barthilla", "kaveri water", "water shortage"
    ])
    is_water_billing = any(w in text_lower for w in ["water bill", "water meter", "rr number"])

    if is_water_quality:
        return {
            "category_name": "Contaminated Drinking Water",
            "agency": "BWSSB",
            "confidence": 0.98,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Contaminated drinking water quality routed to BWSSB."
        }
    if is_water_leak:
        return {
            "category_name": "Water Pipeline Burst & Leakage",
            "agency": "BWSSB",
            "confidence": 0.98,
            "secondary_agency": "BBMP" if "road" in text_lower else None,
            "coordination_reason": SECONDARY_COORDINATION_RULES["pipe_burst_road_damage"]["reason"] if "road" in text_lower else None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Water pipeline burst / leakage routed to BWSSB."
        }
    if is_water_supply:
        cat = "Low Water Pressure" if any(w in text_lower for w in ["low", "pressure", "slow"]) else "No Water Supply"
        return {
            "category_name": cat,
            "agency": "BWSSB",
            "confidence": 0.96,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Drinking water supply disruption routed to BWSSB."
        }
    if is_water_billing:
        return {
            "category_name": "Water Meter & Tanker Issues",
            "agency": "BWSSB",
            "confidence": 0.95,
            "secondary_agency": None,
            "coordination_reason": None,
            "is_conflict": False,
            "needs_manual_review": False,
            "routing_reason": "Water meter / billing issue routed to BWSSB."
        }



    # Inconclusive under deterministic rules: signal AI fallback
    return {
        "category_name": None,
        "agency": None,
        "confidence": 0.0,
        "secondary_agency": None,
        "coordination_reason": None,
        "is_conflict": False,
        "needs_manual_review": False,
        "routing_reason": "No deterministic rule matched; falling back to SentenceTransformers AI embedding model."
    }


def assign_officer_to_complaint(db: Session, complaint: Complaint) -> Optional[Officer]:
    """
    Routes the complaint to the correct department and assigns it to the officer
    with the least amount of active complaints.
    Preserves existing workflow while logging secondary-agency coordination and
    manual review notices when appropriate.
    """
    category = db.query(ComplaintCategory).filter(ComplaintCategory.id == complaint.category_id).first()
    if not category:
        return None

    # Get all active officers in the category's routed department who are "On Duty"
    officers = db.query(Officer).filter(
        Officer.department_id == category.department_id,
        Officer.status == "On Duty"
    ).all()

    if not officers:
        # Fallback to any officer in the department if none are explicitly "On Duty"
        officers = db.query(Officer).filter(
            Officer.department_id == category.department_id
        ).all()

    if not officers:
        return None

    # Calculate load (active complaints) for each officer
    # Active statuses: Registered, Accepted, In Progress
    officer_loads = {}
    for officer in officers:
        active_count = db.query(func.count(Complaint.id)).filter(
            Complaint.assigned_officer_id == officer.id,
            Complaint.status.in_(["Registered", "Accepted", "In Progress"])
        ).scalar()
        officer_loads[officer.id] = (active_count, officer)

    # Find officer with the minimum load
    best_officer_id = min(officer_loads, key=lambda k: officer_loads[k][0])
    best_officer = officer_loads[best_officer_id][1]

    # Assign officer to complaint
    complaint.assigned_officer_id = best_officer.id
    db.flush()

    # Contextual check for secondary agency coordination and conflict flags
    routing_info = resolve_department_routing(
        complaint.description or "",
        complaint.location_address
    )

    # Create notification for officer
    officer_user = db.query(User).filter(User.id == best_officer.user_id).first()
    if officer_user:
        notif_msg = f"A new complaint (ID: {complaint.id}) regarding '{category.name}' has been assigned to you."
        db.add(Notification(
            user_id=officer_user.id,
            complaint_id=complaint.id,
            message=notif_msg
        ))

        # Base status history remark about assignment
        assignment_remark = f"System routed to {category.department.code} and assigned to Officer {officer_user.name}."
        if routing_info.get("secondary_agency"):
            assignment_remark += f" Cross-agency coordination flagged with {routing_info['secondary_agency']}: {routing_info.get('coordination_reason')}"
        if routing_info.get("is_conflict"):
            assignment_remark += f" Note: {routing_info.get('routing_reason')}"

        db.add(ComplaintStatusHistory(
            complaint_id=complaint.id,
            status=complaint.status,
            remarks=assignment_remark,
            changed_by_user_id=complaint.citizen_id
        ))

        # Create citizen notification
        citizen_msg = f"Your complaint has been successfully routed to {category.department.code}. Officer {officer_user.name} has been assigned to resolve it."
        if routing_info.get("secondary_agency"):
            citizen_msg += f" (Secondary coordination with {routing_info['secondary_agency']} flagged for joint resolution)."

        db.add(Notification(
            user_id=complaint.citizen_id,
            complaint_id=complaint.id,
            message=citizen_msg
        ))
        db.flush()

    return best_officer
