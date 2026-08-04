from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List

from backend.app.core.database import get_db
from backend.app.models.user import User, Officer, Role
from backend.app.models.department import Department
from backend.app.models.complaint import Complaint, ComplaintCategory, AIPrediction
from backend.app.routers.deps import get_current_active_user, get_current_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/citizen", response_model=Dict[str, Any])
def get_citizen_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.name != "Citizen":
        raise HTTPException(status_code=403, detail="Citizen role required")
        
    citizen_id = current_user.id
    
    total = db.query(func.count(Complaint.id)).filter(Complaint.citizen_id == citizen_id).scalar() or 0
    
    # Active states: Registered, Accepted, In Progress
    active = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == citizen_id,
        Complaint.status.in_(["Registered", "Accepted", "In Progress"])
    ).scalar() or 0
    
    resolved = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == citizen_id,
        Complaint.status == "Resolved"
    ).scalar() or 0
    
    closed = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == citizen_id,
        Complaint.status == "Closed"
    ).scalar() or 0
    
    # Pending means registered or accepted (not yet worked on)
    pending = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == citizen_id,
        Complaint.status.in_(["Registered", "Accepted"])
    ).scalar() or 0
    
    return {
        "total_complaints": total,
        "active_complaints": active,
        "resolved_complaints": resolved,
        "closed_complaints": closed,
        "pending_complaints": pending
    }

@router.get("/officer", response_model=Dict[str, Any])
def get_officer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.name != "Officer":
        raise HTTPException(status_code=403, detail="Officer role required")
        
    officer = db.query(Officer).filter(Officer.user_id == current_user.id).first()
    if not officer:
        raise HTTPException(status_code=400, detail="Officer profile not found")
        
    total = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == officer.id).scalar() or 0
    
    pending = db.query(func.count(Complaint.id)).filter(
        Complaint.assigned_officer_id == officer.id,
        Complaint.status == "Registered"
    ).scalar() or 0
    
    accepted = db.query(func.count(Complaint.id)).filter(
        Complaint.assigned_officer_id == officer.id,
        Complaint.status == "Accepted"
    ).scalar() or 0
    
    in_progress = db.query(func.count(Complaint.id)).filter(
        Complaint.assigned_officer_id == officer.id,
        Complaint.status == "In Progress"
    ).scalar() or 0
    
    resolved = db.query(func.count(Complaint.id)).filter(
        Complaint.assigned_officer_id == officer.id,
        Complaint.status == "Resolved"
    ).scalar() or 0
    
    closed = db.query(func.count(Complaint.id)).filter(
        Complaint.assigned_officer_id == officer.id,
        Complaint.status == "Closed"
    ).scalar() or 0
    
    return {
        "total_assigned": total,
        "pending": pending,
        "accepted": accepted,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed
    }

@router.get("/admin", response_model=Dict[str, Any])
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # Overall user stats
    total_users = db.query(func.count(User.id)).scalar() or 0
    citizens = db.query(func.count(User.id)).join(Role).filter(Role.name == "Citizen").scalar() or 0
    officers = db.query(func.count(User.id)).join(Role).filter(Role.name == "Officer").scalar() or 0
    
    # Overall complaint stats
    total_complaints = db.query(func.count(Complaint.id)).scalar() or 0
    registered = db.query(func.count(Complaint.id)).filter(Complaint.status == "Registered").scalar() or 0
    accepted = db.query(func.count(Complaint.id)).filter(Complaint.status == "Accepted").scalar() or 0
    in_progress = db.query(func.count(Complaint.id)).filter(Complaint.status == "In Progress").scalar() or 0
    resolved = db.query(func.count(Complaint.id)).filter(Complaint.status == "Resolved").scalar() or 0
    closed = db.query(func.count(Complaint.id)).filter(Complaint.status == "Closed").scalar() or 0
    
    # Category distribution
    cat_counts = db.query(
        ComplaintCategory.name, func.count(Complaint.id)
    ).outerjoin(Complaint).group_by(ComplaintCategory.name).all()
    category_distribution = {name: count for name, count in cat_counts}
    
    # Department distribution
    dept_counts = db.query(
        Department.code, func.count(Complaint.id)
    ).join(ComplaintCategory, ComplaintCategory.department_id == Department.id)\
     .outerjoin(Complaint, Complaint.category_id == ComplaintCategory.id)\
     .group_by(Department.code).all()
    department_distribution = {code: count for code, count in dept_counts}
    
    # Officer stats (Load, performance)
    officer_list = db.query(Officer).all()
    officer_statistics = []
    for off in officer_list:
        off_user = db.query(User).filter(User.id == off.user_id).first()
        if off_user:
            active_load = db.query(func.count(Complaint.id)).filter(
                Complaint.assigned_officer_id == off.id,
                Complaint.status.in_(["Registered", "Accepted", "In Progress"])
            ).scalar() or 0
            resolved_count = db.query(func.count(Complaint.id)).filter(
                Complaint.assigned_officer_id == off.id,
                Complaint.status.in_(["Resolved", "Closed"])
            ).scalar() or 0
            
            officer_statistics.append({
                "id": off.id,
                "name": off_user.name,
                "department": off.department.code,
                "active_load": active_load,
                "completed": resolved_count,
                "status": off.status
            })
            
    # Monitor AI predictions accuracy
    # (Compare user-submitted categories with final category or evaluate confidence scores)
    predictions = db.query(AIPrediction).all()
    total_preds = len(predictions)
    avg_cat_conf = 0.0
    avg_prio_conf = 0.0
    if total_preds > 0:
        avg_cat_conf = sum(p.category_confidence for p in predictions) / total_preds
        avg_prio_conf = sum(p.priority_confidence for p in predictions) / total_preds
        
    return {
        "users": {
            "total": total_users,
            "citizens": citizens,
            "officers": officers
        },
        "complaints": {
            "total": total_complaints,
            "registered": registered,
            "accepted": accepted,
            "in_progress": in_progress,
            "resolved": resolved,
            "closed": closed
        },
        "category_distribution": category_distribution,
        "department_distribution": department_distribution,
        "officer_statistics": officer_statistics,
        "ai_monitoring": {
            "total_predictions": total_preds,
            "average_category_confidence": round(avg_cat_conf, 4),
            "average_priority_confidence": round(avg_prio_conf, 4)
        }
    }
