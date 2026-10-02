import math
import logging
from typing import Tuple, Optional
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

def check_duplicate_complaint(
    db: Session,
    latitude: float,
    longitude: float,
    description: str,
    category_id: int,
    distance_threshold_m: float = 100.0,
    similarity_threshold: float = 0.85
) -> Tuple[bool, Optional[int], float]:
    """
    Checks if a complaint is a duplicate of an existing active complaint using translated English text embeddings.
    Returns (is_duplicate, duplicate_of_complaint_id, similarity_score).
    """
    # Safeguard 1: Translate incoming text to standard English first
    translated_input = None
    if description:
        try:
            translated_input, _, _ = translate_text(description)
        except Exception as e:
            logger.warning("Error translating incoming description for duplicate check (%s). Falling back to raw text.", e)

    if not translated_input or not translated_input.strip():
        logger.warning("translated_text is NULL or empty during duplicate check. Falling back to raw description text.")
        translated_input = description or ""

    # 1. Fetch complaints in the same category within a latitude/longitude bounding box (approx 100m)
    delta = 0.001
    
    candidates = db.query(Complaint).filter(
        Complaint.category_id == category_id,
        Complaint.status.in_(["Registered", "Accepted", "In Progress", "Reopened"]),
        Complaint.location_latitude.between(latitude - delta, latitude + delta),
        Complaint.location_longitude.between(longitude - delta, longitude + delta),
        Complaint.duplicate_of_complaint_id.is_(None)  # Must be an original complaint
    ).all()
    
    if not candidates:
        return False, None, 0.0
        
    # Get embedding for the new complaint using translated English text
    if encoder_model and translated_input.strip():
        new_embedding = encoder_model.encode(translated_input, convert_to_tensor=True)
    else:
        new_embedding = None
        
    best_match_id = None
    max_similarity = 0.0
    
    for candidate in candidates:
        # Verify distance using Haversine
        dist = haversine_distance(latitude, longitude, candidate.location_latitude, candidate.location_longitude)
        
        if dist <= distance_threshold_m:
            # Safeguard 2: Ensure candidate complaint text is the translated English description
            candidate_text = candidate.description or getattr(candidate, "translated_text", None)
            if not candidate_text or not candidate_text.strip():
                logger.warning(
                    "Candidate complaint #%s translated_text is NULL or empty. Falling back to original_description.",
                    candidate.id
                )
                candidate_text = candidate.original_description or ""

            similarity = 0.0
            
            if encoder_model and new_embedding is not None and candidate_text.strip():
                cand_embedding = encoder_model.encode(candidate_text, convert_to_tensor=True)
                score = util.cos_sim(new_embedding, cand_embedding)[0][0].item()
                similarity = max(0.0, min(1.0, score))
            else:
                # Text fallback - Jaccard index / word intersection
                w1 = set(translated_input.lower().split())
                w2 = set(candidate_text.lower().split())
                if w1 or w2:
                    similarity = len(w1.intersection(w2)) / len(w1.union(w2))
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match_id = candidate.id
                
    if max_similarity >= similarity_threshold and best_match_id is not None:
        return True, best_match_id, max_similarity
        
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

