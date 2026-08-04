from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
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

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("complaint_categories.id"), nullable=False)
    description = Column(String, nullable=False)
    original_description = Column(String, nullable=True)
    language = Column(String, default="English")  # English, Kannada, Hinglish
    detected_language = Column(String, nullable=True)
    location_latitude = Column(Float, nullable=False)
    location_longitude = Column(Float, nullable=False)
    location_address = Column(String, nullable=True)
    status = Column(String, default="Registered")  # Registered, Accepted, In Progress, Resolved, Closed
    priority = Column(String, default="Medium")  # Low, Medium, High, Critical
    assigned_officer_id = Column(Integer, ForeignKey("officers.id"), nullable=True)
    duplicate_of_complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    citizen = relationship("User", back_populates="complaints", foreign_keys=[citizen_id])
    category = relationship("ComplaintCategory", back_populates="complaints")
    assigned_officer = relationship("Officer", back_populates="assigned_complaints")
    
    images = relationship("ComplaintImage", back_populates="complaint")
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint")
    ai_prediction = relationship("AIPrediction", back_populates="complaint", uselist=False)
    notifications = relationship("Notification", back_populates="complaint")
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="ai_prediction")
    predicted_category = relationship("ComplaintCategory")

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
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")
    complaint = relationship("Complaint", back_populates="notifications")
