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

    if updated > 0:
        db.commit()
    return updated


def get_sla_summary(complaint: Complaint) -> dict:
    """Returns a serializable SLA summary dict for API responses."""
    sla_status_val, pct = get_sla_status(complaint)
    deadline_str = complaint.sla_deadline.isoformat() if complaint.sla_deadline else None
    hours_remaining: Optional[float] = None
    if complaint.sla_deadline:
        delta = (complaint.sla_deadline - datetime.utcnow()).total_seconds()
        hours_remaining = round(delta / 3600, 2)

    return {
        "sla_deadline": deadline_str,
        "sla_status": complaint.sla_status or sla_status_val,
        "is_escalated": complaint.is_escalated or False,
        "pct_elapsed": round(min(pct, 1.0) * 100, 1),
        "hours_remaining": hours_remaining,
    }
