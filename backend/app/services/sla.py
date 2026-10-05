"""
SLA Management & Auto-Escalation Engine (Blueprint Phase 14)
============================================================
Provides:
  - SLA deadline computation from complaint priority & category policy
  - SLA status evaluation (Normal / Warning / Breached)
  - Batch update of SLA status across active complaints
  - Escalation notification helpers
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.models.complaint import Complaint, SLAPolicy, Notification

# Fallback default resolution hours if no SLAPolicy record exists
DEFAULT_SLA_HOURS = {
    "Critical": 12.0,
    "High":     24.0,
    "Medium":   48.0,
    "Low":      72.0,
}


def compute_sla_deadline(
    db: Session,
    category_id: int,
    priority: str,
    filed_at: Optional[datetime] = None,
) -> datetime:
    """
    Returns the SLA deadline datetime for a complaint.
    Looks up the SLAPolicy table first; falls back to defaults.
    """
    if filed_at is None:
        filed_at = datetime.utcnow()

    policy = db.query(SLAPolicy).filter(
        SLAPolicy.category_id == category_id,
        SLAPolicy.priority == priority,
    ).first()

    hours = policy.resolution_hours if policy else DEFAULT_SLA_HOURS.get(priority, 48.0)
    return filed_at + timedelta(hours=hours)


def get_sla_status(
    complaint: Complaint,
    db: Optional[Session] = None,
) -> Tuple[str, float]:
    """
    Evaluates the current SLA status of a complaint.
    Returns (sla_status, pct_elapsed) where pct_elapsed is 0.0-1.0+.
      - "Normal"  : < warning threshold elapsed
      - "Warning" : >= warning threshold but not yet breached
      - "Breached": deadline passed
    """
    if not complaint.sla_deadline:
        return "Normal", 0.0

    now = datetime.utcnow()
    deadline = complaint.sla_deadline
    filed_at = complaint.created_at

    total_seconds = (deadline - filed_at).total_seconds()
    if total_seconds <= 0:
        return "Breached", 1.0

    elapsed_seconds = (now - filed_at).total_seconds()
    pct_elapsed = elapsed_seconds / total_seconds

    # Fetch warning threshold from policy if DB provided
    warning_threshold = 0.75
    if db:
        policy = db.query(SLAPolicy).filter(
            SLAPolicy.category_id == complaint.category_id,
            SLAPolicy.priority == complaint.priority,
        ).first()
        if policy:
            warning_threshold = policy.warning_threshold_pct

    if now > deadline:
        return "Breached", pct_elapsed
    elif pct_elapsed >= warning_threshold:
        return "Warning", pct_elapsed
    else:
        return "Normal", pct_elapsed


def update_all_sla_statuses(db: Session) -> int:
    """
    Scans all active (non-Closed, non-Resolved) complaints and updates their
    sla_status field. Sends escalation notifications for newly breached or
    warning-state complaints.
    Returns count of updated records.
    """
    active_statuses = ["Registered", "Accepted", "In Progress", "Reopened"]
    complaints = db.query(Complaint).filter(
        Complaint.status.in_(active_statuses),
        Complaint.sla_deadline.isnot(None),
    ).all()

    updated = 0
    for c in complaints:
        new_status, pct = get_sla_status(c, db)
        old_status = c.sla_status or "Normal"

        if new_status != old_status:
            c.sla_status = new_status
            updated += 1

            # ── Newly breached → escalate & notify ────────────────────────────
            if new_status == "Breached" and not c.is_escalated:
                c.is_escalated = True

                # Notify officer
                if c.assigned_officer_id:
                    from backend.app.models.user import User, Officer
                    officer = db.query(Officer).filter(
                        Officer.id == c.assigned_officer_id
                    ).first()
                    if officer:
                        officer_user = db.query(User).filter(
                            User.id == officer.user_id
                        ).first()
                        if officer_user:
                            db.add(Notification(
                                user_id=officer_user.id,
                                complaint_id=c.id,
                                message=(
                                    f"🚨 SLA BREACH: Complaint #{c.id} "
                                    f"({c.category.name}) has exceeded its "
                                    f"SLA deadline. Immediate action required!"
                                ),
                                notification_type="SLA_Breach",
                            ))

                # Notify citizen
                db.add(Notification(
                    user_id=c.citizen_id,
                    complaint_id=c.id,
                    message=(
                        f"⚠️ Your complaint #{c.id} has exceeded its SLA "
                        f"resolution deadline and has been escalated to "
                        f"management for priority action."
                    ),
                    notification_type="SLA_Breach",
                ))

            # ── New warning state → alert officer ─────────────────────────────
            elif new_status == "Warning" and old_status == "Normal":
                if c.assigned_officer_id:
                    from backend.app.models.user import User, Officer
                    officer = db.query(Officer).filter(
                        Officer.id == c.assigned_officer_id
                    ).first()
                    if officer:
                        officer_user = db.query(User).filter(
                            User.id == officer.user_id
                        ).first()
                        if officer_user:
                            db.add(Notification(
                                user_id=officer_user.id,
                                complaint_id=c.id,
                                message=(
                                    f"⏰ SLA Warning: Complaint #{c.id} "
                                    f"({c.category.name}) is approaching its "
                                    f"SLA deadline. Please resolve soon."
                                ),
                                notification_type="SLA_Warning",
                            ))

        # ── Progressive Escalation for complaints that remain breached ────────
        if new_status == "Breached":
            esc_level, esc_stage, hours_overdue = get_escalation_details(c)
            if esc_level and esc_level >= 2:
                existing_esc_notif = db.query(Notification).filter(
                    Notification.complaint_id == c.id,
                    Notification.notification_type == f"SLA_Escalation_L{esc_level}"
                ).first()
                if not existing_esc_notif:
                    if c.assigned_officer_id:
                        from backend.app.models.user import User, Officer
                        officer = db.query(Officer).filter(Officer.id == c.assigned_officer_id).first()
                        if officer:
                            officer_user = db.query(User).filter(User.id == officer.user_id).first()
                            if officer_user:
                                db.add(Notification(
                                    user_id=officer_user.id,
                                    complaint_id=c.id,
                                    message=f"🚨 PROGRESSIVE ESCALATION: Complaint #{c.id} ({c.category.name}) is {hours_overdue}h overdue. {esc_stage}.",
                                    notification_type=f"SLA_Escalation_L{esc_level}"
                                ))
                    db.add(Notification(
                        user_id=c.citizen_id,
                        complaint_id=c.id,
                        message=f"📢 Progressive Escalation Notice: Your grievance #{c.id} ({hours_overdue}h overdue) has progressed to {esc_stage}.",
                        notification_type=f"SLA_Escalation_L{esc_level}"
                    ))
                    updated += 1

        # ── Predictive SLA Early Warning Check (< 75% elapsed) ────────────────
        elif new_status == "Normal" and pct < 0.75:
            is_warn, prob, warn_msg = get_predictive_early_warning(c)
            if is_warn:
                existing_warn = db.query(Notification).filter(
                    Notification.complaint_id == c.id,
                    Notification.notification_type == "SLA_Predictive_Warning"
                ).first()
                if not existing_warn and c.assigned_officer_id:
                    from backend.app.models.user import User, Officer
                    officer = db.query(Officer).filter(Officer.id == c.assigned_officer_id).first()
                    if officer:
                        officer_user = db.query(User).filter(User.id == officer.user_id).first()
                        if officer_user:
                            db.add(Notification(
                                user_id=officer_user.id,
                                complaint_id=c.id,
                                message=f"⚡ Predictive SLA Alert: Complaint #{c.id} ({c.category.name}) predicted at {prob}% breach risk before 75% SLA threshold.",
                                notification_type="SLA_Predictive_Warning"
                            ))
                            updated += 1

    if updated > 0:
        db.commit()
    return updated


def get_escalation_details(complaint: Complaint) -> Tuple[Optional[int], Optional[str], Optional[float]]:
    """
    Computes progressive escalation level (1, 2, 3) and stage details if breached and unresolved.
    Level 1: <= 12 hours overdue -> Assistant Executive Engineer (AEE)
    Level 2: 12-24 hours overdue -> Executive Engineer (EE)
    Level 3: > 24 hours overdue  -> Chief Commissioner & State Monitoring Cell
    """
    if not complaint.sla_deadline:
        return None, None, None
    now = datetime.utcnow()
    if now <= complaint.sla_deadline or complaint.status in ["Resolved", "Closed"]:
        return None, None, None

    hours_overdue = round((now - complaint.sla_deadline).total_seconds() / 3600.0, 2)
    if hours_overdue <= 12.0:
        return 1, "Level 1: Escalated to Assistant Executive Engineer (AEE)", hours_overdue
    elif hours_overdue <= 24.0:
        return 2, "Level 2: Escalated to Executive Engineer (EE)", hours_overdue
    else:
        return 3, "Level 3: Escalated to Chief Commissioner & State Monitoring Cell", hours_overdue


def get_predictive_early_warning(complaint: Complaint) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Calls Phase 16 ML model before the 75% SLA threshold (pct_elapsed < 0.75).
    If breach risk >= 60%, triggers an early warning before the normal 75% threshold.
    """
    if not complaint.sla_deadline:
        return False, None, None
    now = datetime.utcnow()
    if now > complaint.sla_deadline or complaint.status in ["Resolved", "Closed"]:
        return False, None, None

    total_sec = (complaint.sla_deadline - complaint.created_at).total_seconds()
    if total_sec <= 0:
        return False, None, None
    pct = (now - complaint.created_at).total_seconds() / total_sec
    if pct >= 0.75:
        # Already at or past the 75% SLA warning threshold
        return False, None, None

    # Evaluate Phase 16 predictive ML risk before the 75% threshold
    try:
        from backend.app.services.predictive import predictive_service, WARD_TO_ZONE
        cat_name = complaint.category.name if complaint.category else "Others"
        dept_code = complaint.category.department.code if complaint.category and complaint.category.department else "BBMP"
        ward = "Central"
        if complaint.location_address:
            for w in WARD_TO_ZONE.keys():
                if w in complaint.location_address.lower():
                    ward = w.title()
                    break

        pred = predictive_service.predict_complaint_risk(
            category=cat_name,
            ward=ward,
            priority=complaint.priority or "Medium",
            dept=dept_code,
            filed_at=complaint.created_at,
            sla_status=complaint.sla_status or "Normal",
            impact_count=getattr(complaint, "impact_count", 1) or 1
        )
        prob_pct = pred.get("sla_breach_probability_pct", 0.0)
        if prob_pct >= 60.0:
            msg = f"⚡ Predictive SLA Early Warning: High breach risk ({prob_pct}%) forecasted by Phase 16 ML before 75% threshold."
            return True, prob_pct, msg
        return False, prob_pct, None
    except Exception:
        return False, None, None


