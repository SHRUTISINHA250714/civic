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

# ── Separate Response SLA and Resolution SLA Default Timings ───────────────────
# Critical: 2h response, 24h resolution
# High:     4h response, 48h resolution
# Medium:   8h response, 72h resolution
# Low:      24h response, 120h resolution
DEFAULT_RESPONSE_SLA_HOURS = {
    "Critical": 2.0,
    "High":     4.0,
    "Medium":   8.0,
    "Low":      24.0,
}

DEFAULT_RESOLUTION_SLA_HOURS = {
    "Critical": 24.0,
    "High":     48.0,
    "Medium":   72.0,
    "Low":      120.0,
}

# Backward compatibility alias (Resolution SLA)
DEFAULT_SLA_HOURS = DEFAULT_RESOLUTION_SLA_HOURS


def compute_response_sla_deadline(
    db: Optional[Session],
    category_id: int,
    priority: str,
    filed_at: Optional[datetime] = None,
) -> datetime:
    """
    Returns the Response SLA deadline datetime for a complaint.
    Looks up the SLAPolicy table first; falls back to defaults.
    """
    if filed_at is None:
        filed_at = datetime.utcnow()

    hours = DEFAULT_RESPONSE_SLA_HOURS.get(priority, 8.0)
    if db:
        try:
            policy = db.query(SLAPolicy).filter(
                SLAPolicy.category_id == category_id,
                SLAPolicy.priority == priority,
            ).first()
            if policy and getattr(policy, "response_hours", None) is not None:
                hours = policy.response_hours
        except Exception:
            pass

    return filed_at + timedelta(hours=hours)


def compute_resolution_sla_deadline(
    db: Optional[Session],
    category_id: int,
    priority: str,
    filed_at: Optional[datetime] = None,
) -> datetime:
    """
    Returns the Resolution SLA deadline datetime for a complaint.
    Looks up the SLAPolicy table first; falls back to defaults.
    """
    if filed_at is None:
        filed_at = datetime.utcnow()

    hours = DEFAULT_RESOLUTION_SLA_HOURS.get(priority, 72.0)
    if db:
        try:
            policy = db.query(SLAPolicy).filter(
                SLAPolicy.category_id == category_id,
                SLAPolicy.priority == priority,
            ).first()
            if policy and policy.resolution_hours:
                hours = policy.resolution_hours
        except Exception:
            pass

    return filed_at + timedelta(hours=hours)


# Backward compatibility alias for compute_resolution_sla_deadline
compute_sla_deadline = compute_resolution_sla_deadline


def get_sla_status(
    complaint: Complaint,
    db: Optional[Session] = None,
) -> Tuple[str, float]:
    """
    Evaluates the current Resolution SLA status of a complaint.
    Returns (sla_status, pct_elapsed) where pct_elapsed is 0.0-1.0+.
      - "Normal"  : < warning threshold elapsed
      - "Warning" : >= warning threshold but not yet breached
      - "Breached": resolution deadline passed
    """
    if not complaint.sla_deadline:
        return "Normal", 0.0

    now = datetime.utcnow()
    deadline = complaint.sla_deadline
    filed_at = complaint.created_at or now

    total_seconds = (deadline - filed_at).total_seconds()
    if total_seconds <= 0:
        return "Breached", 1.0

    elapsed_seconds = (now - filed_at).total_seconds()
    pct_elapsed = elapsed_seconds / total_seconds

    # Fetch warning threshold from policy if DB provided
    warning_threshold = 0.75
    if db:
        try:
            policy = db.query(SLAPolicy).filter(
                SLAPolicy.category_id == complaint.category_id,
                SLAPolicy.priority == complaint.priority,
            ).first()
            if policy and policy.warning_threshold_pct:
                warning_threshold = policy.warning_threshold_pct
        except Exception:
            pass

    if now > deadline:
        return "Breached", pct_elapsed
    elif pct_elapsed >= warning_threshold:
        return "Warning", pct_elapsed
    else:
        return "Normal", pct_elapsed


