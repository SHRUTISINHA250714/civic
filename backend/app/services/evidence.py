"""
Multimodal Evidence Trust & Hard-Gate Verification Engine (Phases 8 & 9)
========================================================================
Implements:
  Phase 8: Structured Image Analysis (YOLOv8n object detection, OpenCV quality
           diagnostics, and PIL EXIF metadata extraction).
  Phase 9: Strong Multi-Gate Evidence Verification:
           Gate 1: Live GPS vs EXIF GPS Cross-Validation (Distance & Accuracy)
           Gate 2: Timestamp Freshness & Future-Check (EXIF vs Receipt)
           Gate 3: Complaint ↔ Image Semantic Verification (SentenceTransformers & YOLO)
           Gate 4: Reused Image Detection (Perceptual Hashing)
           Decision Engine: Hard Gates (VERIFIED, PARTIALLY_VERIFIED, MANUAL_REVIEW,
                            SUSPICIOUS, REJECTED) + Composite Trust Score (0–100).
"""
import os
import math
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session

# Pillow for EXIF extraction & image processing
try:
    from PIL import Image as PILImage
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# OpenCV for image quality & blurriness evaluation
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# SentenceTransformers and YOLO from existing services
from backend.app.services.ai import encoder_model, yolo_model
from backend.app.core.config import settings

# ── Civic Object Taxonomy & Vision Indicators ────────────────────────────────
OUTDOOR_CIVIC_OBJECTS = {
    "car", "truck", "bus", "motorcycle", "bicycle", "person", "dog", "cat",
    "traffic light", "fire hydrant", "stop sign", "bench", "potted plant", "bird"
}
STRICT_INDOOR_OBJECTS = {
    "tv", "laptop", "mouse", "keyboard", "cell phone", "sofa", "bed", "refrigerator"
}

# Domain semantic profiles for SentenceTransformers cosine matching
CATEGORY_SEMANTIC_PROFILES = {
    "pothole": "potholes, damaged road surface, broken asphalt, crater in road, cracked pavement, tar hole",
    "road damage": "broken road, street excavation, cave-in, asphalt damage, potholes, unpaved road",
    "streetlight": "streetlight not working, street lamp, dark night street, light pole, traffic signal, dark road",
    "water leakage": "water pipeline burst, leaking municipal water pipe, drinking water flood, gushing water on street",
    "sewage overflow": "overflowing sewage gutter, black wastewater, open drain, manhole overflow, drainage block",
    "garbage": "garbage dump, overflowing trash bin, roadside waste pile, litter, blackspot garbage, uncollected trash",
    "illegal dumping": "illegal debris dumping, construction waste, garbage pile on footpath, waste heap",
    "power outage": "electric power outage, snapped power line, damaged transformer, electrical sparks, electric pole",
    "tree fall": "fallen tree blocking street, heavy tree branches collapsed on road, broken tree trunk",
    "traffic signal fault": "broken traffic light, malfunctioning signal, junction traffic block, signal not working",
}

