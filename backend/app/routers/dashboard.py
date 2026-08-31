from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.models.user import User, Officer, Role
from backend.app.models.department import Department
from backend.app.models.complaint import (
    Complaint, ComplaintCategory, AIPrediction, ComplaintEvidenceCheck, SLAPolicy
)
from backend.app.routers.deps import get_current_active_user, get_current_admin
from backend.app.services.sla import get_sla_status, update_all_sla_statuses
from backend.app.services.predictive import predictive_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/citizen", response_model=Dict[str, Any])
def get_citizen_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.name != "Citizen":
        raise HTTPException(status_code=403, detail="Citizen role required")
        
    cid = current_user.id
    total = db.query(func.count(Complaint.id)).filter(Complaint.citizen_id == cid).scalar() or 0
    active = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == cid,
        Complaint.status.in_(["Registered", "Accepted", "In Progress", "Reopened"])
    ).scalar() or 0
    resolved = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == cid, Complaint.status == "Resolved"
    ).scalar() or 0
    closed = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == cid, Complaint.status == "Closed"
    ).scalar() or 0
    pending = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == cid,
        Complaint.status.in_(["Registered", "Accepted"])
    ).scalar() or 0
    reopened = db.query(func.count(Complaint.id)).filter(
        Complaint.citizen_id == cid, Complaint.status == "Reopened"
    ).scalar() or 0

    return {
        "total_complaints":    total,
        "active_complaints":   active,
        "resolved_complaints": resolved,
        "closed_complaints":   closed,
        "pending_complaints":  pending,
        "reopened_complaints": reopened,
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
        
    oid = officer.id
    total       = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == oid).scalar() or 0
    pending     = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == oid, Complaint.status == "Registered").scalar() or 0
    accepted    = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == oid, Complaint.status == "Accepted").scalar() or 0
    in_progress = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == oid, Complaint.status == "In Progress").scalar() or 0
    resolved    = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == oid, Complaint.status == "Resolved").scalar() or 0
    closed      = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == oid, Complaint.status == "Closed").scalar() or 0
    reopened    = db.query(func.count(Complaint.id)).filter(Complaint.assigned_officer_id == oid, Complaint.status == "Reopened").scalar() or 0
    
    # SLA metrics for officer
    sla_warning  = db.query(func.count(Complaint.id)).filter(
        Complaint.assigned_officer_id == oid, Complaint.sla_status == "Warning"
    ).scalar() or 0
    sla_breached = db.query(func.count(Complaint.id)).filter(
        Complaint.assigned_officer_id == oid, Complaint.sla_status == "Breached"
    ).scalar() or 0

    return {
        "total_assigned": total,
        "pending":        pending,
        "accepted":       accepted,
        "in_progress":    in_progress,
        "resolved":       resolved,
        "closed":         closed,
        "reopened":       reopened,
        "sla_warning":    sla_warning,
        "sla_breached":   sla_breached,
    }


