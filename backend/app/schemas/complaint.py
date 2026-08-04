from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ComplaintImageResponse(BaseModel):
    id: int
    image_url: str
    image_type: str
    is_verified: bool
    confidence_score: float
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
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintCreate(BaseModel):
    description: str
    language: str = "English"  # English, Kannada, Hinglish
    location_latitude: float
    location_longitude: float
    location_address: Optional[str] = None
    
    # We will upload images separately or via multipart request,
    # but storing image link after upload is also possible.

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
    location_latitude: float
    location_longitude: float
    location_address: Optional[str] = None
    status: str
    priority: str
    assigned_officer_id: Optional[int] = None
    assigned_officer_name: Optional[str] = None
    duplicate_of_complaint_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    images: List[ComplaintImageResponse] = []
    status_history: List[ComplaintStatusHistoryResponse] = []
    ai_prediction: Optional[AIPredictionResponse] = None
    
    class Config:
        from_attributes = True

class DuplicateWarningResponse(BaseModel):
    is_duplicate: bool
    duplicate_of_id: Optional[int] = None
    similarity_score: float
    message: str

class ComplaintStatusUpdate(BaseModel):
    status: str  # Accepted, In Progress, Resolved, Closed
    remarks: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    complaint_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