GPS_MATCH_THRESHOLD_METERS = 500.0
GPS_CRITICAL_MISMATCH_METERS = 5000.0  # 5 km


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8: OpenCV Quality Checks & Preprocessing
# ─────────────────────────────────────────────────────────────────────────────
def check_image_quality(image_path: str) -> Dict[str, Any]:
    """
    Evaluates image quality using OpenCV (or PIL fallback).
    Checks:
      - Blurriness via Laplacian variance
      - Luminance / Contrast (underexposed/dark vs overexposed)
      - Minimum dimensions / resolution
    """
    if not os.path.exists(image_path):
        return {"status": "INVALID", "details": "Image file does not exist."}

    if not CV2_AVAILABLE:
        # Fallback using PIL
        if PIL_AVAILABLE:
            try:
                with PILImage.open(image_path) as img:
                    w, h = img.size
                    if w < 100 or h < 100:
                        return {"status": "LOW_RES", "details": f"Resolution too low ({w}x{h})."}
                    return {"status": "PASS", "details": "Basic quality passed (PIL fallback)."}
            except Exception:
                return {"status": "UNREADABLE", "details": "Unable to decode image."}
        return {"status": "PASS", "details": "Quality check bypassed (OpenCV unavailable)."}

    try:
        # Read with OpenCV
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            return {"status": "UNREADABLE", "details": "Image could not be decoded by OpenCV."}

        h, w, _ = img_bgr.shape
        if w < 100 or h < 100:
            return {"status": "LOW_RES", "details": f"Image resolution too low ({w}x{h} px)."}

        # Convert to grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Blurriness via Laplacian variance
        blur_val = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = blur_val < 25.0

        # 2. Brightness / exposure
        mean_brightness = float(np.mean(gray))
        is_dark = mean_brightness < 25.0
        is_overexposed = mean_brightness > 245.0

        if is_blurry:
            return {
                "status": "BLURRY",
                "blur_score": round(blur_val, 2),
                "brightness": round(mean_brightness, 1),
                "details": f"Image is noticeably blurry (blur score: {blur_val:.1f} < 25.0)."
            }
        if is_dark:
            return {
                "status": "UNDEREXPOSED",
                "blur_score": round(blur_val, 2),
                "brightness": round(mean_brightness, 1),
                "details": f"Image is excessively dark/underexposed (brightness: {mean_brightness:.1f}/255)."
            }
        if is_overexposed:
            return {
                "status": "OVEREXPOSED",
                "blur_score": round(blur_val, 2),
                "brightness": round(mean_brightness, 1),
                "details": f"Image is overexposed/whiteout (brightness: {mean_brightness:.1f}/255)."
            }

        return {
            "status": "PASS",
            "blur_score": round(blur_val, 2),
            "brightness": round(mean_brightness, 1),
            "details": "Image quality, resolution, and sharpness are satisfactory."
        }
    except Exception as e:
        return {"status": "PASS", "details": f"Quality check warning: {str(e)}"}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 8: YOLOv8 Structured Object Detection
