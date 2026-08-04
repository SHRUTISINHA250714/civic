from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.user import User, Officer
from backend.app.models.complaint import Complaint, ComplaintCategory, Notification, ComplaintStatusHistory

def assign_officer_to_complaint(db: Session, complaint: Complaint) -> Optional[Officer]:
    """
    Routs the complaint to the correct department and assigns it to the officer
    with the least amount of active complaints.
    """
    category = db.query(ComplaintCategory).filter(ComplaintCategory.id == complaint.category_id).first()
    if not category:
        return None
        
    # Get all active officers in the category's routed department who are "On Duty"
    officers = db.query(Officer).filter(
        Officer.department_id == category.department_id,
        Officer.status == "On Duty"
    ).all()
    
    if not officers:
        # Fallback to any officer in the department if none are explicitly "On Duty"
        officers = db.query(Officer).filter(
            Officer.department_id == category.department_id
        ).all()
        
    if not officers:
        return None
        
    # Calculate load (active complaints) for each officer
    # Active statuses: Registered, Accepted, In Progress
    officer_loads = {}
    for officer in officers:
        active_count = db.query(func.count(Complaint.id)).filter(
            Complaint.assigned_officer_id == officer.id,
            Complaint.status.in_(["Registered", "Accepted", "In Progress"])
        ).scalar()
        officer_loads[officer.id] = (active_count, officer)
        
    # Find officer with the minimum load
    best_officer_id = min(officer_loads, key=lambda k: officer_loads[k][0])
    best_officer = officer_loads[best_officer_id][1]
    
    # Assign officer to complaint
    complaint.assigned_officer_id = best_officer.id
    db.flush()
    
    # Create notification for officer
    officer_user = db.query(User).filter(User.id == best_officer.user_id).first()
    if officer_user:
        notif_msg = f"A new complaint (ID: {complaint.id}) regarding '{category.name}' has been assigned to you."
        db.add(Notification(
            user_id=officer_user.id,
            complaint_id=complaint.id,
            message=notif_msg
        ))
        
        # Append status history remark about assignment
        db.add(ComplaintStatusHistory(
            complaint_id=complaint.id,
            status=complaint.status,
            remarks=f"System routed to {category.department.code} and assigned to Officer {officer_user.name}.",
            changed_by_user_id=complaint.citizen_id
        ))
        
        # Create citizen notification
        citizen_msg = f"Your complaint has been successfully routed to {category.department.code}. Officer {officer_user.name} has been assigned to resolve it."
        db.add(Notification(
            user_id=complaint.citizen_id,
            complaint_id=complaint.id,
            message=citizen_msg
        ))
        
    return best_officer