@router.get("/admin", response_model=Dict[str, Any])
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # ── 1. User stats ──────────────────────────────────────────────────────────
    total_users  = db.query(func.count(User.id)).scalar() or 0
    citizens     = db.query(func.count(User.id)).join(Role).filter(Role.name == "Citizen").scalar() or 0
    officers     = db.query(func.count(User.id)).join(Role).filter(Role.name == "Officer").scalar() or 0

    # ── 2. Complaint stats ────────────────────────────────────────────────────
    total_complaints = db.query(func.count(Complaint.id)).scalar() or 0
    registered       = db.query(func.count(Complaint.id)).filter(Complaint.status == "Registered").scalar() or 0
    accepted         = db.query(func.count(Complaint.id)).filter(Complaint.status == "Accepted").scalar() or 0
    in_progress      = db.query(func.count(Complaint.id)).filter(Complaint.status == "In Progress").scalar() or 0
    resolved         = db.query(func.count(Complaint.id)).filter(Complaint.status == "Resolved").scalar() or 0
    closed           = db.query(func.count(Complaint.id)).filter(Complaint.status == "Closed").scalar() or 0
    reopened         = db.query(func.count(Complaint.id)).filter(Complaint.status == "Reopened").scalar() or 0

    # ── 3. Category & Department distribution ────────────────────────────────
    cat_counts = db.query(ComplaintCategory.name, func.count(Complaint.id))\
        .outerjoin(Complaint).group_by(ComplaintCategory.name).all()
    category_distribution = {name: count for name, count in cat_counts}

    dept_counts = db.query(Department.code, func.count(Complaint.id))\
        .join(ComplaintCategory, ComplaintCategory.department_id == Department.id)\
        .outerjoin(Complaint, Complaint.category_id == ComplaintCategory.id)\
        .group_by(Department.code).all()
    department_distribution = {code: count for code, count in dept_counts}

    # ── 4. SLA Monitoring ─────────────────────────────────────────────────────
    sla_normal   = db.query(func.count(Complaint.id)).filter(
        Complaint.sla_status == "Normal",
        Complaint.status.notin_(["Closed", "Resolved"])
    ).scalar() or 0
    sla_warning  = db.query(func.count(Complaint.id)).filter(Complaint.sla_status == "Warning").scalar() or 0
    sla_breached = db.query(func.count(Complaint.id)).filter(Complaint.sla_status == "Breached").scalar() or 0
    escalated    = db.query(func.count(Complaint.id)).filter(Complaint.is_escalated == True).scalar() or 0
    
    total_active = registered + accepted + in_progress + reopened
    sla_compliance_pct = 0.0
    if total_active > 0:
        compliant = total_active - sla_breached
        sla_compliance_pct = round(compliant / total_active * 100, 1)

    # ── 5. Officer performance ────────────────────────────────────────────────
    officer_list = db.query(Officer).all()
    officer_statistics = []
    for off in officer_list:
        off_user = db.query(User).filter(User.id == off.user_id).first()
        if off_user:
            active_load    = db.query(func.count(Complaint.id)).filter(
                Complaint.assigned_officer_id == off.id,
                Complaint.status.in_(["Registered", "Accepted", "In Progress", "Reopened"])
            ).scalar() or 0
            resolved_count = db.query(func.count(Complaint.id)).filter(
                Complaint.assigned_officer_id == off.id,
                Complaint.status.in_(["Resolved", "Closed"])
            ).scalar() or 0
            breached_count = db.query(func.count(Complaint.id)).filter(
                Complaint.assigned_officer_id == off.id,
                Complaint.sla_status == "Breached"
            ).scalar() or 0
            
            officer_statistics.append({
                "id":            off.id,
                "name":          off_user.name,
                "department":    off.department.code,
                "active_load":   active_load,
                "completed":     resolved_count,
                "sla_breached":  breached_count,
                "status":        off.status,
            })

    # ── 6. AI monitoring ──────────────────────────────────────────────────────
    predictions = db.query(AIPrediction).all()
    total_preds = len(predictions)
    avg_cat_conf  = 0.0
    avg_prio_conf = 0.0
    voice_intakes = 0
    if total_preds > 0:
        avg_cat_conf  = sum(p.category_confidence for p in predictions) / total_preds
        avg_prio_conf = sum(p.priority_confidence for p in predictions) / total_preds
        voice_intakes = sum(1 for p in predictions if p.transcription_used)

    # ── 7. Evidence Trust Analytics ───────────────────────────────────────────
    ev_checks = db.query(ComplaintEvidenceCheck).all()
    total_ev = len(ev_checks)
    ev_high       = sum(1 for e in ev_checks if e.trust_level == "High")
    ev_medium     = sum(1 for e in ev_checks if e.trust_level == "Medium")
    ev_low        = sum(1 for e in ev_checks if e.trust_level == "Low")
    ev_suspicious = sum(1 for e in ev_checks if e.trust_level == "Suspicious")
    avg_trust_score = round(sum(e.trust_score for e in ev_checks) / total_ev, 2) if total_ev > 0 else 0.0

    # ── 8. GIS Hotspot Data (top 20 complaint locations for heatmap) ──────────
    all_complaints = db.query(Complaint).filter(
        Complaint.status.notin_(["Closed"])
    ).all()
    hotspot_points = [
        {
            "lat":      c.location_latitude,
            "lon":      c.location_longitude,
            "id":       c.id,
            "status":   c.status,
            "priority": c.priority,
            "category": c.category.name,
        }
        for c in all_complaints
    ]

    # ── 9. Predictive Risk Insights (reopen rates, SLA breaches by dept) ──────
    reopen_counts = db.query(
        Department.code, func.sum(Complaint.reopen_count)
    ).join(ComplaintCategory, ComplaintCategory.department_id == Department.id)\
     .join(Complaint, Complaint.category_id == ComplaintCategory.id)\
     .group_by(Department.code).all()
    reopen_by_dept = {code: (int(cnt) if cnt else 0) for code, cnt in reopen_counts}

    breach_by_dept = db.query(
        Department.code, func.count(Complaint.id)
    ).join(ComplaintCategory, ComplaintCategory.department_id == Department.id)\
     .join(Complaint, Complaint.category_id == ComplaintCategory.id)\
     .filter(Complaint.sla_status == "Breached")\
     .group_by(Department.code).all()
    breach_by_dept_map = {code: count for code, count in breach_by_dept}

    return {
        "users": {"total": total_users, "citizens": citizens, "officers": officers},
        "complaints": {
            "total":       total_complaints,
            "registered":  registered,
            "accepted":    accepted,
            "in_progress": in_progress,
            "resolved":    resolved,
            "closed":      closed,
            "reopened":    reopened,
        },
        "category_distribution":   category_distribution,
        "department_distribution": department_distribution,
        "officer_statistics":      officer_statistics,
        "sla_monitoring": {
            "sla_normal":          sla_normal,
            "sla_warning":         sla_warning,
            "sla_breached":        sla_breached,
            "escalated":           escalated,
            "compliance_percent":  sla_compliance_pct,
            "breach_by_department": breach_by_dept_map,
        },
        "ai_monitoring": {
            "total_predictions":             total_preds,
            "average_category_confidence":   round(avg_cat_conf, 4),
            "average_priority_confidence":   round(avg_prio_conf, 4),
            "voice_intake_count":            voice_intakes,
        },
        "evidence_trust": {
            "total_checks":      total_ev,
            "high":              ev_high,
            "medium":            ev_medium,
            "low":               ev_low,
            "suspicious":        ev_suspicious,
            "avg_trust_score":   avg_trust_score,
        },
        "gis_hotspots":     hotspot_points,
        "predictive_risk": {
            "reopen_rate_by_department":  reopen_by_dept,
            "sla_breach_by_department":   breach_by_dept_map,
        },
        "predictive_intelligence": predictive_service.get_predictive_overview(),
    }


@router.post("/admin/run-sla-check")
def run_sla_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Manually trigger SLA status update and send escalation notifications."""
    updated = update_all_sla_statuses(db)
    return {"message": f"SLA check complete. {updated} complaint(s) updated."}
