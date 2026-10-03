import os
import re
import time

# Bypassing the TensorFlow/Keras 3 compatibility issue (MUST be set before importing transformers)
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import logging
from typing import Tuple, Dict, Any, Optional
from langdetect import detect, detect_langs
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)
try:
    from sentence_transformers import SentenceTransformer, util
except Exception as e:
    print("Warning: could not import SentenceTransformer:", e)
    SentenceTransformer = None
    util = None
from ultralytics import YOLO

# Initialize models
print("Initializing AI SentenceTransformer Model...")
try:
    # Small model (90MB), runs fast on CPU
    encoder_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("SentenceTransformer loaded.")
except Exception as e:
    print("Failed to load SentenceTransformer:", e)
    encoder_model = None

print("Initializing AI YOLO Model...")
try:
    # Lightweight COCO model, downloads automatically if not cached (~12MB)
    yolo_model = YOLO("yolov8n.pt")
    print("YOLO model loaded.")
except Exception as e:
    print("Failed to load YOLO:", e)
    yolo_model = None

# ─────────────────────────────────────────────────────────────────────────────
# Master Taxonomy & Authority Metadata for the 4 Karnataka Civic Authorities:
# 1. BBMP: Roads, Drains, Street Lighting, Parks & Municipal Civic Services
# 2. BESCOM: Electricity Distribution & Consumer Services
# 3. BWSSB: Water Supply & Underground Drainage/Sewerage
# 4. BSWML: Solid Waste Management & C&D Waste Management
# ─────────────────────────────────────────────────────────────────────────────

AGENCY_METADATA = {
    "BBMP": {
        "name": "Bruhat Bengaluru Mahanagara Palike",
        "code": "BBMP",
        "domain": "Roads, Drains, Street Lighting & Civic Services",
        "description": "Municipal civic services: roads, drains, street lighting, footpaths, parks, public health, lakes, trees, civic infrastructure."
    },
    "BESCOM": {
        "name": "Bangalore Electricity Supply Company Limited",
        "code": "BESCOM",
        "domain": "Electricity Distribution & Consumer Services",
        "description": "Electricity distribution, power outages, electrical faults, meters, poles/lines, billing/service complaints."
    },
    "BWSSB": {
        "name": "Bangalore Water Supply and Sewerage Board",
        "code": "BWSSB",
        "domain": "Water Supply & Underground Drainage/Sewerage",
        "description": "Water supply, low pressure, leakage, sewer overflow/blockage, water quality, connections, billing."
    },
    "BSWML": {
        "name": "Bengaluru Solid Waste Management Limited",
        "code": "BSWML",
        "domain": "Solid-Waste & C&D-Waste Management",
        "description": "Solid-waste and C&D-waste management, garbage collection, dumping/black spots, waste transportation, processing, C&D waste."
    }
}

