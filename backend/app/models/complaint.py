from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ComplaintCategory(Base):
    __tablename__ = "complaint_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    default_priority = Column(String, default="Medium")  # Low, Medium, High, Critical
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    department = relationship("Department", back_populates="categories")
    complaints = relationship("Complaint", back_populates="category")
    sla_policies = relationship("SLAPolicy", back_populates="category")

class SLAPolicy(Base):
    """SLA resolution time policies per category & priority."""
    __tablename__ = "sla_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("complaint_categories.id"), nullable=False)
    priority = Column(String, nullable=False)          # Low, Medium, High, Critical
    resolution_hours = Column(Float, nullable=False)   # e.g. 72, 48, 24, 12
    warning_threshold_pct = Column(Float, default=0.75)  # 75% of time elapsed → Warning
    created_at = Column(DateTime, default=datetime.utcnow)
    
    category = relationship("ComplaintCategory", back_populates="sla_policies")

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("complaint_categories.id"), nullable=False)
    description = Column(String, nullable=False)
    original_description = Column(String, nullable=True)
    language = Column(String, default="English")  # English, Kannada, Hinglish, Voice
    detected_language = Column(String, nullable=True)
    
    # Audio complaint support
    audio_url = Column(String, nullable=True)         # URL of voice recording if submitted
    
    # Location
    location_latitude = Column(Float, nullable=False)
    location_longitude = Column(Float, nullable=False)
    location_address = Column(String, nullable=True)
    
    # Status & Priority
    status = Column(String, default="Registered")  # Registered, Accepted, In Progress, Resolved, Reopened, Closed
    priority = Column(String, default="Medium")    # Low, Medium, High, Critical
    
    # Assignment
    assigned_officer_id = Column(Integer, ForeignKey("officers.id"), nullable=True)
    duplicate_of_complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    impact_count = Column(Integer, default=1)
    
    # SLA Tracking
    sla_deadline = Column(DateTime, nullable=True)
    sla_status = Column(String, default="Normal")  # Normal, Warning, Breached
    is_escalated = Column(Boolean, default=False)
    
    # Citizen Feedback / Verification of Resolution
    citizen_verified = Column(Boolean, nullable=True)            # None=pending, True=approved, False=rejected
    citizen_feedback_rating = Column(Integer, nullable=True)     # 1-5 stars
    citizen_feedback_remarks = Column(String, nullable=True)
    reopen_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    citizen = relationship("User", back_populates="complaints", foreign_keys=[citizen_id])
    category = relationship("ComplaintCategory", back_populates="complaints")
    assigned_officer = relationship("Officer", back_populates="assigned_complaints")
    
    images = relationship("ComplaintImage", back_populates="complaint")
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint")
    ai_prediction = relationship("AIPrediction", back_populates="complaint", uselist=False)
    notifications = relationship("Notification", back_populates="complaint")
    evidence_check = relationship("ComplaintEvidenceCheck", back_populates="complaint", uselist=False)
    
    # Self-referencing relationship for duplicate handling
    duplicates = relationship("Complaint", backref="original_complaint", remote_side=[id])

class ComplaintImage(Base):
    __tablename__ = "complaint_images"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    image_url = Column(String, nullable=False)
    image_type = Column(String, default="Reporting")  # Reporting, Resolution
    is_verified = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)
    perceptual_hash = Column(String, nullable=True)
    bounding_boxes = Column(Text, nullable=True)
    quality_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="images")

class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    status = Column(String, nullable=False)
    remarks = Column(String, nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="status_history")
    changed_by_user = relationship("User", back_populates="history_records")

class AIPrediction(Base):
    __tablename__ = "ai_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), unique=True, nullable=False)
    predicted_category_id = Column(Integer, ForeignKey("complaint_categories.id"), nullable=False)
    category_confidence = Column(Float, default=0.0)
    predicted_priority = Column(String, nullable=False)
    priority_confidence = Column(Float, default=0.0)
    translation_time = Column(Float, default=0.0)  # in seconds
    transcription_used = Column(Boolean, default=False)  # True if voice input was used
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="ai_prediction")
    predicted_category = relationship("ComplaintCategory")

class ComplaintEvidenceCheck(Base):
    """Multimodal Evidence Trust Score & Hard Gate Verification for each complaint."""
    __tablename__ = "complaint_evidence_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), unique=True, nullable=False)
    
    # ── Hard Gate Verification Decision ───────────────────────────────────────
    verification_decision = Column(String, default="VERIFIED")  # VERIFIED, PARTIALLY_VERIFIED, MANUAL_REVIEW, SUSPICIOUS, REJECTED
    
    # ── Gate 1: GPS / EXIF Validation ─────────────────────────────────────────
    live_gps_provided = Column(Boolean, default=False)
    exif_gps_found = Column(Boolean, default=False)
    gps_distance_m = Column(Float, nullable=True)    # Distance between live GPS and EXIF GPS
    gps_match = Column(Boolean, default=True)        # True if within threshold (< 500m)
    gps_accuracy = Column(Float, nullable=True)      # Accuracy in meters from device
    geo_status = Column(String, default="MATCH")     # MATCH, MISMATCH, EXIF_MISSING, SUSPICIOUS
    
    # ── Gate 2: Timestamp Consistency ─────────────────────────────────────────
    timestamp_valid = Column(Boolean, default=True)
    freshness_status = Column(String, default="FRESH")  # FRESH, STALE, FUTURE, UNKNOWN
    
    # ── Gate 3: Image vs Text Semantic Agreement ──────────────────────────────
    vision_objects_detected = Column(String, nullable=True)  # JSON list of YOLO labels
    vision_agreement_score = Column(Float, default=0.5)      # 0.0 - 1.0
    semantic_match_status = Column(String, default="MATCH")  # MATCH, PARTIAL_MATCH, MISMATCH, UNKNOWN
    semantic_confidence = Column(Float, default=0.0)
    image_category = Column(String, nullable=True)
    
    # ── Gate 4: Reused Image Detection ────────────────────────────────────────
    is_reused_image = Column(Boolean, default=False)
    reused_complaint_id = Column(Integer, nullable=True)
    perceptual_hash = Column(String, nullable=True)
    
    # ── Quality & Audit ───────────────────────────────────────────────────────
    quality_check = Column(String, nullable=True)
    gate_reasons = Column(Text, nullable=True)       # JSON list of gate reasons
    
    # ── Composite Score (Legacy & Trust Display) ──────────────────────────────
    trust_score = Column(Float, default=50.0)        # 0-100
    trust_level = Column(String, default="Medium")   # High, Medium, Low, Suspicious
    verification_details = Column(Text, nullable=True)  # Human-readable explanation
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="evidence_check")

class DuplicateComplaintMapping(Base):
    __tablename__ = "duplicate_complaint_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    original_complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    duplicate_complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    similarity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    message = Column(String, nullable=False)
    notification_type = Column(String, default="General")  # General, SLA_Warning, SLA_Breach, Resolution, Reopen
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")
    complaint = relationship("Complaint", back_populates="notifications")