def update_all_sla_statuses(db: Session) -> int:
    """
    Scans all active (non-Closed, non-Resolved) complaints and updates their
    sla_status and response_sla_status fields. Sends escalation notifications for
    actual breaches.
    Returns count of updated records.
    """
    active_statuses = ["Registered", "Accepted", "In Progress", "Reopened"]
    complaints = db.query(Complaint).filter(
        Complaint.status.in_(active_statuses),
        Complaint.sla_deadline.isnot(None),
    ).all()

    updated = 0
    now = datetime.utcnow()

    for c in complaints:
        new_status, pct = get_sla_status(c, db)
        old_status = c.sla_status or "Normal"

        # Update response SLA status
        if c.status == "Registered":
            resp_deadline = getattr(c, "response_sla_deadline", None) or compute_response_sla_deadline(
                db, c.category_id, c.priority, c.created_at
            )
            if now > resp_deadline and getattr(c, "response_sla_status", "Pending") != "Breached":
                c.response_sla_status = "Breached"
                updated += 1
        else:
            if hasattr(c, "response_sla_status") and c.response_sla_status not in ["Met", "Responded"]:
                c.response_sla_status = "Met"
                updated += 1

        if new_status != old_status:
            c.sla_status = new_status
            updated += 1

            # ── Actual resolution breach (only when deadline passed) ──────────
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
                            cat_name = c.category.name if c.category else "General"
                            db.add(Notification(
                                user_id=officer_user.id,
                                complaint_id=c.id,
                                message=(
                                    f"🚨 SLA BREACH: Complaint #{c.id} "
                                    f"({cat_name}) has exceeded its "
                                    f"resolution SLA deadline. Immediate action required!"
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

            # ── Warning state → alert officer ─────────────────────────────────
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
                            cat_name = c.category.name if c.category else "General"
                            db.add(Notification(
                                user_id=officer_user.id,
                                complaint_id=c.id,
                                message=(
                                    f"⏰ SLA Warning: Complaint #{c.id} "
                                    f"({cat_name}) is approaching its "
                                    f"SLA deadline. Please resolve soon."
                                ),
                                notification_type="SLA_Warning",
                            ))

        # ── Progressive Escalation (STRICTLY for actual breaches) ─────────────
        if new_status == "Breached" and now > c.sla_deadline:
            esc_level, esc_stage, hours_overdue = get_escalation_details(c)
            if esc_level and esc_level >= 2:
                existing_esc_notif = db.query(Notification).filter(
                    Notification.complaint_id == c.id,
                    Notification.notification_type == f"SLA_Escalation_L{esc_level}"
                ).first()
                if not existing_esc_notif:
                    cat_name = c.category.name if c.category else "General"
                    if c.assigned_officer_id:
                        from backend.app.models.user import User, Officer
                        officer = db.query(Officer).filter(Officer.id == c.assigned_officer_id).first()
                        if officer:
                            officer_user = db.query(User).filter(User.id == officer.user_id).first()
                            if officer_user:
                                db.add(Notification(
                                    user_id=officer_user.id,
                                    complaint_id=c.id,
                                    message=f"🚨 PROGRESSIVE ESCALATION: Complaint #{c.id} ({cat_name}) is {hours_overdue}h overdue. {esc_stage}.",
                                    notification_type=f"SLA_Escalation_L{esc_level}"
                                ))
                    db.add(Notification(
                        user_id=c.citizen_id,
                        complaint_id=c.id,
                        message=f"📢 Progressive Escalation Notice: Your grievance #{c.id} ({hours_overdue}h overdue) has progressed to {esc_stage}.",
                        notification_type=f"SLA_Escalation_L{esc_level}"
                    ))
                    updated += 1

        # ── Predictive SLA Early Warning Check (BEFORE resolution deadline) ───
        elif new_status != "Breached" and now <= c.sla_deadline:
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
                            cat_name = c.category.name if c.category else "General"
                            db.add(Notification(
                                user_id=officer_user.id,
                                complaint_id=c.id,
                                message=f"⚡ {warn_msg} for Complaint #{c.id} ({cat_name}). Prioritize this complaint.",
                                notification_type="SLA_Predictive_Warning"
                            ))
                            updated += 1

    if updated > 0:
        db.commit()
    return updated


def get_escalation_details(complaint: Complaint) -> Tuple[Optional[int], Optional[str], Optional[float]]:
    """
    Computes progressive escalation level (1, 2, 3) and stage details.
    Display escalation level ONLY after an actual resolution SLA breach (now > complaint.sla_deadline).
    Level 1: <= 12 hours overdue -> Assistant Executive Engineer (AEE)
    Level 2: 12-24 hours overdue -> Executive Engineer (EE)
    Level 3: > 24 hours overdue  -> Chief Commissioner & State Monitoring Cell
    """
    if not complaint.sla_deadline:
        return None, None, None
    now = datetime.utcnow()
    # Escalation is strictly displayed after actual resolution deadline breach
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
    Calls Random Forest ML model before the resolution SLA deadline (now <= complaint.sla_deadline).
    If breach risk >= 60%, triggers:
      'AI Warning: X% probability of SLA breach'
    """
    if not complaint.sla_deadline:
        return False, None, None
    now = datetime.utcnow()
    if now > complaint.sla_deadline or complaint.status in ["Resolved", "Closed"]:
        return False, None, None

    # Evaluate Random Forest ML breach risk before the deadline
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
            msg = f"AI Warning: {prob_pct}% probability of SLA breach"
            return True, prob_pct, msg
        return False, prob_pct, None
    except Exception:
        return False, None, None


def get_sla_summary(complaint: Complaint) -> dict:
    """
    Returns a serializable SLA summary dict for API responses, distinguishing
    between Response SLA and Resolution SLA, and between actual breaches and
    AI-predicted breach warnings.
    """
    now = datetime.utcnow()
    sla_status_val, pct = get_sla_status(complaint)
    deadline_str = complaint.sla_deadline.isoformat() if complaint.sla_deadline else None
    hours_remaining: Optional[float] = None
    sla_duration_hours: Optional[float] = None
    sla_duration_str: Optional[str] = None
    time_remaining_str: Optional[str] = None
    resolution_sla_status: str = "On Track"
    is_breached = False

    # ── Resolution SLA Duration ──────────────────────────────────────────────
    if complaint.sla_deadline and complaint.created_at:
        dur_sec = (complaint.sla_deadline - complaint.created_at).total_seconds()
        sla_duration_hours = round(dur_sec / 3600.0, 1)
        if sla_duration_hours.is_integer():
            sla_duration_str = f"{int(sla_duration_hours)}h"
        else:
            sla_duration_str = f"{sla_duration_hours}h"
    else:
        sla_duration_hours = DEFAULT_RESOLUTION_SLA_HOURS.get(complaint.priority, 72.0)
        sla_duration_str = f"{int(sla_duration_hours)}h"

    # ── Resolution Status Evaluation ─────────────────────────────────────────
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
            is_breached = False
    else:
        if complaint.sla_deadline:
            delta = (complaint.sla_deadline - now).total_seconds()
            hours_remaining = round(delta / 3600.0, 2)
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

    # Effective status: "Breached" strictly when actual resolution deadline passed
    effective_sla_status = "Breached" if is_breached else (complaint.sla_status or sla_status_val)
    if is_resolved and not is_breached:
        effective_sla_status = "Normal"

    # Escalation level ONLY after actual breach
    esc_level, esc_stage, hours_overdue = (get_escalation_details(complaint) if is_breached else (None, None, None))

    # Predictive Early Warning ONLY before deadline (and not resolved)
    if not is_resolved and not is_breached:
        is_early_warn, breach_prob, warn_msg = get_predictive_early_warning(complaint)
        recommended_action = "Prioritize this complaint." if is_early_warn else None
    else:
        is_early_warn, breach_prob, warn_msg, recommended_action = False, None, None, None

    # ── Response SLA Evaluation ──────────────────────────────────────────────
    resp_deadline = getattr(complaint, "response_sla_deadline", None)
    if not resp_deadline:
        resp_deadline = compute_response_sla_deadline(
            None, complaint.category_id, complaint.priority, complaint.created_at
        )
    resp_deadline_str = resp_deadline.isoformat() if resp_deadline else None

    resp_dur_hours = DEFAULT_RESPONSE_SLA_HOURS.get(complaint.priority, 8.0)
    if resp_deadline and complaint.created_at:
        dur_r_sec = (resp_deadline - complaint.created_at).total_seconds()
        resp_dur_hours = round(dur_r_sec / 3600.0, 1)
    resp_dur_str = f"{int(resp_dur_hours)}h" if resp_dur_hours.is_integer() else f"{resp_dur_hours}h"

    response_sla_status = "Pending Response"
    response_is_breached = False
    response_hours_remaining = None
    response_time_remaining_str = None

    if complaint.status in ["Accepted", "In Progress", "Resolved", "Closed"]:
        # Find earliest response transition timestamp
        responded_time = None
        if hasattr(complaint, "status_history") and complaint.status_history:
            for sh in complaint.status_history:
                if sh.status in ["Accepted", "In Progress", "Resolved", "Closed"]:
                    responded_time = sh.created_at
                    break
        if not responded_time:
            responded_time = complaint.updated_at or complaint.created_at

        if resp_deadline and responded_time:
            if responded_time <= resp_deadline:
                response_sla_status = "Responded within SLA"
                response_time_remaining_str = "Responded on time"
                response_is_breached = False
                response_hours_remaining = 0.0
            else:
                response_sla_status = "Breached Response SLA"
                r_overdue = round((responded_time - resp_deadline).total_seconds() / 3600.0, 1)
                response_time_remaining_str = f"Responded after breach (+{max(0.1, r_overdue)}h)"
                response_is_breached = True
                response_hours_remaining = -r_overdue
        else:
            response_sla_status = "Responded within SLA"
            response_time_remaining_str = "Responded on time"
            response_is_breached = False
            response_hours_remaining = 0.0
    else:
        # Still awaiting initial officer response (e.g. Registered)
        if resp_deadline:
            delta_r = (resp_deadline - now).total_seconds()
            response_hours_remaining = round(delta_r / 3600.0, 2)
            if response_hours_remaining > 0:
                rh_int = int(response_hours_remaining)
                rm_int = int((response_hours_remaining - rh_int) * 60)
                response_time_remaining_str = f"{rh_int}h {rm_int}m left to respond" if rh_int > 0 else f"{rm_int}m left to respond"
                response_sla_status = "Pending Response"
                response_is_breached = False
            else:
                r_overdue = round(abs(response_hours_remaining), 1)
                response_time_remaining_str = f"Response Breached by {r_overdue}h"
                response_sla_status = "Breached Response SLA"
                response_is_breached = True
        else:
            response_sla_status = "Pending Response"
            response_time_remaining_str = "Awaiting response"

    return {
        # ── Resolution SLA (Primary SLA) ──────────────────────────────────────
        "sla_deadline": deadline_str,
        "sla_status": effective_sla_status,
        "is_escalated": (is_breached and (complaint.is_escalated or (esc_level is not None))),
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
        "recommended_action": recommended_action,
        "hours_overdue": hours_overdue,
        "escalation_level": esc_level,
        "escalation_stage": esc_stage,

        # Explicit Resolution SLA aliases
        "resolution_sla_deadline": deadline_str,
        "resolution_sla_duration_hours": sla_duration_hours,
        "resolution_sla_duration_str": sla_duration_str,
        "resolution_hours_remaining": hours_remaining,

        # ── Response SLA ──────────────────────────────────────────────────────
        "response_sla_deadline": resp_deadline_str,
        "response_sla_duration_hours": resp_dur_hours,
        "response_sla_duration_str": resp_dur_str,
        "response_hours_remaining": response_hours_remaining,
        "response_time_remaining_str": response_time_remaining_str,
        "response_sla_status": response_sla_status,
        "response_is_breached": response_is_breached,
    }