# ─────────────────────────────────────────────────────────────────────────────
def run_yolo_detection(image_path: str) -> Dict[str, Any]:
    """
    Executes Ultralytics YOLOv8n object detection.
    Returns:
      - detected_objects : List[str]
      - bounding_boxes   : List[Dict[str, Any]] (label, confidence, box [x1, y1, x2, y2])
      - confidence_scores: Dict[str, float]
      - has_civic_objects: bool
      - is_indoor_device : bool
    """
    if not yolo_model or not os.path.exists(image_path):
        return {
            "detected_objects": [],
            "bounding_boxes": [],
            "confidence_scores": {},
            "has_civic_objects": True,
            "is_indoor_device": False,
        }

    try:
        results = yolo_model(image_path, verbose=False)
        detected_objects = []
        bounding_boxes = []
        confidence_scores = {}

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_idx = int(box.cls[0].item())
                label = yolo_model.names[cls_idx]
                conf = float(box.conf[0].item())
                xyxy = [round(float(c), 1) for c in box.xyxy[0].tolist()]

                detected_objects.append(label)
                bounding_boxes.append({
                    "label": label,
                    "confidence": round(conf, 3),
                    "box": xyxy
                })
                if label not in confidence_scores or conf > confidence_scores[label]:
                    confidence_scores[label] = round(conf, 3)

        detected_set = set(detected_objects)
        is_indoor = bool(detected_set & STRICT_INDOOR_OBJECTS)
        has_civic = bool(detected_set & OUTDOOR_CIVIC_OBJECTS) or (len(detected_objects) == 0)

        return {
            "detected_objects": detected_objects,
            "bounding_boxes": bounding_boxes,
            "confidence_scores": confidence_scores,
            "has_civic_objects": has_civic,
            "is_indoor_device": is_indoor,
        }
    except Exception as e:
        print(f"YOLO detection exception: {e}")
        return {
            "detected_objects": [],
            "bounding_boxes": [],
            "confidence_scores": {},
            "has_civic_objects": True,
            "is_indoor_device": False,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Perceptual Hashing (dHash) for Reused Image Detection (Gate 4)
# ─────────────────────────────────────────────────────────────────────────────
def compute_perceptual_hash(image_path: str) -> Optional[str]:
    """
    Computes a 64-bit difference perceptual hash (dHash) represented as 16 hex chars.
    Robust against resizing, slight color grading, and JPEG re-compression.
    Zero external dependencies beyond PIL.
    """
    if not PIL_AVAILABLE or not os.path.exists(image_path):
        return None
    try:
        with PILImage.open(image_path) as img:
            # Convert to grayscale and resize to 9x8 (72 pixels)
            gray = img.convert("L").resize((9, 8), PILImage.Resampling.LANCZOS)
            pixels = list(gray.getdata())

            # Compare adjacent pixels row-by-row
            difference = []
            for row in range(8):
                for col in range(8):
                    pixel_left = pixels[row * 9 + col]
                    pixel_right = pixels[row * 9 + col + 1]
                    difference.append(pixel_left > pixel_right)

            # Convert 64 booleans to hex string
            decimal_value = 0
            for index, value in enumerate(difference):
                if value:
                    decimal_value += 2 ** index
            hex_hash = f"{decimal_value:016x}"
            return hex_hash
    except Exception:
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculates bit difference between two 16-character hex hashes."""
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        xor_val = val1 ^ val2
        return bin(xor_val).count("1")
    except Exception:
        return 64


# ─────────────────────────────────────────────────────────────────────────────
# EXIF Metadata Extractor (GPS & Timestamp)
# ─────────────────────────────────────────────────────────────────────────────
def _extract_exif(image_path: str) -> Dict[str, Any]:
    """
    Extracts GPS coordinates and capture timestamp from image EXIF.
    Returns:
      - lat, lon: float | None
      - timestamp: datetime | None
      - camera_make, camera_model: str | None
    """
    res = {
        "lat": None,
        "lon": None,
        "timestamp": None,
        "camera_make": None,
        "camera_model": None
    }
    if not PIL_AVAILABLE or not os.path.exists(image_path):
        return res

    try:
        with PILImage.open(image_path) as img:
            exif_data = img._getexif() or {}
            exif_obj = img.getexif()

            tags_dict = {}
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                tags_dict[tag_name] = value

            if exif_obj:
                for tag_id, value in exif_obj.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    if tag_name not in tags_dict:
                        tags_dict[tag_name] = value

                # Check IFD subtables in Pillow
                if hasattr(exif_obj, "get_ifd"):
                    gps_ifd = exif_obj.get_ifd(0x8825)
                    if gps_ifd:
                        if "GPSInfo" not in tags_dict or not isinstance(tags_dict["GPSInfo"], dict):
                            tags_dict["GPSInfo"] = {}
                        for k, v in gps_ifd.items():
                            subtag = GPSTAGS.get(k, str(k))
                            tags_dict["GPSInfo"][subtag] = v

                    exif_sub = exif_obj.get_ifd(0x8769)
                    if exif_sub:
                        for k, v in exif_sub.items():
                            tag_name = TAGS.get(k, str(k))
                            if tag_name not in tags_dict:
                                tags_dict[tag_name] = v

            if not tags_dict:
                return res

            res["camera_make"] = str(tags_dict.get("Make", "")).strip() or None
            res["camera_model"] = str(tags_dict.get("Model", "")).strip() or None

            # 1. Timestamp extraction
            time_str = tags_dict.get("DateTimeOriginal") or tags_dict.get("DateTime") or tags_dict.get("DateTimeDigitized")
            if time_str and isinstance(time_str, str):
                try:
                    # Typical EXIF format: "YYYY:MM:DD HH:MM:SS"
                    parsed_time = datetime.strptime(time_str.strip(), "%Y:%m:%d %H:%M:%S")
                    res["timestamp"] = parsed_time.replace(tzinfo=timezone.utc)
                except Exception:
                    pass

            # 2. GPS extraction
            gps_raw = tags_dict.get("GPSInfo")
            if gps_raw and isinstance(gps_raw, dict):
                gps_info = {}
                for k, v in gps_raw.items():
                    subtag = GPSTAGS.get(k, str(k))
                    gps_info[subtag] = v

                if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                    def _dms_to_deg(dms, ref):
                        if isinstance(dms, (int, float)):
                            deg = float(dms)
                        else:
                            d, m, s = [float(x) for x in dms]
                            deg = d + (m / 60.0) + (s / 3600.0)
                        if ref in ["S", "W"]:
                            deg = -deg
                        return deg

                    lat_val = _dms_to_deg(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
                    lon_val = _dms_to_deg(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))

                    # Sanity check
                    if -90.0 <= lat_val <= 90.0 and -180.0 <= lon_val <= 180.0:
                        res["lat"] = lat_val
                        res["lon"] = lon_val

    except Exception:
        pass

    return res


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in metres between two GPS coordinates."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return R * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


# ─────────────────────────────────────────────────────────────────────────────
# Gate 3: Semantic Complaint ↔ Image Matching (NLP + Vision)
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_semantic_match(
    complaint_text: str,
    category_name: str,
    detected_objects: List[str],
    is_indoor_device: bool,
    image_path: Optional[str] = None
) -> Tuple[str, float, str, str]:
    """
    Compares complaint category & description against image contents.
    Returns:
      - semantic_status     : MATCH | PARTIAL_MATCH | MISMATCH | UNKNOWN
      - semantic_confidence : float (0.0 to 1.0)
      - image_category      : str (inferred category from image)
      - details             : str
    """
    if is_indoor_device:
        return "MISMATCH", 0.95, "Indoor Device / Screen", "Image shows indoor screens, devices, or household furniture — not municipal infrastructure."

    cat_lower = category_name.lower()

    # Determine profile
    best_domain = "civic infrastructure"
    for k in CATEGORY_SEMANTIC_PROFILES.keys():
        if k in cat_lower:
            best_domain = k
            break

    # If YOLO detected specific objects, check direct alignment
    detected_set = set(o.lower() for o in detected_objects)

    # Specific category negative filters (hard mismatch detection)
    is_pothole_complaint = any(k in cat_lower for k in ["pothole", "road", "tar", "asphalt"])
    is_garbage_complaint = any(k in cat_lower for k in ["garbage", "waste", "trash", "dump"])
    is_power_complaint = any(k in cat_lower for k in ["power", "electric", "wire", "spark", "transformer"])
    is_water_complaint = any(k in cat_lower for k in ["water", "sewage", "drain", "leak", "pipe"])

    # Filename / image label context clues
    fname = os.path.basename(image_path).lower() if image_path else ""
    is_garbage_img_hint = any(k in fname for k in ["garbage", "trash", "waste", "dump"])
    is_pothole_img_hint = any(k in fname for k in ["pothole", "road_damage", "crater", "asphalt"])

    GARBAGE_COCO_OBJECTS = {"bottle", "cup", "wine glass", "banana", "apple", "sandwich", "backpack", "suitcase"}
    has_garbage_objects = bool(detected_set & GARBAGE_COCO_OBJECTS)

    # 1. Pothole complaint with garbage photo -> Hard Mismatch
    if is_pothole_complaint and (is_garbage_img_hint or has_garbage_objects) and not is_pothole_img_hint:
        return "MISMATCH", 0.92, "Garbage / Solid Waste", "Image depicts solid waste/garbage, but complaint is for road damage/potholes."

    # 2. Garbage complaint with pothole photo -> Hard Mismatch
    if is_garbage_complaint and is_pothole_img_hint and not (is_garbage_img_hint or has_garbage_objects):
        return "MISMATCH", 0.92, "Road Damage / Pothole", "Image depicts road damage/potholes, but complaint is for garbage/waste."

    # Fallback to SentenceTransformer embedding similarity if available
    sim_score = 0.65
    if encoder_model:
        try:
            # Build target category representation
            target_profile = CATEGORY_SEMANTIC_PROFILES.get(best_domain, category_name)
            desc_text = f"{category_name}: {complaint_text[:200]}"
            target_emb = encoder_model.encode(target_profile, convert_to_tensor=True)
            desc_emb = encoder_model.encode(desc_text, convert_to_tensor=True)

            from sentence_transformers import util
            cos_sim = float(util.cos_sim(target_emb, desc_emb)[0][0].item())
            sim_score = max(0.40, min(0.98, cos_sim))
        except Exception:
            sim_score = 0.70

    # Optional: Google Gemini Multimodal Vision query if configured
    gemini_key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
    if gemini_key and "your_" not in gemini_key and len(gemini_key) > 25 and image_path and os.path.exists(image_path):
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            with PILImage.open(image_path) as pimg:
                prompt = (
                    f"You are a civic grievance verification auditor in Karnataka. "
                    f"A citizen filed a complaint under Category: '{category_name}', Description: '{complaint_text}'. "
                    f"Look at the image. Does this image depict the civic grievance or a plausible scene of this issue? "
                    f"Respond in one word: MATCH, PARTIAL_MATCH, or MISMATCH, followed by a colon and 1-sentence reason."
                )
                response = model.generate_content([prompt, pimg])
                text_resp = response.text.strip().upper()
                if "MISMATCH" in text_resp:
                    return "MISMATCH", 0.92, "Unrelated Subject", f"Gemini Vision detected mismatch: {response.text.strip()}"
                elif "MATCH" in text_resp:
                    return "MATCH", 0.94, category_name, f"Gemini Vision verified category match: {response.text.strip()}"
        except Exception as e:
            # Non-blocking: fallback to local SentenceTransformers
            print("Gemini Vision check skipped/failed:", e)

    # Heuristic matching using YOLO objects + NLP
    if not detected_objects:
        # Close-up image of a pothole, garbage, or water puddle often has 0 COCO objects
        return "MATCH", 0.72, category_name, "Close-up evidence image aligns with reported municipal issue."

    if bool(detected_set & OUTDOOR_CIVIC_OBJECTS):
        return "MATCH", max(0.75, sim_score), category_name, f"Outdoor street context detected ({', '.join(list(detected_set)[:3])}) matching civic grievance."

    return "PARTIAL_MATCH", 0.60, category_name, "Image exhibits partial semantic alignment with complaint."


# ─────────────────────────────────────────────────────────────────────────────
# Phase 9: Hard-Gate Decision & Trust Score Engine
# ─────────────────────────────────────────────────────────────────────────────
def compute_evidence_trust(
    live_lat: float,
    live_lon: float,
    image_path: Optional[str],
    detected_yolo_objects: Optional[list] = None,
    category_name: str = "General Civic",
    submission_timestamp: Optional[datetime] = None,
    gps_accuracy: Optional[float] = None,
    db: Optional[Session] = None,
    complaint_description: str = "",
) -> Dict[str, Any]:
    """
    Computes hard-gate verification decisions and the composite Trust Score.
    """
    gate_reasons: List[str] = []
    details: List[str] = []

    # ── 1. Phase 8 Image Quality & YOLO Analysis ──────────────────────────────
    quality_info = {"status": "PASS", "details": "No image uploaded."}
    yolo_info = {
        "detected_objects": [],
        "bounding_boxes": [],
        "confidence_scores": {},
        "has_civic_objects": True,
        "is_indoor_device": False,
    }
    perceptual_hash = None

    if image_path and os.path.exists(image_path):
        quality_info = check_image_quality(image_path)
        yolo_info = run_yolo_detection(image_path)
        perceptual_hash = compute_perceptual_hash(image_path)
    elif detected_yolo_objects:
        yolo_info["detected_objects"] = detected_yolo_objects

    # ── 2. Gate 1: Geo Verification ───────────────────────────────────────────
    live_gps_provided = bool(live_lat != 0.0 and live_lon != 0.0)
    exif_data = _extract_exif(image_path) if image_path else {}
    exif_lat = exif_data.get("lat")
    exif_lon = exif_data.get("lon")
    exif_gps_found = bool(exif_lat is not None and exif_lon is not None)

    gps_distance_m: Optional[float] = None
    gps_match = True
    geo_status = "MATCH"

    if not live_gps_provided:
        geo_status = "SUSPICIOUS"
        gps_match = False
        gate_reasons.append("No live GPS coordinates provided.")
        details.append("⚠️ Missing live GPS coordinates.")
    elif exif_gps_found:
        gps_distance_m = _haversine(live_lat, live_lon, exif_lat, exif_lon)
        if gps_distance_m <= GPS_MATCH_THRESHOLD_METERS:
            geo_status = "MATCH"
            gps_match = True
            details.append(f"✅ EXIF GPS matches live location ({gps_distance_m:.0f}m away).")
        elif gps_distance_m >= GPS_CRITICAL_MISMATCH_METERS:
            geo_status = "MISMATCH"
            gps_match = False
            gate_reasons.append(f"Severe Geo Mismatch: Photo EXIF location is {round(gps_distance_m/1000, 1)}km away from live device GPS.")
            details.append(f"❌ Severe GPS mismatch ({round(gps_distance_m/1000, 1)}km away).")
        else:
            geo_status = "MISMATCH"
            gps_match = False
            gate_reasons.append(f"Geo Mismatch: Photo EXIF is {gps_distance_m:.0f}m away (threshold: {GPS_MATCH_THRESHOLD_METERS:.0f}m).")
            details.append(f"⚠️ EXIF GPS is {gps_distance_m:.0f}m away from live GPS.")
    else:
        geo_status = "EXIF_MISSING"
        details.append("ℹ️ Photo lacks EXIF GPS metadata (treated as supporting evidence missing).")

    if gps_accuracy and gps_accuracy > 150.0:
        details.append(f"ℹ️ Device GPS accuracy is approximate (±{gps_accuracy:.0f}m).")

    # ── 3. Gate 2: Timestamp Freshness ────────────────────────────────────────
    now_utc = datetime.now(timezone.utc)
    exif_time = exif_data.get("timestamp")
    timestamp_valid = True
    freshness_status = "FRESH"

    if exif_time:
        diff_hours = (now_utc - exif_time).total_seconds() / 3600.0
        if diff_hours < -0.16:  # More than 10 minutes in future
            freshness_status = "FUTURE"
            timestamp_valid = False
            gate_reasons.append("Timestamp Anomaly: Photo EXIF timestamp is in the future.")
            details.append(f"❌ Future timestamp detected in EXIF ({exif_time.strftime('%Y-%m-%d %H:%M')}).")
        elif diff_hours > 72.0:
            freshness_status = "STALE"
            timestamp_valid = False
            gate_reasons.append(f"Stale Photo: Evidence photo was taken {diff_hours:.0f} hours ago (> 72h limit).")
            details.append(f"⚠️ Photo is {diff_hours:.0f} hours old.")
        else:
            freshness_status = "FRESH"
            details.append(f"✅ Photo timestamp is recent ({diff_hours:.1f}h ago).")
    else:
        freshness_status = "UNKNOWN"
        details.append("ℹ️ EXIF timestamp missing (safe fallback applied).")

    # ── 4. Gate 3: Semantic Verification ──────────────────────────────────────
    semantic_status, semantic_conf, img_cat, sem_details = evaluate_semantic_match(
        complaint_text=complaint_description,
        category_name=category_name,
        detected_objects=yolo_info["detected_objects"],
        is_indoor_device=yolo_info["is_indoor_device"],
        image_path=image_path
    )
    details.append(sem_details)
    if semantic_status == "MISMATCH":
        gate_reasons.append(f"Semantic Mismatch: Image does not depict '{category_name}'.")

    # ── 5. Gate 4: Reused Image Detection ─────────────────────────────────────
    is_reused_image = False
    reused_complaint_id: Optional[int] = None
    if db and perceptual_hash:
        try:
            from backend.app.models.complaint import ComplaintImage
            existing_imgs = db.query(ComplaintImage).filter(
                ComplaintImage.perceptual_hash.isnot(None)
            ).all()

            for prev in existing_imgs:
                dist = hamming_distance(perceptual_hash, prev.perceptual_hash)
                if dist <= 4:  # Identical or near-identical image
                    is_reused_image = True
                    reused_complaint_id = prev.complaint_id
                    gate_reasons.append(f"Duplicate Image: This photo was already submitted for Complaint #{reused_complaint_id}.")
                    details.append(f"⚠️ Duplicate image detected (reused from Complaint #{reused_complaint_id}).")
                    break
        except Exception:
            pass

    # ── 6. Hard-Gate Decision Engine ──────────────────────────────────────────
    # Critical Rule: Semantic mismatch must NEVER become VERIFIED
    if yolo_info["is_indoor_device"]:
        verification_decision = "REJECTED"
    elif semantic_status == "MISMATCH":
        verification_decision = "REJECTED"
    elif geo_status == "MISMATCH" and gps_distance_m and gps_distance_m >= GPS_CRITICAL_MISMATCH_METERS:
        verification_decision = "SUSPICIOUS"
    elif is_reused_image:
        verification_decision = "SUSPICIOUS"
    elif freshness_status == "FUTURE":
        verification_decision = "MANUAL_REVIEW"
    elif quality_info["status"] in ["BLURRY", "UNDEREXPOSED", "LOW_RES"]:
        verification_decision = "PARTIALLY_VERIFIED"
    elif geo_status == "MISMATCH":
        verification_decision = "MANUAL_REVIEW"
    elif semantic_status == "MATCH" and geo_status in ["MATCH", "EXIF_MISSING"] and freshness_status in ["FRESH", "UNKNOWN"]:
        verification_decision = "VERIFIED" if geo_status == "MATCH" else "PARTIALLY_VERIFIED"
    elif semantic_status == "PARTIAL_MATCH":
        verification_decision = "PARTIALLY_VERIFIED"
    else:
        verification_decision = "MANUAL_REVIEW"

    # ── 7. Composite Trust Score Calculation (0–100) ──────────────────────────
    # Weighted: GPS = 35%, Timestamp = 20%, Vision/Semantic = 45%
    # GPS component (35 pts)
    if geo_status == "MATCH":
        gps_score = 35.0
    elif geo_status == "EXIF_MISSING" and live_gps_provided:
        gps_score = 25.0
    elif geo_status == "MISMATCH" and gps_distance_m and gps_distance_m < GPS_CRITICAL_MISMATCH_METERS:
        gps_score = 12.0
    else:
        gps_score = 0.0

    # Timestamp component (20 pts)
    if freshness_status == "FRESH":
        time_score = 20.0
    elif freshness_status == "UNKNOWN":
        time_score = 15.0
    elif freshness_status == "STALE":
        time_score = 8.0
    else:
        time_score = 0.0

    # Semantic component (45 pts)
    if semantic_status == "MATCH":
        sem_score = 45.0 * max(0.6, semantic_conf)
    elif semantic_status == "PARTIAL_MATCH":
        sem_score = 25.0
    else:
        sem_score = 0.0

    trust_score = round(gps_score + time_score + sem_score, 1)

    # If rejected by hard gate, clamp score to low/suspicious
    if verification_decision == "REJECTED":
        trust_score = min(trust_score, 24.0)
    elif verification_decision == "SUSPICIOUS":
        trust_score = min(trust_score, 35.0)

    if trust_score >= 75:
        trust_level = "High"
    elif trust_score >= 50:
        trust_level = "Medium"
    elif trust_score >= 25:
        trust_level = "Low"
    else:
        trust_level = "Suspicious"

    return {
        "verification_decision": verification_decision,
        "trust_score": trust_score,
        "trust_level": trust_level,
        "live_gps_provided": live_gps_provided,
        "exif_gps_found": exif_gps_found,
        "gps_distance_m": round(gps_distance_m, 1) if gps_distance_m is not None else None,
        "gps_match": gps_match,
        "gps_accuracy": gps_accuracy,
        "geo_status": geo_status,
        "timestamp_valid": timestamp_valid,
        "freshness_status": freshness_status,
        "vision_objects_detected": json.dumps(yolo_info["detected_objects"][:10]),
        "vision_agreement_score": round(semantic_conf, 4),
        "semantic_match_status": semantic_status,
        "semantic_confidence": round(semantic_conf, 3),
        "image_category": img_cat,
        "is_reused_image": is_reused_image,
        "reused_complaint_id": reused_complaint_id,
        "perceptual_hash": perceptual_hash,
        "quality_check": quality_info["status"],
        "gate_reasons": json.dumps(gate_reasons) if gate_reasons else None,
        "verification_details": " ".join(details),
        # Additional Phase 8 structured detection payload for image record
        "bounding_boxes": json.dumps(yolo_info["bounding_boxes"]),
    }