# Hierarchical Taxonomy (Agency -> Category -> Subcategory / Problem)
CATEGORY_HIERARCHY = {
    # ── BBMP (Roads, Drains, Streetlights & Municipal Services) ──
    "Potholes & Damaged Roads": {
        "agency": "BBMP",
        "category": "Roads",
        "subcategory": "Potholes & Damaged Roads",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Pothole": {
        "agency": "BBMP",
        "category": "Roads",
        "subcategory": "Pothole",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Road Damage": {
        "agency": "BBMP",
        "category": "Roads",
        "subcategory": "Road Damage & Surface Fault",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Broken Footpaths & Walkways": {
        "agency": "BBMP",
        "category": "Footpaths",
        "subcategory": "Broken Footpath & Walkways",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Blocked Stormwater Drains & Waterlogging": {
        "agency": "BBMP",
        "category": "Storm-water drains",
        "subcategory": "Blocked Stormwater Drain & Flooding",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Damaged Streetlights": {
        "agency": "BBMP",
        "category": "Street lighting",
        "subcategory": "Streetlight Not Working / Broken Lamp",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Streetlight": {
        "agency": "BBMP",
        "category": "Street lighting",
        "subcategory": "Streetlight Not Working",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Tree Fall & Dangerous Branches": {
        "agency": "BBMP",
        "category": "Trees",
        "subcategory": "Fallen Tree & Dangerous Branches",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Tree Fall": {
        "agency": "BBMP",
        "category": "Trees",
        "subcategory": "Fallen Tree",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Park Maintenance & Public Gardens": {
        "agency": "BBMP",
        "category": "Parks",
        "subcategory": "Park Maintenance & Broken Equipment",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Low"
    },
    "Lakes & Water Bodies": {
        "agency": "BBMP",
        "category": "Lakes",
        "subcategory": "Lake Waste & Encroachment",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Public Toilet & Civic Amenities": {
        "agency": "BBMP",
        "category": "Public sanitation",
        "subcategory": "Public Toilet Maintenance & Sanitation",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "Low"
    },
    "Road & Footpath Encroachment": {
        "agency": "BBMP",
        "category": "Public property",
        "subcategory": "Encroachment on Public Land & Footpath",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Construction Debris & Road Cave-in": {
        "agency": "BBMP",
        "category": "Road obstruction",
        "subcategory": "Road Cave-in & Obstruction",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Stray Animal & Dead Animal Removal": {
        "agency": "BBMP",
        "category": "Public sanitation",
        "subcategory": "Stray & Dead Animal Removal",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Others": {
        "agency": "BBMP",
        "category": "Civic infrastructure",
        "subcategory": "General Civic Complaint",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "Low"
    },

    # ── BESCOM (Electricity Distribution) ──────────────────────
    "Power Outage & Blackout": {
        "agency": "BESCOM",
        "category": "Power supply",
        "subcategory": "Power Outage & Blackout",
        "requires_image": False,
        "requires_gps": False,
        "default_priority": "High"
    },
    "Power Outage": {
        "agency": "BESCOM",
        "category": "Power supply",
        "subcategory": "Power Outage",
        "requires_image": False,
        "requires_gps": False,
        "default_priority": "High"
    },
    "Frequent Power Cuts": {
        "agency": "BESCOM",
        "category": "Power supply",
        "subcategory": "Frequent & Repeated Power Cuts",
        "requires_image": False,
        "requires_gps": False,
        "default_priority": "Medium"
    },
    "Voltage Fluctuation (Low/High)": {
        "agency": "BESCOM",
        "category": "Voltage",
        "subcategory": "Voltage Fluctuation (Low/High)",
        "requires_image": False,
        "requires_gps": False,
        "default_priority": "Medium"
    },
    "Transformer Failure & Sparks": {
        "agency": "BESCOM",
        "category": "Transformer",
        "subcategory": "Transformer Failure & Sparks",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Damaged Electric Poles & Broken Wires": {
        "agency": "BESCOM",
        "category": "Poles",
        "subcategory": "Damaged Electric Pole & Broken Wire",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Fallen Electric Wire": {
        "agency": "BESCOM",
        "category": "Electrical lines",
        "subcategory": "Fallen & Dangling Live Wire",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Exposed Wires & Electrical Hazards": {
        "agency": "BESCOM",
        "category": "Street electrical safety",
        "subcategory": "Exposed Electrical Equipment & Hazard",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Streetlight Power Supply Fault": {
        "agency": "BESCOM",
        "category": "Electrical infrastructure",
        "subcategory": "Feeder Line & Power Supply Fault",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Electricity Meter & Billing Issues": {
        "agency": "BESCOM",
        "category": "Billing",
        "subcategory": "Faulty Meter & Billing Amount Dispute",
        "requires_image": False,
        "requires_gps": False,
        "default_priority": "Low"
    },

    # ── BWSSB (Water Supply & Sewerage) ────────────────────────
    "No Water Supply": {
        "agency": "BWSSB",
        "category": "Water supply",
        "subcategory": "No Water Supply & Dry Taps",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Low Water Pressure": {
        "agency": "BWSSB",
        "category": "Water supply",
        "subcategory": "Low Water Pressure & Timing Issue",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Water Pipeline Burst & Leakage": {
        "agency": "BWSSB",
        "category": "Water leakage",
        "subcategory": "Water Pipeline Burst & Road Leakage",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Water Leakage": {
        "agency": "BWSSB",
        "category": "Water leakage",
        "subcategory": "Pipeline Leakage",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Contaminated Drinking Water": {
        "agency": "BWSSB",
        "category": "Water quality",
        "subcategory": "Dirty & Contaminated Drinking Water",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Sewage Overflow & Gutter Water": {
        "agency": "BWSSB",
        "category": "Sewage overflow",
        "subcategory": "Sewer Overflow on Road & Property",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Sewage Overflow": {
        "agency": "BWSSB",
        "category": "Sewage overflow",
        "subcategory": "Sewage Overflow",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Blocked Sewer Line & Manhole Overflow": {
        "agency": "BWSSB",
        "category": "Sewer blockage",
        "subcategory": "Blocked Sewer & Clogged Pipeline",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Damaged Manhole Cover & Missing Lid": {
        "agency": "BWSSB",
        "category": "Manhole",
        "subcategory": "Open Manhole & Broken Manhole Cover",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Water Meter & Tanker Issues": {
        "agency": "BWSSB",
        "category": "Meter",
        "subcategory": "Faulty Water Meter & Tanker Supply",
        "requires_image": False,
        "requires_gps": False,
        "default_priority": "Low"
    },

    # ── BSWML (Solid Waste & C&D Waste Management) ─────────────
    "Garbage Not Collected": {
        "agency": "BSWML",
        "category": "Door-to-door collection",
        "subcategory": "Garbage Not Collected / Missed Collection",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Garbage": {
        "agency": "BSWML",
        "category": "Door-to-door collection",
        "subcategory": "Garbage Collection Issue",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Irregular Garbage Collection": {
        "agency": "BSWML",
        "category": "Door-to-door collection",
        "subcategory": "Auto-Tipper Not Arriving / Collection Delay",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Overflowing Garbage Bins & Blackspots": {
        "agency": "BSWML",
        "category": "Garbage accumulation",
        "subcategory": "Garbage Pile & Overflowing Bins",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Illegal Roadside Waste Dumping": {
        "agency": "BSWML",
        "category": "Illegal dumping",
        "subcategory": "Waste Dumped on Road & Footpath",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Illegal Dumping": {
        "agency": "BSWML",
        "category": "Illegal dumping",
        "subcategory": "Illegal Dumping Location",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Foul Smell & Waste Health Hazard": {
        "agency": "BSWML",
        "category": "Garbage accumulation",
        "subcategory": "Foul Smell & Stinking Waste Hazard",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "High"
    },
    "Garbage Burning & Air Pollution": {
        "agency": "BSWML",
        "category": "Waste burning",
        "subcategory": "Garbage Burning & Plastic Burning",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Critical"
    },
    "Wet & Dry Waste Segregation Issues": {
        "agency": "BSWML",
        "category": "Segregation",
        "subcategory": "Mixed Waste & Source Segregation Violation",
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "Low"
    },
    "Bulk & Construction Waste Dumping": {
        "agency": "BSWML",
        "category": "C&D waste",
        "subcategory": "Construction & Demolition Debris on Road",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "Medium"
    },
    "Dead Animal Waste on Road": {
        "agency": "BSWML",
        "category": "Garbage accumulation",
        "subcategory": "Dead Animal & Organic Waste Removal",
        "requires_image": True,
        "requires_gps": True,
        "default_priority": "High"
    }
}

CATEGORIES = list(CATEGORY_HIERARCHY.keys())

