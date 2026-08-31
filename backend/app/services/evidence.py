"""
Multimodal Evidence Trust Score Engine (Blueprint Phase 9)
==========================================================
Evaluates the trustworthiness of a citizen's complaint submission by analysing:
  1. Live GPS vs Image EXIF GPS consistency
  2. Timestamp sanity
  3. Computer vision (YOLO) object alignment with complaint category text
  4. Overall composite trust score (0-100) and Trust Level
"""
import os
import math
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

# Optionally use Pillow / piexif to read EXIF data
try:
    from PIL import Image as PILImage
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── YOLO outdoor object indicators (same as ai.py) ────────────────────────────
OUTDOOR_OBJECTS = {
    "car", "truck", "bus", "motorcycle", "bicycle", "person", "dog", "cat",
    "traffic light", "fire hydrant", "stop sign", "bench", "potted plant", "bird"
}
INDOOR_OBJECTS = {"tv", "laptop", "mouse", "keyboard", "cell phone", "sofa", "bed", "refrigerator"}

# Category → expected YOLO objects mapping for vision agreement scoring
CATEGORY_VISION_HINTS: Dict[str, set] = {
    "garbage":           {"person", "car"},
    "pothole":           {"car", "motorcycle", "truck", "bicycle"},
    "water leakage":     {"car", "person"},
    "no water supply":   {"person"},
    "streetlight":       {"car", "truck", "person", "traffic light"},
    "sewage overflow":   {"car", "person"},
    "tree fall":         {"car", "truck", "person"},
    "road damage":       {"car", "motorcycle", "truck", "bicycle"},
    "illegal dumping":   {"car", "person", "truck"},
    "power outage":      {"car", "person"},
    "fallen electric wire": {"car", "person"},
    "traffic signal fault": {"car", "traffic light", "motorcycle", "person"},
    "road encroachment": {"car", "truck"},
    "metro station issue": {"person"},
    "metro track damage": {"person"},
    "metro safety concern": {"person"},
    "illegal construction": {"truck", "car", "person"},
    "park maintenance":  {"person", "bench"},
    "layout encroachment": {"car", "truck", "person"},
    "others":            set(),
}

GPS_THRESHOLD_METERS = 500.0  # GPS mismatch tolerance


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in metres between two GPS coordinates."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _extract_exif_gps(image_path: str) -> Optional[Tuple[float, float]]:
    """Extract (latitude, longitude) from image EXIF metadata, or None."""
    if not PIL_AVAILABLE or not os.path.exists(image_path):
        return None
    try:
        img = PILImage.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None
        gps_info = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for gps_tag_id, gps_val in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_val

        if not gps_info or "GPSLatitude" not in gps_info:
            return None

        def _to_decimal(coords, ref):
            d, m, s = coords
            result = float(d) + float(m) / 60 + float(s) / 3600
            if ref in ("S", "W"):
                result = -result
            return result

        lat = _to_decimal(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
        lon = _to_decimal(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))
        return lat, lon
    except Exception:
        return None


def _vision_agreement(detected_objects: list, category_name: str) -> float:
    """
    Returns a 0.0-1.0 score for how well the detected YOLO objects agree
    with the complaint category.
    """
    cat_key = category_name.lower()
    expected = CATEGORY_VISION_HINTS.get(cat_key, set())
    
    detected_set = set(o.lower() for o in detected_objects)
    is_indoor = bool(detected_set & INDOOR_OBJECTS)
    
    if is_indoor:
        return 0.15  # Strongly suspicious
    
    if not detected_objects:
        return 0.55  # Close-up shot — neutral, common for genuine complaints
    
    is_outdoor = bool(detected_set & OUTDOOR_OBJECTS)
    if not expected:
        return 0.70 if is_outdoor else 0.45
    
    overlap = len(detected_set & expected)
    partial_score = 0.60 + 0.30 * min(overlap / max(len(expected), 1), 1.0)
    return min(0.99, partial_score)


