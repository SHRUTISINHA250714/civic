from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ComplaintImageResponse(BaseModel):
    id: int
    image_url: str
    image_type: str
    is_verified: bool
    confidence_score: float
    bounding_boxes: Optional[str] = None
    quality_status: Optional[str] = None
    perceptual_hash: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintStatusHistoryResponse(BaseModel):
    id: int
    status: str
    remarks: Optional[str] = None
    changed_by_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIPredictionResponse(BaseModel):
    id: int
    predicted_category_name: str
    category_confidence: float
    predicted_priority: str
    priority_confidence: float
    translation_time: float
    transcription_used: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class EvidenceCheckResponse(BaseModel):
    """Multimodal Evidence Trust Score & Hard Gate Verification summary."""
    verification_decision: str = "VERIFIED"     # VERIFIED, PARTIALLY_VERIFIED, MANUAL_REVIEW, SUSPICIOUS, REJECTED
    trust_score: float
    trust_level: str                            # High, Medium, Low, Suspicious
    live_gps_provided: bool
    exif_gps_found: bool
    gps_distance_m: Optional[float] = None
    gps_match: bool
    gps_accuracy: Optional[float] = None
    geo_status: str = "MATCH"                   # MATCH, MISMATCH, EXIF_MISSING, SUSPICIOUS
    timestamp_valid: bool
    freshness_status: str = "FRESH"             # FRESH, STALE, FUTURE, UNKNOWN
    vision_objects_detected: str                # JSON list string
    vision_agreement_score: float
    semantic_match_status: str = "MATCH"        # MATCH, PARTIAL_MATCH, MISMATCH, UNKNOWN
    semantic_confidence: float = 0.0
    image_category: Optional[str] = None
    is_reused_image: bool = False
    reused_complaint_id: Optional[int] = None
    quality_check: Optional[str] = None
    gate_reasons: Optional[str] = None
    verification_details: Optional[str] = None
    
    class Config:
        from_attributes = True

class SLASummaryResponse(BaseModel):
    """SLA tracking summary."""
    sla_deadline: Optional[str] = None
    sla_status: str                 # Normal, Warning, Breached
    is_escalated: bool
    pct_elapsed: float              # 0-100
    hours_remaining: Optional[float] = None

class CitizenVerifyResolutionRequest(BaseModel):
    """Citizen approves or rejects resolution."""
    approve: bool               # True = approve & close | False = reject & reopen
    feedback_rating: Optional[int] = None   # 1–5 stars
    feedback_remarks: Optional[str] = None

class ComplaintCreate(BaseModel):
    description: str
    language: str = "English"  # English, Kannada, Hinglish, Voice
    location_latitude: float
    location_longitude: float
    location_address: Optional[str] = None

class ComplaintResponse(BaseModel):
    id: int
    citizen_id: int
    citizen_name: str
    category_id: int
    category_name: str
    department_id: int
    department_name: str
    description: str
    original_description: Optional[str] = None
    language: str
    detected_language: Optional[str] = None
    audio_url: Optional[str] = None
    location_latitude: float
    location_longitude: float
    location_address: Optional[str] = None
    status: str
    priority: str
    assigned_officer_id: Optional[int] = None
    assigned_officer_name: Optional[str] = None
    duplicate_of_complaint_id: Optional[int] = None
    
    # SLA
    sla_deadline: Optional[str] = None
    sla_status: Optional[str] = "Normal"
    is_escalated: bool = False
    
    # Citizen verification
    citizen_verified: Optional[bool] = None
    citizen_feedback_rating: Optional[int] = None
    citizen_feedback_remarks: Optional[str] = None
    reopen_count: int = 0
    
    created_at: datetime
    updated_at: datetime
    
    images: List[ComplaintImageResponse] = []
    status_history: List[ComplaintStatusHistoryResponse] = []
    ai_prediction: Optional[AIPredictionResponse] = None
    evidence_check: Optional[EvidenceCheckResponse] = None
    sla_summary: Optional[SLASummaryResponse] = None
    
    class Config:
        from_attributes = True

class DuplicateWarningResponse(BaseModel):
    is_duplicate: bool
    duplicate_of_id: Optional[int] = None
    similarity_score: float
    message: str

class ComplaintStatusUpdate(BaseModel):
    status: str  # Accepted, In Progress, Resolved, Closed, Reopened
    remarks: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    complaint_id: Optional[int] = None
    notification_type: str = "General"
    created_at: datetime
    
    class Config:
        from_attributes = True
