import math
import logging
from typing import Tuple, Optional, Any, List, Dict
from sqlalchemy.orm import Session
from sentence_transformers import util
from backend.app.models.complaint import Complaint
from backend.app.services.ai import encoder_model, translate_text

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates distance in meters between two GPS coordinates using the Haversine formula.
    """
    # Convert latitude and longitude to spherical coordinates in radians
    degrees_to_radians = math.pi / 180.0
    
    phi1 = lat1 * degrees_to_radians
    phi2 = lat2 * degrees_to_radians
    
    theta1 = lon1 * degrees_to_radians
    theta2 = lon2 * degrees_to_radians
    
    # Compute spherical distance
    d_phi = phi2 - phi1
    d_theta = theta2 - theta1
    
    a = (math.sin(d_phi / 2.0) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * 
         math.sin(d_theta / 2.0) ** 2)
         
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    # Earth radius in meters
    earth_radius = 6371000.0
    return c * earth_radius

STOPWORDS = {
    "the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "for", "to", "of",
    "it", "this", "there", "please", "very", "near", "opposite", "from", "with", "by",
    "sir", "madam", "bengaluru", "bangalore", "area"
}

def extract_civic_keywords(text: str) -> set:
    """Extracts non-stopword content tokens to assist wording-variation semantic matching."""
    words = [w.strip(",.!?\"'()[]{}").lower() for w in text.split()]
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}

def hamming_distance(h1: Optional[str], h2: Optional[str]) -> int:
    """Calculates bitwise Hamming distance between two hexadecimal perceptual hashes."""
    if not h1 or not h2:
        return 64
    try:
        val1 = int(str(h1), 16)
        val2 = int(str(h2), 16)
        return bin(val1 ^ val2).count("1")
    except Exception:
        return 64

def check_duplicate_complaint(
    db: Session,
    latitude: float,
    longitude: float,
    description: str,
    category_id: int,
    distance_threshold_m: float = 100.0,
    similarity_threshold: float = 0.85,
    image_path: Optional[str] = None,
    image_semantic_status: Optional[str] = None,
    perceptual_hash: Optional[str] = None,
    return_details: bool = False,
) -> Any:
    """
    Checks if a complaint is a duplicate of an existing active complaint:
      1. Evaluates description similarity, image similarity, and location proximity together.
      2. Links a new report to an existing parent ONLY when combined evidence supports the same incident.
      3. If image matches but description or location conflicts, flags for manual review instead of auto-merging or marking suspicious.
      4. If evidence is inconclusive, creates a separate complaint or requests review.
      5. A reused image alone does not classify a complaint as suspicious or automatically establish a duplicate.
    Returns:
      (is_duplicate, duplicate_of_complaint_id, similarity_score) if not return_details
      (is_duplicate, duplicate_of_complaint_id, similarity_score, review_flag, details_dict) if return_details
    """
    # Safeguard 0: Multimodal image-context gate.
    if image_semantic_status == "MISMATCH":
        logger.info("Duplicate check rejected: Uploaded image semantic mismatch for category_id %s.", category_id)
        if return_details:
            return False, None, 0.0, "IMAGE_MISMATCH", {"reason": "Uploaded image semantic mismatch"}
        return False, None, 0.0

    # Safeguard 1: Translate incoming text to standard English first
    translated_input = None
    if description and description.strip():
        try:
            translated_input, _, _ = translate_text(description)
        except Exception as e:
            logger.warning("Error translating incoming description for duplicate check (%s). Falling back to raw text.", e)

    if not translated_input or not translated_input.strip():
        logger.warning("translated_text is NULL or empty during duplicate check. Falling back to raw description text.")
        translated_input = description or ""

    # 1. Fetch complaints in the same category within an extended bounding box (~300m)
    delta = 0.003
    
    candidates = db.query(Complaint).filter(
        Complaint.category_id == category_id,
        Complaint.status.in_(["Registered", "Accepted", "In Progress", "Reopened"]),
        Complaint.location_latitude.between(latitude - delta, latitude + delta),
        Complaint.location_longitude.between(longitude - delta, longitude + delta),
        Complaint.duplicate_of_complaint_id.is_(None)  # Must be an original complaint
    ).all()
    
    if not candidates:
        if return_details:
            return False, None, 0.0, "NO_CANDIDATES", {}
        return False, None, 0.0
        
    # Get embedding for the new complaint using translated English text
    if encoder_model and translated_input.strip():
        new_embedding = encoder_model.encode(translated_input, convert_to_tensor=True)
    else:
        new_embedding = None
        
    best_match_id = None
    max_similarity = 0.0
    best_dist = 9999.0
    best_desc_score = 0.0
    best_img_score = 0.0
    conflict_found = False
    conflict_candidate_id = None
    conflict_reason = None
    
    for candidate in candidates:
        # Distance using Haversine
        dist = haversine_distance(latitude, longitude, candidate.location_latitude, candidate.location_longitude)
        
        # A. Location Proximity Score
        loc_score = max(0.0, 1.0 - (dist / distance_threshold_m)) if dist <= distance_threshold_m else 0.0
        loc_conflict = dist > 150.0  # Conflict if photo reused at a distant location (> 150m)

        # B. Description Similarity Score
        candidate_text = candidate.description or getattr(candidate, "translated_text", None)
        if not candidate_text or not candidate_text.strip():
            candidate_text = candidate.original_description or ""

        desc_score = 0.0
        if encoder_model and new_embedding is not None and candidate_text.strip():
            cand_embedding = encoder_model.encode(candidate_text, convert_to_tensor=True)
            cos_score = util.cos_sim(new_embedding, cand_embedding)[0][0].item()
            cos_score = max(0.0, min(1.0, cos_score))

            kw1 = extract_civic_keywords(translated_input)
            kw2 = extract_civic_keywords(candidate_text)
            token_sim = (len(kw1.intersection(kw2)) / max(1, len(kw1.union(kw2)))) if (kw1 or kw2) else 0.0
            desc_score = max(cos_score, (0.80 * cos_score) + (0.20 * token_sim))
        else:
            w1 = extract_civic_keywords(translated_input)
            w2 = extract_civic_keywords(candidate_text)
            if w1 or w2:
                desc_score = len(w1.intersection(w2)) / len(w1.union(w2))

        desc_conflict = desc_score < 0.45  # Conflict if descriptions describe totally different issues

        # C. Image Similarity Score
        cand_hashes = [img.perceptual_hash for img in candidate.images if img.perceptual_hash] if hasattr(candidate, "images") else []
        img_identical = False
        img_score = desc_score  # Neutral default

        if perceptual_hash and cand_hashes:
            min_hdist = min(hamming_distance(perceptual_hash, ch) for ch in cand_hashes)
            img_identical = (min_hdist <= 6)
            img_score = max(0.0, 1.0 - (min_hdist / 16.0))

        # D. Conflict Check (Requirement 3 & 5):
        # If image matches but description or location conflicts, flag for manual review
        # DO NOT automatically merge or mark it suspicious!
        if img_identical and (loc_conflict or desc_conflict):
            conflict_found = True
            conflict_candidate_id = candidate.id
            conflict_detail = f"location differs by {round(dist)}m" if loc_conflict else "description conflicts"
            conflict_reason = f"Image matches Complaint #{candidate.id} but {conflict_detail}. Flagged for manual review."
            logger.info("Duplicate conflict detected: %s", conflict_reason)
            continue

        # Skip candidates outside spatial threshold for duplicate merging
        if dist > distance_threshold_m:
            continue

        # E. Combined Evidence Score (Weighted: 50% Text, 35% Location, 15% Image)
        proximity_bonus = 0.05 if dist <= 40.0 else 0.0
        combined_score = (0.50 * desc_score) + (0.35 * loc_score) + (0.15 * img_score) + proximity_bonus
        combined_score = max(0.0, min(1.0, combined_score))

        if combined_score > max_similarity:
            max_similarity = combined_score
            best_match_id = candidate.id
            best_dist = dist
            best_desc_score = desc_score
            best_img_score = img_score

    # Conflict path: image matched an existing report but location/description differed
    if conflict_found and max_similarity < similarity_threshold:
        if return_details:
            return False, None, max_similarity, "MANUAL_REVIEW_CONFLICT", {
                "conflict_candidate_id": conflict_candidate_id,
                "reason": conflict_reason,
            }
        return False, None, max_similarity

    # Verified Duplicate: Combined evidence supports the same incident
    if max_similarity >= similarity_threshold and best_match_id is not None and best_desc_score >= 0.70:
        if return_details:
            return True, best_match_id, max_similarity, "COMBINED_MATCH", {
                "parent_id": best_match_id,
                "score": max_similarity,
                "dist_m": round(best_dist, 1),
                "desc_score": round(best_desc_score, 3),
                "img_score": round(best_img_score, 3),
            }
        return True, best_match_id, max_similarity

    # Inconclusive path (Borderline evidence: 0.60 <= score < threshold)
    if 0.60 <= max_similarity < similarity_threshold and best_match_id is not None:
        if return_details:
            return False, None, max_similarity, "INCONCLUSIVE_REVIEW", {
                "candidate_id": best_match_id,
                "score": max_similarity,
                "reason": f"Borderline similarity with nearby Complaint #{best_match_id}. Created separate complaint for manual audit.",
            }
        return False, None, max_similarity

    # No match
    if return_details:
        return False, None, max_similarity, "NO_MATCH", {}
    return False, None, max_similarity

def backfill_translated_descriptions(db: Session) -> int:
    """
    One-time backfill/migration step to ensure all stored complaint records
    have populated translated English text in `description`.
    """
    complaints = db.query(Complaint).all()
    updated_count = 0
    for c in complaints:
        if not c.description or c.description == c.original_description:
            text_to_translate = c.original_description or c.description
            if text_to_translate:
                trans, _, _ = translate_text(text_to_translate)
                if trans and trans.strip():
                    c.description = trans
                    updated_count += 1
    if updated_count > 0:
        db.commit()
        logger.info("Backfilled %d complaint records with translated English descriptions.", updated_count)
    return updated_count