def compute_evidence_trust(
    live_lat: float,
    live_lon: float,
    image_path: Optional[str],
    detected_yolo_objects: Optional[list],
    category_name: str,
    submission_timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Computes the Multimodal Evidence Trust Score for a complaint submission.

    Returns a dict with:
        trust_score          : float 0-100
        trust_level          : "High" | "Medium" | "Low" | "Suspicious"
        live_gps_provided    : bool
        exif_gps_found       : bool
        gps_distance_m       : float | None
        gps_match            : bool
        vision_agreement_score: float
        vision_objects_detected: str (JSON list)
        timestamp_valid      : bool
        verification_details : str (human-readable explanation)
    """
    details = []
    score = 50.0  # Baseline
    
    # ── 1. GPS Live Presence ───────────────────────────────────────────────────
    live_gps_provided = live_lat != 0.0 and live_lon != 0.0
    if live_gps_provided:
        score += 10.0
        details.append("✅ Live GPS coordinates provided.")
    else:
        score -= 15.0
        details.append("⚠️ No live GPS coordinates provided.")

    # ── 2. EXIF GPS Cross-Validation ──────────────────────────────────────────
    exif_gps_found = False
    gps_distance_m: Optional[float] = None
    gps_match = True
    
    if image_path:
        exif_coords = _extract_exif_gps(image_path)
        if exif_coords:
            exif_gps_found = True
            gps_distance_m = _haversine(live_lat, live_lon, exif_coords[0], exif_coords[1])
            if gps_distance_m <= GPS_THRESHOLD_METERS:
                score += 15.0
                gps_match = True
                details.append(f"✅ Photo EXIF GPS matches live location (distance: {gps_distance_m:.0f}m).")
            else:
                score -= 20.0
                gps_match = False
                details.append(f"❌ Photo EXIF GPS is far from live location ({gps_distance_m:.0f}m away — threshold: {GPS_THRESHOLD_METERS:.0f}m).")
        else:
            details.append("ℹ️ No EXIF GPS metadata found in image (common for screenshots/direct uploads).")
    else:
        details.append("ℹ️ No image uploaded; EXIF check skipped.")
    
    # ── 3. Timestamp Sanity Check ─────────────────────────────────────────────
    timestamp_valid = True
    now_utc = datetime.now(timezone.utc)
    if submission_timestamp:
        if submission_timestamp.tzinfo is None:
            submission_timestamp = submission_timestamp.replace(tzinfo=timezone.utc)
        diff_hours = abs((now_utc - submission_timestamp).total_seconds()) / 3600
        if diff_hours > 72:
            timestamp_valid = False
            score -= 10.0
            details.append(f"⚠️ Submission timestamp is {diff_hours:.1f}h old — potential stale report.")
        else:
            score += 5.0
            details.append(f"✅ Submission timestamp is recent ({diff_hours:.1f}h ago).")
    
    # ── 4. Vision Agreement (YOLO category match) ─────────────────────────────
    objects_list = detected_yolo_objects or []
    vision_score = _vision_agreement(objects_list, category_name)
    vision_impact = (vision_score - 0.5) * 40.0  # Normalise: 0.5 baseline = 0 impact
    score += vision_impact
    
    detected_str = json.dumps(objects_list[:10]) if objects_list else "[]"
    if vision_score >= 0.70:
        details.append(f"✅ Image content aligns with '{category_name}' category (score: {vision_score:.2f}).")
    elif vision_score >= 0.45:
        details.append(f"ℹ️ Image content partially aligns with '{category_name}' (score: {vision_score:.2f}).")
    else:
        details.append(f"❌ Image appears to be an indoor or unrelated scene — suspicious (score: {vision_score:.2f}).")
    
    # ── 5. Final Score Clamping & Trust Level Assignment ─────────────────────
    trust_score = max(0.0, min(100.0, score))
    
    if trust_score >= 75:
        trust_level = "High"
    elif trust_score >= 50:
        trust_level = "Medium"
    elif trust_score >= 25:
        trust_level = "Low"
    else:
        trust_level = "Suspicious"
    
    return {
        "trust_score": round(trust_score, 2),
        "trust_level": trust_level,
        "live_gps_provided": live_gps_provided,
        "exif_gps_found": exif_gps_found,
        "gps_distance_m": round(gps_distance_m, 1) if gps_distance_m is not None else None,
        "gps_match": gps_match,
        "vision_agreement_score": round(vision_score, 4),
        "vision_objects_detected": detected_str,
        "timestamp_valid": timestamp_valid,
        "verification_details": " ".join(details),
    }
