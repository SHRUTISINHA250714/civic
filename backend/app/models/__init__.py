from backend.app.core.database import Base
from backend.app.models.user import Role, User, Officer
from backend.app.models.department import Department
from backend.app.models.complaint import (
    ComplaintCategory, Complaint, ComplaintImage,
    ComplaintStatusHistory, AIPrediction, DuplicateComplaintMapping,
    Notification
)

# Export all models and Base for database creation
__all__ = [
    "Base",
    "Role",
    "User",
    "Officer",
    "Department",
    "ComplaintCategory",
    "Complaint",
    "ComplaintImage",
    "ComplaintStatusHistory",
    "AIPrediction",
    "DuplicateComplaintMapping",
    "Notification"
]