CATEGORY_PROTOTYPES = {
    # BBMP
    "Potholes & Damaged Roads": "pothole road crater street hole cracked asphalt deep pit driving hazard road cave-in road damage bbmp",
    "Pothole": "pothole road crater hole on street deep pothole asphalt damaged",
    "Road Damage": "road damage broken asphalt damaged street surface uneven road",
    "Broken Footpaths & Walkways": "broken footpath pavement pedestrian sidewalk damaged tiles curb broken walking danger",
    "Blocked Stormwater Drains & Waterlogging": "blocked stormwater drain rainwater flooding waterlogging choked rajakaluve storm drain road flooded",
    "Damaged Streetlights": "damaged streetlight broken streetlamp pole fixture light bulb cracked fallen streetlight pole light not working dark road",
    "Streetlight": "streetlight dark road street light off bulb fused no lighting at night bbmp",
    "Park Maintenance & Public Gardens": "park maintenance public garden dirty broken park bench overgrown weeds public park neglected",
    "Lakes & Water Bodies": "lake waste lake pollution encroachment sewage entering lake illegal dumping near lake",
    "Public Toilet & Civic Amenities": "public toilet dirty unusable broken civic amenity unhygienic public restroom",
    "Road & Footpath Encroachment": "encroachment vendors blocking footpath illegal shop road encroached pedestrian path blocked",
    "Tree Fall & Dangerous Branches": "tree fallen tree fall heavy branch broken fallen across road storm damage blocking street",
    "Tree Fall": "tree fallen down blocked road broken tree branch storm damage",
    "Construction Debris & Road Cave-in": "construction debris building waste concrete debris dumped on road road sinkhole cave in",
    "Stray Animal & Dead Animal Removal": "stray dog menace dead animal carcass on street dog bite danger cattle blocking road",
    "Others": "general civic grievance public nuisance municipal complaint bbmp",

    # BESCOM
    "Power Outage & Blackout": "power cut power outage electricity blackout no current power failure load shedding bescom",
    "Power Outage": "power outage electricity cut blackout no current bescom",
    "Frequent Power Cuts": "frequent power cuts intermittent power power trips recurring electricity outage",
    "Voltage Fluctuation (Low/High)": "voltage fluctuation low voltage high voltage appliance damage power surge",
    "Transformer Failure & Sparks": "transformer failure transformer sparking transformer blast smoke fire burnt transformer",
    "Damaged Electric Poles & Broken Wires": "damaged electric pole broken electric wire live wire dangling snapped cable pole tilted",
    "Fallen Electric Wire": "fallen electric wire live wire sparking wire danger electric shock",
    "Exposed Wires & Electrical Hazards": "exposed electric wire open junction box shock hazard naked wire hanging on footpath",
    "Streetlight Power Supply Fault": "feeder line power fault power supply to poles interrupted line fault",
    "Electricity Meter & Billing Issues": "electricity meter fault burnt meter incorrect electric bill faulty meter reading bescom tariff",

    # BWSSB
    "No Water Supply": "no water supply drinking water not coming dry taps kaveri water not supplied bwssb",
    "Low Water Pressure": "low water pressure trickle water supply insufficient water supply trickle",
    "Water Pipeline Burst & Leakage": "water pipeline burst main pipe leak drinking water wasted running water on road flooding",
    "Water Leakage": "water leakage pipe leak drinking water wasted pipeline broken",
    "Contaminated Drinking Water": "contaminated water dirty muddy water foul smelling drinking water sewage mixed in water",
    "Sewage Overflow & Gutter Water": "sewage overflow gutter water stinking sewer water overflowing onto street drainage backup",
    "Sewage Overflow": "sewage overflow drainage overflow gutter sewage on road",
    "Blocked Sewer Line & Manhole Overflow": "blocked sewer line choked manhole overflow overflowing drainage sewage chamber blocked",
    "Damaged Manhole Cover & Missing Lid": "damaged manhole cover open manhole missing lid dangerous hole open sewer pit",
    "Water Meter & Tanker Issues": "water meter broken faulty water bill BWSSB tanker water problem",

    # BSWML
    "Garbage Not Collected": "garbage not collected waste collection missed door to door waste collector not coming bswml auto tipper",
    "Garbage": "garbage trash waste dump litter dustbin overflowing sweeping not done bswml",
    "Irregular Garbage Collection": "irregular garbage collection waste van not coming on time trash collection delayed auto tipper",
    "Overflowing Garbage Bins & Blackspots": "overflowing garbage bin waste blackspot huge pile of garbage overflowing dustbin",
    "Illegal Roadside Waste Dumping": "illegal dumping roadside garbage waste dumped on empty plot unauthorized trash disposal",
    "Illegal Dumping": "illegal dumping trash waste disposal unauthorized dump",
    "Foul Smell & Waste Health Hazard": "foul smell stinking garbage rotten waste health hazard flies and mosquitoes breeding",
    "Garbage Burning & Air Pollution": "garbage burning toxic smoke burning plastic waste bonfire of garbage air pollution",
    "Wet & Dry Waste Segregation Issues": "waste segregation wet and dry waste mixed waste vehicle not segregating",
    "Bulk & Construction Waste Dumping": "bulk waste dumping debris construction material dumped on roadside bswml c and d waste",
    "Dead Animal Waste on Road": "dead animal carcass rotting dead dog on roadside dead animal waste"
}

# Category to Department exact mapping for ONLY the 4 authorities
CATEGORY_TO_DEPARTMENT = {cat: meta["agency"] for cat, meta in CATEGORY_HIERARCHY.items()}


