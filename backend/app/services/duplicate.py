import math
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from sentence_transformers import util
from backend.app.models.complaint import Complaint
from backend.app.services.ai import encoder_model

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
    similarity_threshold: float = 0.70
) -> Tuple[bool, Optional[int], float]:
    """
    Checks if a complaint is a duplicate of an existing active complaint.
    Returns (is_duplicate, duplicate_of_complaint_id, similarity_score).
    """
    # 1. Fetch complaints in the same category within a latitude/longitude bounding box (approx 100m)
    # 1 degree of lat/lon is approx 111km, so 100m is roughly 0.001 degrees
    delta = 0.001
    
    candidates = db.query(Complaint).filter(
        Complaint.category_id == category_id,
        Complaint.status.in_(["Registered", "Accepted", "In Progress"]),
        Complaint.location_latitude.between(latitude - delta, latitude + delta),
        Complaint.location_longitude.between(longitude - delta, longitude + delta),
        Complaint.duplicate_of_complaint_id.is_(None)  # Must be an original complaint
    ).all()
    
    if not candidates:
        return False, None, 0.0
        
    # Get embedding for the new complaint
    if encoder_model:
        new_embedding = encoder_model.encode(description, convert_to_tensor=True)
    else:
        new_embedding = None
        
    best_match_id = None
    max_similarity = 0.0
    
    for candidate in candidates:
        # Verify distance using Haversine
        dist = haversine_distance(latitude, longitude, candidate.location_latitude, candidate.location_longitude)
        
        if dist <= distance_threshold_m:
            # Distance check passed, check description similarity
            similarity = 0.0
            
            if encoder_model and new_embedding is not None:
                cand_embedding = encoder_model.encode(candidate.description, convert_to_tensor=True)
                score = util.cos_sim(new_embedding, cand_embedding)[0][0].item()
                similarity = max(0.0, min(1.0, score))
            else:
                # Text fallback - Jaccard index / word intersection
                w1 = set(description.lower().split())
                w2 = set(candidate.description.lower().split())
                if w1 or w2:
                    similarity = len(w1.intersection(w2)) / len(w1.union(w2))
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match_id = candidate.id
                
    if max_similarity >= similarity_threshold and best_match_id is not None:
        return True, best_match_id, max_similarity
        
    return False, None, max_similarity