def get_sla_summary(complaint: Complaint) -> dict:
    """Returns a serializable SLA summary dict for API responses."""
    sla_status_val, pct = get_sla_status(complaint)
    deadline_str = complaint.sla_deadline.isoformat() if complaint.sla_deadline else None
    hours_remaining: Optional[float] = None
    sla_duration_hours: Optional[float] = None
    sla_duration_str: Optional[str] = None
    time_remaining_str: Optional[str] = None
    resolution_sla_status: str = "On Track"
    is_breached = False

    if complaint.sla_deadline and complaint.created_at:
        dur_sec = (complaint.sla_deadline - complaint.created_at).total_seconds()
        sla_duration_hours = round(dur_sec / 3600.0, 1)
        if sla_duration_hours.is_integer():
            sla_duration_str = f"{int(sla_duration_hours)}h"
        else:
            sla_duration_str = f"{sla_duration_hours}h"

    is_resolved = complaint.status in ["Resolved", "Closed"]
    resolved_time = None
    if is_resolved:
        if hasattr(complaint, "status_history") and complaint.status_history:
            for sh in reversed(complaint.status_history):
                if sh.status in ["Resolved", "Closed"]:
                    resolved_time = sh.created_at
                    break
        if not resolved_time:
            resolved_time = complaint.updated_at or complaint.created_at

    if is_resolved:
        if complaint.sla_deadline and resolved_time:
            if resolved_time <= complaint.sla_deadline and (complaint.sla_status != "Breached"):
                resolution_sla_status = "Resolved within SLA"
                time_remaining_str = "Resolved on time"
                is_breached = False
            else:
                resolution_sla_status = "Breached SLA"
                overdue_h = round((resolved_time - complaint.sla_deadline).total_seconds() / 3600.0, 1)
                time_remaining_str = f"Resolved after breach (+{max(0.1, overdue_h)}h)"
                is_breached = True
        else:
            resolution_sla_status = "Resolved within SLA"
            time_remaining_str = "Resolved"
    else:
        if complaint.sla_deadline:
            delta = (complaint.sla_deadline - datetime.utcnow()).total_seconds()
            hours_remaining = round(delta / 3600, 2)
            if hours_remaining > 0:
                h_int = int(hours_remaining)
                m_int = int((hours_remaining - h_int) * 60)
                time_remaining_str = f"{h_int}h {m_int}m left" if h_int > 0 else f"{m_int}m left"
                if (complaint.sla_status or sla_status_val) == "Warning":
                    resolution_sla_status = "Approaching SLA"
                else:
                    resolution_sla_status = "On Track"
                is_breached = False
            else:
                overdue = round(abs(hours_remaining), 1)
                time_remaining_str = f"Breached by {overdue}h"
                resolution_sla_status = "SLA Breached"
                is_breached = True
        else:
            resolution_sla_status = "On Track"
            time_remaining_str = "No SLA"

    effective_sla_status = "Breached" if is_breached else (complaint.sla_status or sla_status_val)
    if is_resolved and not is_breached:
        effective_sla_status = "Normal"

    esc_level, esc_stage, hours_overdue = (None, None, None) if is_resolved else get_escalation_details(complaint)
    is_early_warn, breach_prob, warn_msg = (False, None, None) if is_resolved else get_predictive_early_warning(complaint)

    return {
        "sla_deadline": deadline_str,
        "sla_status": effective_sla_status,
        "is_escalated": complaint.is_escalated or (esc_level is not None),
        "pct_elapsed": 100.0 if is_breached else (0.0 if is_resolved else round(min(pct, 1.0) * 100, 1)),
        "hours_remaining": hours_remaining,
        "sla_duration_hours": sla_duration_hours,
        "sla_duration_str": sla_duration_str,
        "time_remaining_str": time_remaining_str,
        "resolution_sla_status": resolution_sla_status,
        "is_breached": is_breached,
        "predictive_early_warning": is_early_warn,
        "predictive_breach_prob": breach_prob,
        "predictive_message": warn_msg,
        "hours_overdue": hours_overdue,
        "escalation_level": esc_level,
        "escalation_stage": esc_stage,
    }