# Extensive Kannada & Kanglish Civic Vocabulary Mapping
KANNADA_CIVIC_DICTIONARY = {
    # ── Potholes & Roads (BBMP) ───────────────────────
    "ಇಂದಿರಾ": "Indiranagar",
    "ನಗರ": "Nagar",
    "ಅಡಿ": "ft",
    "ದೊಡ್ಡ": "severe",
    "ಹಾಳಾಗಿದೆ": "road damaged",
    "ಅಪಾಯಕಾರಿ": "hazard",
    "ಬಿದ್ದಿದೆ": "formed",
    "ಮತ್ತು": "and",
    "ಗುಂಡಿ": "pothole",
    "ಗುಂಡಿಗಳು": "potholes",
    "ಗುಂಡಿಯಿದೆ": "pothole exists",
    "ಗುಂಡಿಬಿದ್ದಿದೆ": "pothole formed",
    "ಗುಂಡಿಯಾಗಿದೆ": "pothole formed",
    "ಹಳ್ಳ": "pothole",
    "ಹೊಂಡ": "crater",
    "ರಸ್ತೆ": "road",
    "ರಸ್ತೆಯಲ್ಲಿ": "on the road",
    "ರಸ್ತೇಲಿ": "on the road",
    "ರಸ್ತೆಯ": "road",
    "ರೋಡ್": "road",
    "ಫುಟ್‌ಪಾತ್": "footpath",
    "ಕಾಲುದಾರಿ": "footpath",
    "ಡಾಂಬರು": "asphalt",
    "ಕಂದಕ": "trench",
    "ರಸ್ತೆ ಹಾಳಾಗಿದೆ": "road is completely damaged broken asphalt",
    "ಗಟಾರ ಮುಚ್ಚಳ": "manhole cover drain lid",
    "ಮರ ಬಿದ್ದಿದೆ": "tree fallen blocking road",
    "ಮರದ ಕೊಂಬೆ": "tree branch fallen",
    "ಬೀದಿ ನಾಯಿ": "stray dog",
    "ಸತ್ತ ಪ್ರಾಣಿ": "dead animal carcass",
    "ಕಟ್ಟಡ ತ್ಯಾಜ್ಯ": "construction debris",

    # ── Garbage & Solid Waste (BSWML) ─────────────────
    "ಕಸ": "garbage solid waste trash",
    "ಕಸದ": "garbage waste",
    "ಕಸದ ರಾಶಿ": "garbage dump pile of waste",
    "ಕಸದ ತೊಟ್ಟಿ": "garbage dustbin overflowing",
    "ಕಸದಬುಟ್ಟಿ": "dustbin garbage bin",
    "ಕಸಗುಡಿಸಿಲ್ಲ": "sweeping not done garbage not collected",
    "ತ್ಯಾಜ್ಯ": "solid waste garbage trash",
    "ಕಸ ಎತ್ತಿಲ್ಲ": "garbage not collected missed collection",
    "ಕಸದ ಗಾಡಿ": "waste collection vehicle",
    "ದುರ್ನಾತ": "foul smell stinking waste",
    "ವಾಸನೆ": "stinking bad smell rotten garbage",
    "ಕಸ ಸುಡುವುದು": "garbage burning toxic smoke",
    "ಪ್ಲಾಸ್ಟಿಕ್ ತ್ಯಾಜ್ಯ": "plastic waste dump",

    # ── Water & Sewage (BWSSB) ────────────────────────
    "ನೀರು": "water supply",
    "ನೀರಿನ": "water pipeline",
    "ನೀರು ಬರ್ತಿಲ್ಲ": "no water supply dry taps",
    "ನೀರುಬರ್ತಿಲ್ಲ": "no water supply dry taps",
    "ನೀರಿಲ್ಲ": "no water supply dry taps drinking water",
    "ನಲ್ಲಿಯಲ್ಲಿ ನೀರಿಲ್ಲ": "no water in tap dry taps",
    "ನಲ್ಲಿ": "water tap",
    "ನಲ್ಲಿಯಲ್ಲಿ": "in the tap",
    "ನೀರು ಸರಬರಾಜು ಇಲ್ಲ": "no municipal water supply dry tap",
    "ನೀರಿನ ಸೋರಿಕೆ": "water pipeline leakage burst",
    "ಪೈಪ್ ಒಡೆದಿದೆ": "pipeline burst water leaking",
    "ಪೈಪ್": "water pipe",
    "ಚರಂಡಿ": "sewage drainage gutter",
    "ಚರಂಡಿ ನೀರು": "sewage overflow dirty gutter water",
    "ಗಟಾರ": "gutter drainage sewer",
    "ಮ್ಯಾನ್ಹೋಲ್": "manhole sewer chamber",
    "ಮ್ಯಾನ್‌ಹೋಲ್": "manhole drain cover",
    "ಕೊಳಚೆ ನೀರು": "contaminated dirty sewage water",
    "ಕುಡಿಯುವ ನೀರು": "drinking water supply",

    # ── Electricity (BESCOM) ──────────────────────────
    "ಕರೆಂಟ್": "electricity power supply",
    "ಕರೆಂಟಿಲ್ಲ": "power outage blackout no electricity",
    "ಕರೆಂಟ್ ಇಲ್ಲ": "power outage blackout no current",
    "ಇಲ್ಲ": "not available outage",
    "ಕಟ್ ಆಗಿದೆ": "power cut failure shut down",
    "ವಿದ್ಯುತ್": "electricity power",
    "ವಿದ್ಯುತ್ ಕಡಿತ": "power cut power failure",
    "ವಿದ್ಯುತ್ ಕಂಬ": "electric pole damaged pole",
    "ಕಂಬ": "electric pole",
    "ವೈರ್": "electric wire cable",
    "ವೈರ್ ಬಿದ್ದಿದೆ": "live electric wire fallen on road danger",
    "ತಂತಿ": "electric wire cable",
    "ಸ್ಪಾರ್ಕ್": "electric spark sparking hazard",
    "ಕಿಡಿ": "sparks from transformer electric wire",
    "ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್": "transformer failure burnt",
    "ಬೆಸ್ಕಾಂ": "bescom electricity board",
    "ಬೀದಿ ದೀಪ": "streetlight street lamp",
    "ಬೀದಿ ದೀಪಗಳು": "streetlights",
    "ದೀಪ ಉರಿಯುತ್ತಿಲ್ಲ": "streetlight not working dark road",
}

# Common Romanized Kannada / Kanglish civic keyword mapping
KANGLISH_CIVIC_MAP = {
    "gundi": "pothole",
    "gundigalu": "potholes",
    "gundi ide": "pothole is on road",
    "gundi biddide": "pothole formed crater",
    "halla": "pothole",
    "doddha": "severe",
    "dodda": "severe",
    "ide": "is",
    "haalagide": "damaged hazard",
    "haalaagide": "damaged hazard",
    "halagide": "damaged hazard",
    "rasthe": "road",
    "raste": "road",
    "rastheyalli": "on the road",
    "rasteyalli": "on the road",
    "rastele": "on the road",
    "footpath": "footpath",
    "kasa": "garbage",
    "kachra": "garbage",
    "kachada": "garbage",
    "waste dump": "garbage dump",
    "smell barthide": "foul smell garbage",
    "current illa": "power outage",
    "current cut": "power cut",
    "vidyuth": "electricity",
    "wire biddide": "electric wire fallen",
    "kamba": "electric pole",
    "transformer spark": "transformer sparking",
    "bescom": "bescom",
    "neeru barthilla": "no water supply",
    "neeru supply illa": "no water supply",
    "pipeline burst": "pipeline burst",
    "pipe leak": "water pipe leak",
    "charandi": "sewage overflow",
    "gatara": "gutter drain",
    "sewage": "sewage overflow",
    "manhole": "manhole chamber",
    "bmtc": "bmtc bus",
    "bmtc bus": "bmtc bus",
    "bus banthilla": "bus delayed",
    "bus delay": "bus delay",
    "bus stop illa": "bus stop issue",
    "light uriyalla": "streetlight not working",
    "mara biddide": "tree fallen",
}

# Common Romanized Hindi / Hinglish civic keyword mapping
HINGLISH_CIVIC_MAP = {
    "gaddha": "pothole",
    "gaddhe": "potholes",
    "bada": "severe",
    "baddi": "severe",
    "badi": "severe",
    "bahut": "very",
    "bohot": "very",
    "bohut": "very",
    "khatarnak": "hazard",
    "sadak": "road",
    "par": "on",
    "pe": "on",
    "mein": "in",
    "me": "in",
    "hai": "is",
    "h": "is",
    "nahi": "not",
    "nahin": "not",
    "nhi": "not",
    "kya": "what",
    "kachra": "garbage",
    "ganda": "dirty contaminated",
    "pani": "water",
    "paani": "water",
    "bijli": "electricity",
    "gaya": "outage",
    "gaye": "outage",
    "aaraha": "coming",
    "aaya": "arrived",
    "samasya": "problem",
    "galli": "street",
    "rasta": "road",
    "naali": "drain sewer",
    "nali": "drain",
    "khulla": "open dangerous",
}

INDIC_MARKER_WORDS = set(list(KANGLISH_CIVIC_MAP.keys()) + list(HINGLISH_CIVIC_MAP.keys()) + [
    "hai", "h", "nahi", "nahin", "nhi", "kya", "bada", "baddha", "badi", "gaddha", "gaddhe",
    "bahut", "bohot", "bohut", "khatarnak", "samasya", "sadak", "par", "mein", "me",
    "ka", "ki", "ke", "ko", "se", "aur", "pe", "paani", "pani", "ganda", "kachra",
    "bijli", "gaya", "gaye", "aaraha", "aaya", "karoo", "karo", "raha", "rahe", "rahi",
    "gundi", "ide", "iddhe", "biddide", "biddidhe", "biddira", "swalpa", "rasteyalli",
    "rastele", "raste", "tumba", "thumba", "nodidara", "agide", "aagide", "haalaagide",
    "halagide", "ilva", "illva", "illa", "iradilla", "niru", "neeru", "bartha", "barilla",
    "koodale", "kudale", "beku", "madbeku", "nodi", "kettogide", "bandh", "karet",
    "kurentu", "myaanhollu", "gataar", "naali", "rasta", "khulla"
])

