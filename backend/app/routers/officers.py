from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.core.database import get_db
from backend.app.models.user import User, Officer, Role
from backend.app.models.department import Department
from backend.app.models.complaint import ComplaintCategory
from backend.app.schemas.user import OfficerResponse, UserResponse
from backend.app.schemas.department import DepartmentResponse, ComplaintCategoryResponse, RoutingRuleUpdate
from backend.app.routers.deps import get_current_admin

router = APIRouter(prefix="/admin-control", tags=["Admin Control"])

@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    return db.query(Department).all()

@router.get("/categories", response_model=List[ComplaintCategoryResponse])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    categories = db.query(ComplaintCategory).all()
    res = []
    for cat in categories:
        res.append({
            "id": cat.id,
            "name": cat.name,
            "department_id": cat.department_id,
            "department_name": cat.department.name,
            "default_priority": cat.default_priority,
            "is_active": cat.is_active,
            "created_at": cat.created_at
        })
    return res

@router.put("/categories/{id}/routing", response_model=ComplaintCategoryResponse)
def update_routing_rule(
    id: int,
    rule_in: RoutingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    cat = db.query(ComplaintCategory).filter(ComplaintCategory.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Complaint category not found")
        
    dept = db.query(Department).filter(Department.id == rule_in.department_id).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found")
        
    cat.department_id = rule_in.department_id
    if rule_in.default_priority:
        cat.default_priority = rule_in.default_priority
        
    db.commit()
    db.refresh(cat)
    
    return {
        "id": cat.id,
        "name": cat.name,
        "department_id": cat.department_id,
        "department_name": cat.department.name,
        "default_priority": cat.default_priority,
        "is_active": cat.is_active,
        "created_at": cat.created_at
    }

@router.get("/officers", response_model=List[OfficerResponse])
def list_officers(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    officers = db.query(Officer).all()
    res = []
    for off in officers:
        off_user = db.query(User).filter(User.id == off.user_id).first()
        if off_user:
            res.append({
                "id": off.id,
                "user_id": off.user_id,
                "user": {
                    "name": off_user.name,
                    "email": off_user.email,
                    "phone": off_user.phone
                },
                "department_id": off.department_id,
                "department_name": off.department.name,
                "status": off.status
            })
    return res

@router.put("/officers/{id}/status")
def update_officer_status(
    id: int,
    status_update: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    off = db.query(Officer).filter(Officer.id == id).first()
    if not off:
        raise HTTPException(status_code=404, detail="Officer profile not found")
        
    new_status = status_update.get("status")
    if not new_status or new_status not in ["On Duty", "Active", "Inactive"]:
        raise HTTPException(status_code=400, detail="Invalid status value. Must be 'On Duty', 'Active', or 'Inactive'.")
        
    off.status = new_status
    db.commit()
    return {"message": f"Officer status updated to '{new_status}' successfully."}

@router.get("/citizens", response_model=List[UserResponse])
def list_citizens(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    return db.query(User).join(Role).filter(Role.name == "Citizen").all()

@router.put("/citizens/{id}/status")
def update_citizen_status(
    id: int,
    status_update: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    citizen = db.query(User).join(Role).filter(User.id == id, Role.name == "Citizen").first()
    if not citizen:
        raise HTTPException(status_code=404, detail="Citizen not found")
        
    new_status = status_update.get("status")
    if not new_status or new_status not in ["Active", "Suspended"]:
        raise HTTPException(status_code=400, detail="Invalid status value. Must be 'Active' or 'Suspended'.")
        
    citizen.status = new_status
    db.commit()
    return {"message": f"Citizen status updated to '{new_status}' successfully."}