def contains_kannada_script(text: str) -> bool:
    """Checks if string contains Kannada Unicode characters (0x0C80 to 0x0CFF)."""
    return any('\u0C80' <= ch <= '\u0CFF' for ch in text)

def translate_text(text: str) -> Tuple[str, str, float]:
    """
    Detects language (Kannada, English, Kanglish, Hinglish) and translates to English.
    Removes the language gate that skips translation when detected language is 'en'.
    Translation runs unless text is high-confidence English with no Indic/Kanglish/Hinglish marker words.
    Returns (translated_text, detected_lang, time_taken).
    """
    start_time = time.time()
    text = text.strip()
    if not text:
        return "", "en", 0.0

    # 1. Check for Kannada Unicode script
    has_kannada_script = contains_kannada_script(text)
    
    # 2. Check for Indic/Kanglish/Hinglish marker words
    words_lower = set(re.findall(r'\b\w+\b', text.lower()))
    has_indic_markers = bool(words_lower.intersection(INDIC_MARKER_WORDS)) or \
                         any(k in text.lower() for k in KANGLISH_CIVIC_MAP.keys()) or \
                         any(k in text.lower() for k in HINGLISH_CIVIC_MAP.keys())

    # 3. Language detection for display metadata
    detected_lang = "en"
    high_confidence_en = False

    if has_kannada_script:
        detected_lang = "kn"
    elif has_indic_markers:
        detected_lang = "kn-en"  # Indic transliterated (Kanglish / Hinglish)
    else:
        try:
            langs = detect_langs(text)
            if langs:
                top_lang = langs[0]
                detected_lang = top_lang.lang
                if top_lang.lang == "en" and top_lang.prob > 0.95:
                    high_confidence_en = True
        except Exception:
            detected_lang = "en"

    # 4. Translation Guard:
    # Skip translation ONLY IF langdetect reports high-confidence 'en' AND there are NO Indic/Kanglish/Hinglish markers AND no Kannada script.
    if high_confidence_en and not has_indic_markers and not has_kannada_script:
        return text, "en", round(time.time() - start_time, 4)

    # 5. Translation Execution
    translated_text = text
    translated_online = False

    # Tier 1: Online GoogleTranslator API
    try:
        translator = GoogleTranslator(source='auto', target='en')
        candidate = translator.translate(text)
        if candidate and len(candidate.strip()) > 1 and candidate.strip().lower() != text.strip().lower():
            translated_text = candidate.strip()
            translated_online = True
    except Exception as e:
        logger.warning("Online GoogleTranslator failed (%s). Proceeding with dictionary/normalizer fallback.", e)
        translated_online = False

    # Tier 2: Linguistic civic dictionary normalizer (always enriches or falls back)
    # Pass 1: Multi-word phrase matching on full text BEFORE single-word tokenization
    working_text = text
    
    # Collect all multi-word keys (keys containing a space) across all three dictionaries
    multi_word_pairs = []
    for d in (KANNADA_CIVIC_DICTIONARY, KANGLISH_CIVIC_MAP, HINGLISH_CIVIC_MAP):
        for k, v in d.items():
            if " " in k.strip():
                multi_word_pairs.append((k.strip(), v))
    
    # Sort by phrase key length descending (longest phrase first)
    multi_word_pairs.sort(key=lambda x: len(x[0]), reverse=True)

    for phrase_key, eng_val in multi_word_pairs:
        if contains_kannada_script(phrase_key):
            if phrase_key in working_text:
                working_text = working_text.replace(phrase_key, f" {eng_val} ")
        else:
            pattern = re.compile(re.escape(phrase_key), re.IGNORECASE)
            if pattern.search(working_text):
                working_text = pattern.sub(f" {eng_val} ", working_text)

    # Pass 2: Single-word tokenization & matching on remaining working_text
    enriched_tokens = []
    for word in working_text.split():
        clean_word = word.strip(",.!?\"'()[]{}")
        clean_lower = clean_word.lower()
        if clean_word in KANNADA_CIVIC_DICTIONARY:
            enriched_tokens.append(KANNADA_CIVIC_DICTIONARY[clean_word])
        elif clean_lower in KANGLISH_CIVIC_MAP:
            enriched_tokens.append(KANGLISH_CIVIC_MAP[clean_lower])
        elif clean_lower in HINGLISH_CIVIC_MAP:
            enriched_tokens.append(HINGLISH_CIVIC_MAP[clean_lower])
        else:
            # Substring stem check for Kannada / Indic inflections (single-word keys only)
            matched = False
            for k_key, eng_val in KANNADA_CIVIC_DICTIONARY.items():
                if " " not in k_key and k_key in clean_word:
                    enriched_tokens.append(eng_val)
                    matched = True
                    break
            if not matched:
                # Strip raw Kannada script characters if unmapped
                clean_ascii = "".join([c for c in clean_word if not ('\u0C80' <= c <= '\u0CFF')])
                if clean_ascii.strip():
                    enriched_tokens.append(clean_ascii.strip())

    dictionary_translated = " ".join([t for t in enriched_tokens if t.strip()])

    # If online translation failed or left untranslated Kannada script, use Tier 2 dictionary translation
    if not translated_online or contains_kannada_script(translated_text):
        translated_text = dictionary_translated if dictionary_translated.strip() else text

    # Ensure no residual Kannada script remains in final translated_text
    if contains_kannada_script(translated_text):
        translated_text = "".join([c for c in translated_text if not ('\u0C80' <= c <= '\u0CFF')])
        translated_text = " ".join(translated_text.split())

    if not translated_text or not translated_text.strip():
        logger.warning("Translation yielded empty result for input '%s'. Falling back to raw text.", text)
        translated_text = text

    time_taken = round(time.time() - start_time, 4)
    return translated_text, detected_lang, time_taken

def classify_complaint(text: str) -> Tuple[str, float]:
    """
    Classifies complaint text into predefined categories using SentenceTransformer semantic similarity
    combined with high-precision domain keyword intent scoring strictly across the 4 Karnataka Civic Authorities:
    - BBMP: Roads, Footpaths, Stormwater Drains, Streetlights, Trees, Parks, Lakes, Civic Services
    - BESCOM: Power Supply, Voltage, Lines & Poles, Transformers, Meters & Billing
    - BWSSB: Water Supply, Pipeline Leakage, Quality, Sewerage & Drainage, Sewage Overflow, Manholes
    - BSWML: Door-to-Door Collection, Garbage Accumulation, Illegal Dumping, Burning, C&D Waste
    """
    text_lower = text.lower()

    # 1. Streetlight signal (STRICT RULE: Municipal street lighting routes to BBMP, NOT BESCOM)
    is_streetlight = any(w in text_lower for w in [
        "streetlight", "street light", "dark road", "street lamp", "light uriyalla",
        "light not working", "streetlamp", "flickering light", "broken lamp",
        "bidi dipa", "beedi deepa", "no street light", "bulb fused", "lamp post"
    ])

    # 2. BBMP Civic signals
    is_pothole = any(w in text_lower for w in ["pothole", "gundi", "crater", "road pit", "road hole", "road cave-in", "broken asphalt", "road cracks"])
    is_footpath = any(w in text_lower for w in ["footpath", "sidewalk", "broken footpath", "paving", "curb", "pedestrian path", "foot path"])
    is_drain = any(w in text_lower for w in ["stormwater", "waterlogging", "rain flooding", "rainwater", "rajakaluve", "storm drain", "flood point", "water logging"])
    is_tree = any(w in text_lower for w in ["tree fall", "tree fallen", "branch broken", "storm damage tree", "dangerous tree", "dead tree", "overgrown branch"])
    is_lake = any(w in text_lower for w in ["lake", "kere", "lake waste", "lake pollution", "lake sewage"])
    is_park = any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in ["park", "parks", "garden", "playground", "park bench"])
    is_road = any(w in text_lower for w in ["road damage", "asphalt", "broken road", "rasthe", "road cut", "road divider", "median"])
    is_sanitation = any(w in text_lower for w in ["public toilet", "urinal", "stray dog", "dead animal carcass", "animal removal", "encroachment"])

    # 3. BESCOM Electrical signals
    is_power = any(w in text_lower for w in [
        "power cut", "power outage", "blackout", "no current", "current illa",
        "load shedding", "electricity failure", "power failure", "intermittent power"
    ])
    is_voltage = any(w in text_lower for w in ["voltage", "low voltage", "high voltage", "voltage fluctuation", "power surge"])
    is_electric_hazard = any(w in text_lower for w in [
        "electric wire", "live wire", "sparking", "transformer", "electric pole",
        "shock hazard", "bescom", "snapped wire", "tilted pole", "spark", "transformer blast", "exploded"
    ])
    is_electric_billing = any(w in text_lower for w in ["electric bill", "electricity bill", "meter reading", "faulty meter", "meter burnt", "tariff"])

    # 4. BWSSB Water & Sewerage signals
    is_water_quality = any(w in text_lower for w in [
        "dirty water", "contaminated", "contamination", "muddy", "discoloured", "discolored",
        "foul water", "stinking water", "bad smell water", "bad taste water", "smelly water"
    ])
    is_water_leak = any(w in text_lower for w in [
        "pipeline burst", "pipe leak", "water leak", "water pipe burst", "pipeline leakage", "running water on road"
    ])
    is_water_supply = any(w in text_lower for w in [
        "no water supply", "water not coming", "dry tap", "drinking water",
        "low water pressure", "neeru barthilla", "kaveri water", "water shortage"
    ])
    is_sewage = any(w in text_lower for w in [
        "sewage", "gutter", "drainage", "manhole", "sewer line", "charandi", "gatara",
        "sewage overflow", "sewer overflow", "blocked sewer", "manhole open", "broken manhole"
    ])
    is_water_billing = any(w in text_lower for w in ["water bill", "water meter", "rr number", "bwssb tanker"])

    # 5. BSWML Solid Waste signals
    is_garbage = any(w in text_lower for w in [
        "garbage", "trash", "waste", "kachra", "kasa", "dustbin", "waste collection",
        "illegal dumping", "dumping", "sweeping", "foul smell", "stinking waste",
        "garbage burning", "plastic burning", "waste burning", "segregation",
        "black spot", "blackspot", "auto tipper", "c&d", "construction debris",
        "demolition waste", "bswml"
    ])

    # ── Priority Rule-Based Direct Category Assignment ─────────────────────
    # Streetlight explicitly routes to BBMP
    if is_streetlight:
        return "Damaged Streetlights", 0.96

    # Electricity & Power (BESCOM) - high hazard priority
    if is_electric_hazard:
        if any(w in text_lower for w in ["transformer", "blast", "explosion"]):
            return "Transformer Failure & Sparks", 0.96
        if any(w in text_lower for w in ["wire", "pole", "snapped", "dangling"]):
            return "Damaged Electric Poles & Broken Wires", 0.96
        if "spark" in text_lower:
            return "Transformer Failure & Sparks", 0.96
        return "Exposed Wires & Electrical Hazards", 0.95
    if is_voltage:
        return "Voltage Fluctuation (Low/High)", 0.95
    if is_power:
        if any(w in text_lower for w in ["frequent", "repeated", "again"]):
            return "Frequent Power Cuts", 0.94
        return "Power Outage & Blackout", 0.96
    if is_electric_billing:
        return "Electricity Meter & Billing Issues", 0.94

    # Water & Sewerage (BWSSB)
    if is_water_quality:
        return "Contaminated Drinking Water", 0.96
    if is_water_leak:
        return "Water Pipeline Burst & Leakage", 0.96
    if is_water_supply:
        if "low" in text_lower or "pressure" in text_lower:
            return "Low Water Pressure", 0.94
        return "No Water Supply", 0.96
    if is_sewage:
        if any(w in text_lower for w in ["manhole", "cover", "lid", "open"]):
            return "Damaged Manhole Cover & Missing Lid", 0.96
        if any(w in text_lower for w in ["block", "chok"]):
            return "Blocked Sewer Line & Manhole Overflow", 0.95
        return "Sewage Overflow & Gutter Water", 0.95
    if is_water_billing:
        return "Water Meter & Tanker Issues", 0.93

    # Solid Waste Management (BSWML)
    if is_garbage:
        if any(w in text_lower for w in ["burn", "smoke", "fire", "plastic"]):
            return "Garbage Burning & Air Pollution", 0.96
        if any(w in text_lower for w in ["not collected", "missed", "van not", "auto tipper"]):
            return "Garbage Not Collected", 0.96
        if any(w in text_lower for w in ["c&d", "construction", "demolition", "debris"]):
            return "Bulk & Construction Waste Dumping", 0.95
        if any(w in text_lower for w in ["dump", "roadside", "empty plot", "vacant"]):
            return "Illegal Roadside Waste Dumping", 0.94
        if any(w in text_lower for w in ["smell", "stink", "rotten"]):
            return "Foul Smell & Waste Health Hazard", 0.93
        if any(w in text_lower for w in ["segregat", "wet", "dry"]):
            return "Wet & Dry Waste Segregation Issues", 0.92
        return "Overflowing Garbage Bins & Blackspots", 0.94

    # Potholes, Roads & Civic Services (BBMP)
    if is_pothole:
        return "Potholes & Damaged Roads", 0.96
    if is_footpath:
        return "Broken Footpaths & Walkways", 0.95
    if is_drain:
        return "Blocked Stormwater Drains & Waterlogging", 0.95
    if is_tree:
        return "Tree Fall & Dangerous Branches", 0.95
    if is_lake:
        return "Lakes & Water Bodies", 0.94
    if is_park:
        return "Park Maintenance & Public Gardens", 0.93
    if is_road:
        return "Potholes & Damaged Roads", 0.91
    if is_sanitation:
        if any(w in text_lower for w in ["toilet", "urinal"]):
            return "Public Toilet & Civic Amenities", 0.92
        if any(w in text_lower for w in ["animal", "dog", "carcass"]):
            return "Stray Animal & Dead Animal Removal", 0.92
        return "Road & Footpath Encroachment", 0.91

    # Fallback to SentenceTransformer semantic similarity across the 4 authorities
    if not encoder_model:
        return "Others", 0.50

    try:
        category_texts = [CATEGORY_PROTOTYPES[cat] for cat in CATEGORIES]
        category_embeddings = encoder_model.encode(category_texts, convert_to_tensor=True)
        text_embedding = encoder_model.encode(text, convert_to_tensor=True)

        cos_scores = util.cos_sim(text_embedding, category_embeddings)[0]

        best_idx = cos_scores.argmax().item()
        confidence = float(cos_scores[best_idx].item())
        normalized_confidence = max(0.2, min(0.99, confidence))

        return CATEGORIES[best_idx], normalized_confidence
    except Exception as e:
        print("Classification failed:", e)
        return "Others", 0.50

def classify_complaint_structured(text: str) -> Dict[str, Any]:
    """
    Returns full hierarchical classification for the 4 Karnataka Civic Authorities:
    {
      "agency": "BWSSB",
      "category": "Sewage overflow",
      "subcategory": "Sewage Overflow",
      "priority": "High",
      "confidence": 0.94,
      "requires_image": true,
      "requires_gps": true,
      "department_code": "BWSSB",
      "department_name": "Bangalore Water Supply and Sewerage Board",
      "category_name": "Sewage Overflow & Gutter Water"
    }
    """
    cat_name, confidence = classify_complaint(text)
    priority, prio_conf = predict_priority(text, cat_name)

    meta = CATEGORY_HIERARCHY.get(cat_name, {
        "agency": CATEGORY_TO_DEPARTMENT.get(cat_name, "BBMP"),
        "category": "Civic infrastructure",
        "subcategory": cat_name,
        "requires_image": False,
        "requires_gps": True,
        "default_priority": "Medium"
    })

    agency = meta["agency"]
    agency_info = AGENCY_METADATA.get(agency, {
        "name": "Bruhat Bengaluru Mahanagara Palike",
        "code": agency,
        "domain": "Civic Services"
    })

    return {
        "agency": agency,
        "category": meta["category"],
        "subcategory": meta["subcategory"],
        "priority": priority,
        "confidence": round(confidence, 2),
        "requires_image": meta.get("requires_image", False),
        "requires_gps": meta.get("requires_gps", True),
        "department_code": agency,
        "department_name": agency_info["name"],
        "category_name": cat_name,
        "predicted_category_name": cat_name,
    }

def predict_priority(
    text: str,
    category_name: str,
    impact_count: int = 1,
    location_address: Optional[str] = None,
    cat_conf: float = 0.85,
    evidence_trust_score: float = 50.0
) -> Tuple[str, float]:
    """
    Explainable Hybrid Priority Score (0.0 to 1.0):
      - 35% Category Risk (Default domain severity)
      - 25% Emergency Signals (Urgency & danger keywords)
      - 20% Duplicate / Impact Count (Increases priority as more citizens link reports)
      - 10% Situation Context (High-traffic roads, junctions, schools, hospitals)
      - 10% AI / Evidence Confidence (YOLO & evidence verification trust)

    Emergency Overrides:
      Incidents involving fire, live wires, flooding, or injury risk strictly override to 'Critical'.
    """
    text_lower = (text or "").lower()
    address_lower = (location_address or "").lower()
    combined_text = f"{text_lower} {address_lower}"

    # ── 1. Emergency Overrides (Fire, Live Wires, Flooding, Injury Risk) ──────
    emergency_override_keywords = [
        # Fire
        "fire", "burning", "toxic smoke", "smoke coming", "bonfire",
        # Live Wires & Electrical
        "live wire", "broken electric wire", "snapped wire", "snapped cable",
        "sparking", "transformer blast", "transformer explosion", "sparking transformer",
        "exposed wire", "shock hazard", "current leak",
        # Flooding
        "flooding", "severe flooding", "waterlogging", "rain flood", "water entering",
        "pipeline burst", "sinkhole", "road cave-in", "canal burst", "overflowing drainage storm",
        # Injury Risk
        "injury", "hospital", "life threatening", "severe accident", "open manhole",
        "manhole open", "drowning hazard", "electrocution", "fatal", "dangerous hole"
    ]
    is_emergency_override = any(kw in combined_text for kw in emergency_override_keywords)

    # ── 2. Category Risk Component (35%) ─────────────────────────────────────
    critical_categories = {
        "Transformer Failure & Sparks", "Damaged Electric Poles & Broken Wires",
        "Exposed Wires & Electrical Hazards", "Damaged Manhole Cover & Missing Lid",
        "Contaminated Drinking Water", "Garbage Burning & Air Pollution", "Fallen Electric Wire"
    }
    high_categories = {
        "Potholes & Damaged Roads", "Blocked Stormwater Drains & Waterlogging", "Construction Debris & Road Cave-in",
        "Power Outage & Blackout", "Power Outage", "No Water Supply", "Water Pipeline Burst & Leakage",
        "Sewage Overflow & Gutter Water", "Blocked Sewer Line & Manhole Overflow", "Damaged Bus & Passenger Safety",
        "Unsafe Driving & Rash Driving", "Garbage Not Collected", "Overflowing Garbage Bins & Blackspots",
        "Foul Smell & Waste Health Hazard", "Tree Fall & Dangerous Branches", "Tree Fall", "Pothole", "Water Leakage",
        "Sewage Overflow", "Garbage", "Lakes & Water Bodies", "Distribution Feeder & Cable Fault"
    }
    medium_categories = {
        "Broken Footpaths & Walkways", "Streetlights Not Working", "Damaged Streetlights",
        "Low Water Pressure", "Voltage Fluctuation (Low/High)", "Streetlight Power Supply Fault",
        "Irregular Garbage Collection", "Park Maintenance & Public Gardens", "Public Toilet & Civic Amenities",
        "Wet & Dry Waste Segregation Issues", "Stray Animal & Dead Animal Removal", "Public Toilet Maintenance & Sanitation"
    }

    if category_name in critical_categories:
        category_score = 1.0
    elif category_name in high_categories:
        category_score = 0.75
    elif category_name in medium_categories:
        category_score = 0.50
    else:
        category_score = 0.25

    # ── 3. Emergency Signals Component (25%) ─────────────────────────────────
    if is_emergency_override:
        emergency_signal_score = 1.0
    else:
        secondary_urgency = [
            "hazard", "danger", "accident", "crater", "cannot walk", "traffic jam",
            "blocked", "stinking", "dark road", "elderly", "kids", "children", "urgent", "deep hole"
        ]
        matches = sum(1 for kw in secondary_urgency if kw in combined_text)
        if matches >= 2:
            emergency_signal_score = 0.75
        elif matches == 1:
            emergency_signal_score = 0.50
        else:
            emergency_signal_score = 0.15

    # ── 4. Duplicate / Impact Count Component (20%) ──────────────────────────
    # Increases priority as more citizens link reports for the same problem
    n_reports = max(1, impact_count)
    if n_reports == 1:
        impact_score = 0.20
    elif n_reports == 2:
        impact_score = 0.45
    elif n_reports == 3:
        impact_score = 0.70
    elif n_reports == 4:
        impact_score = 0.85
    else:
        impact_score = 1.00

    # ── 5. Situation Context Component (10%) ─────────────────────────────────
    context_keywords = [
        "main road", "highway", "ring road", "junction", "cross", "signal",
        "market", "school", "college", "hospital", "clinic", "bus stand",
        "bus stop", "metro", "station", "flyover", "arterial", "traffic", "crowded"
    ]
    has_high_context = any(kw in combined_text for kw in context_keywords)
    situation_score = 1.0 if has_high_context else 0.30

    # ── 6. AI / Evidence Confidence Component (10%) ──────────────────────────
    confidence_norm = float(cat_conf) if cat_conf is not None else 0.85
    trust_norm = (float(evidence_trust_score) / 100.0) if evidence_trust_score is not None else 0.50
    ai_confidence_score = min(1.0, max(0.20, (confidence_norm * 0.60) + (trust_norm * 0.40)))

    # ── Composite Hybrid Score ────────────────────────────────────────────────
    hybrid_score = (
        (0.35 * category_score) +
        (0.25 * emergency_signal_score) +
        (0.20 * impact_score) +
        (0.10 * situation_score) +
        (0.10 * ai_confidence_score)
    )

    # ── Emergency Overrides strictly take precedence ──────────────────────────
    if is_emergency_override or category_name in critical_categories:
        return "Critical", 0.98

    # Priority level mapping based on composite hybrid score
    if hybrid_score >= 0.70:
        priority = "Critical"
    elif hybrid_score >= 0.50:
        priority = "High"
    elif hybrid_score >= 0.32:
        priority = "Medium"
    else:
        priority = "Low"

    return priority, round(min(0.99, max(0.60, hybrid_score)), 2)

def verify_image(image_path: str, category_name: str) -> Tuple[bool, float]:
    """
    Verifies if the uploaded image matches a municipal/outdoor street context using YOLO.
    Checks for the presence of street elements like roads, cars, poles, etc.
    """
    if not yolo_model:
        # Fallback if YOLO failed to load
        return True, 0.75
        
    if not os.path.exists(image_path):
        return False, 0.0
        
    try:
        # Run YOLO inference
        results = yolo_model(image_path, verbose=False)
        
        # Extract detected class names
        detected_objects = []
        for r in results:
            for c in r.boxes.cls:
                detected_objects.append(yolo_model.names[int(c)])
                
        print(f"YOLO detected objects in image: {detected_objects}")
        
        # Define street/outdoor objects that validate municipal complaints
        outdoor_indicators = {
            "car", "truck", "bus", "motorcycle", "bicycle", "person", "dog", "cat", 
            "traffic light", "fire hydrant", "stop sign", "bench", "potted plant"
        }
        
        # Verify based on detected objects
        matching_indicators = [obj for obj in detected_objects if obj in outdoor_indicators]
        
        # Heuristics:
        # If the image contains a computer screen, cell phone, or strictly indoor objects like sofa, bed, etc., reject it
        indoor_indicators = {"tv", "laptop", "mouse", "keyboard", "cell phone", "sofa", "bed", "refrigerator"}
        is_indoor_device = any(obj in detected_objects for obj in indoor_indicators)
        
        # Verified if outdoor elements present, and not an indoor screenshot/device photo
        if len(matching_indicators) > 0 and not is_indoor_device:
            # Verified
            confidence = min(0.99, 0.70 + (0.05 * len(detected_objects)))
            return True, confidence
        elif len(detected_objects) == 0:
            # No objects detected at all (e.g. close-up of a road hole or garbage pile)
            # This is normal for close-up complaint shots, so we verify but with moderate confidence
            return True, 0.65
        elif is_indoor_device:
            # Device screen / indoor shot
            return False, 0.90
        else:
            # Only indoor items found
            return False, 0.70
            
    except Exception as e:
        print("YOLO image verification failed:", e)
        # Fallback
        return True, 0.50

def get_detected_objects(image_path: str) -> list:
    """
    Returns list of YOLO-detected class name strings for a given image.
    Used to feed into the Evidence Trust Engine.
    """
    if not yolo_model or not os.path.exists(image_path):
        return []
    try:
        results = yolo_model(image_path, verbose=False)
        detected = []
        for r in results:
            for c in r.boxes.cls:
                detected.append(yolo_model.names[int(c)])
        return detected
    except Exception as e:
        print("YOLO detection failed:", e)
        return []

def transcribe_audio(audio_path: str) -> Tuple[str, str]:
    """
    Attempts to transcribe an audio file to text.
    Tries SpeechRecognition library first; falls back to a placeholder message.
    Returns (transcribed_text, source) where source is 'speech_recognition' or 'fallback'.
    """
    if not os.path.exists(audio_path):
        return "", "fallback"
    
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
        # Try Google Speech Recognition (free tier, requires internet)
        text = recognizer.recognize_google(audio_data, language="kn-IN,en-IN")
        print(f"Audio transcribed (Google STT): {text[:80]}...")
        return text, "speech_recognition"
    except ImportError:
        print("SpeechRecognition library not installed. Using audio upload stub.")
    except Exception as e:
        print(f"STT transcription failed: {e}")
    
    # Fallback: indicate that voice was uploaded but transcription unavailable
    return "[Voice complaint uploaded — transcription unavailable. Officer will review audio.]", "fallback"
