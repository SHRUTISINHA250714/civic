import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.user import User, Officer
from backend.app.models.department import Department
from backend.app.models.complaint import (
    Complaint, ComplaintCategory, ComplaintImage,
    ComplaintStatusHistory, AIPrediction, DuplicateComplaintMapping,
    Notification, ComplaintEvidenceCheck
)
from backend.app.schemas.complaint import (
    ComplaintResponse, DuplicateWarningResponse, ComplaintStatusUpdate,
    CitizenVerifyResolutionRequest, EvidenceCheckResponse
)
from backend.app.routers.deps import get_current_active_user, get_current_citizen, get_current_officer
from backend.app.services import (
    translate_text, classify_complaint, classify_complaint_structured, predict_priority,
    verify_image, get_detected_objects, transcribe_audio,
    check_duplicate_complaint, assign_officer_to_complaint,
    compute_evidence_trust, compute_sla_deadline, get_sla_summary
)
from backend.app.services.duplicate import haversine_distance

router = APIRouter(prefix="/complaints", tags=["Complaints"])


# ─────────────────────────────────────────────────────────────────────────────
# GET /complaints/departments-categories — List the 4 departments & their categories
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/departments-categories")
def get_departments_and_categories(db: Session = Depends(get_db)):
    """Returns the 4 Karnataka Civic Authorities (BBMP, BESCOM, BWSSB, BSWML) and their active categories."""
    dept_order = ["BBMP", "BESCOM", "BWSSB", "BSWML"]
    dept_domains = {
        "BBMP": "Roads & Civic Infrastructure (BBMP)",
        "BESCOM": "Electricity & Power Supply (BESCOM)",
        "BWSSB": "Water Supply & Sewerage Drainage (BWSSB)",
        "BSWML": "Solid Waste Management & Sanitation (BSWML)",
    }
    
    all_depts = db.query(Department).all()
    # Filter to only the 4 valid departments
    valid_depts = [d for d in all_depts if d.code in dept_domains]
    # Sort in canonical order
    valid_depts.sort(key=lambda d: dept_order.index(d.code) if d.code in dept_order else 99)
    
    result = []
    for d in valid_depts:
        categories = (
            db.query(ComplaintCategory)
            .filter(ComplaintCategory.department_id == d.id, ComplaintCategory.is_active == True)
            .order_by(ComplaintCategory.name)
            .all()
        )
        result.append({
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "domain": dept_domains.get(d.code, "Civic Services"),
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "default_priority": cat.default_priority,
                }
                for cat in categories
            ]
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints/preview-ai — Real-time live AI translation & routing preview
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/preview-ai")
def preview_complaint_ai(
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Live AI assistance: Detects language, translates to English, predicts category,
    priority, agency, subcategory, and evidence requirements across the 4 departments.
    """
    if not description or len(description.strip()) < 3:
        return {
            "original_text": description,
            "translated_text": description,
            "detected_language": "en",
            "agency": "BBMP",
            "category": "Roads",
            "subcategory": "Pothole",
            "requires_image": True,
            "requires_gps": True,
            "predicted_department": "BBMP",
            "predicted_department_name": "Bruhat Bengaluru Mahanagara Palike",
            "predicted_category_name": "Potholes & Damaged Roads",
            "predicted_category_id": None,
            "predicted_priority": "Medium",
            "confidence": 0.50
        }

    translated_desc, detected_lang, _ = translate_text(description)
    structured_ai = classify_complaint_structured(translated_desc)
    predicted_priority, prio_conf = predict_priority(translated_desc, structured_ai["predicted_category_name"])

    cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == structured_ai["predicted_category_name"]).first()
    if not cat:
        cat = db.query(ComplaintCategory).filter(ComplaintCategory.name == "Others").first()

    dept_code = structured_ai["agency"]
    dept_name = cat.department.name if cat and cat.department else structured_ai.get("agency_full_name", "Bruhat Bengaluru Mahanagara Palike")

    return {
        "original_text": description,
        "translated_text": translated_desc,
        "detected_language": detected_lang,
        "agency": structured_ai["agency"],
        "category": structured_ai["category"],
        "subcategory": structured_ai["subcategory"],
        "requires_image": structured_ai["requires_image"],
        "requires_gps": structured_ai["requires_gps"],
        "predicted_department": dept_code,
        "predicted_department_name": dept_name,
        "predicted_category_name": cat.name if cat else structured_ai["predicted_category_name"],
        "predicted_category_id": cat.id if cat else None,
        "predicted_priority": predicted_priority,
        "confidence": structured_ai["confidence"]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Serialise a Complaint ORM object to API response dict
# ─────────────────────────────────────────────────────────────────────────────
def serialize_complaint(c: Complaint, db: Session) -> dict:
    citizen_name    = c.citizen.name
    category_name   = c.category.name
    department_name = c.category.department.name
    department_id   = c.category.department.id

    assigned_officer_name = None
    if c.assigned_officer:
        officer_user = db.query(User).filter(User.id == c.assigned_officer.user_id).first()
        if officer_user:
            assigned_officer_name = officer_user.name

    images_res = [
        {
            "id": img.id,
            "image_url": img.image_url,
            "image_type": img.image_type,
            "is_verified": img.is_verified,
            "confidence_score": img.confidence_score,
            "bounding_boxes": getattr(img, "bounding_boxes", None),
            "quality_status": getattr(img, "quality_status", None),
            "perceptual_hash": getattr(img, "perceptual_hash", None),
            "created_at": img.created_at,
        }
        for img in c.images
    ]

    history_res = [
        {
            "id": h.id,
            "status": h.status,
            "remarks": h.remarks,
            "changed_by_name": h.changed_by_user.name,
            "created_at": h.created_at,
        }
        for h in c.status_history
    ]

    ai_pred_res = None
    if c.ai_prediction:
        ai_pred_res = {
            "id":                       c.ai_prediction.id,
            "predicted_category_name":  c.ai_prediction.predicted_category.name,
            "category_confidence":      c.ai_prediction.category_confidence,
            "predicted_priority":       c.ai_prediction.predicted_priority,
            "priority_confidence":      c.ai_prediction.priority_confidence,
            "translation_time":         c.ai_prediction.translation_time,
            "transcription_used":       c.ai_prediction.transcription_used,
            "created_at":               c.ai_prediction.created_at,
        }

    evidence_res = None
    if c.evidence_check:
        ev = c.evidence_check
        evidence_res = {
            "verification_decision":    getattr(ev, "verification_decision", "VERIFIED") or "VERIFIED",
            "trust_score":              ev.trust_score,
            "trust_level":              ev.trust_level,
            "live_gps_provided":        ev.live_gps_provided,
            "exif_gps_found":           ev.exif_gps_found,
            "gps_distance_m":           ev.gps_distance_m,
            "gps_match":                ev.gps_match,
            "gps_accuracy":             getattr(ev, "gps_accuracy", None),
            "geo_status":               getattr(ev, "geo_status", "MATCH") or "MATCH",
            "timestamp_valid":          ev.timestamp_valid,
            "freshness_status":         getattr(ev, "freshness_status", "FRESH") or "FRESH",
            "vision_objects_detected":  ev.vision_objects_detected,
            "vision_agreement_score":   ev.vision_agreement_score,
            "semantic_match_status":    getattr(ev, "semantic_match_status", "MATCH") or "MATCH",
            "semantic_confidence":      getattr(ev, "semantic_confidence", 0.0) or 0.0,
            "image_category":           getattr(ev, "image_category", None),
            "is_reused_image":          getattr(ev, "is_reused_image", False) or False,
            "reused_complaint_id":      getattr(ev, "reused_complaint_id", None),
            "quality_check":            getattr(ev, "quality_check", None),
            "gate_reasons":             getattr(ev, "gate_reasons", None),
            "verification_details":     ev.verification_details,
        }

    sla_res = get_sla_summary(c)

    # Phase 10 Duplicate & Impact calculations
    is_duplicate = False
    parent_complaint_id = None
    child_report_id = None
    parent_status = None
    impact_count = getattr(c, "impact_count", 1) or 1
    dup_message = None
    parent_history_res = []
    child_count = 0

    if c.duplicate_of_complaint_id:
        is_duplicate = True
        parent_complaint_id = c.duplicate_of_complaint_id
        child_report_id = c.id
        parent = db.query(Complaint).filter(Complaint.id == c.duplicate_of_complaint_id).first()
        if parent:
            parent_status = parent.status
            impact_count = parent.impact_count or 1
            dup_message = f"This issue has already been reported by another citizen. Your report has been linked to Complaint #{parent.id}."
            parent_history_res = [
                {
                    "id": h.id,
                    "status": h.status,
                    "remarks": h.remarks,
                    "changed_by_name": h.changed_by_user.name if h.changed_by_user else "System",
                    "created_at": h.created_at,
                }
                for h in parent.status_history
            ]
        else:
            parent_status = c.status
    else:
        child_count = db.query(func.count(Complaint.id)).filter(
            Complaint.duplicate_of_complaint_id == c.id
        ).scalar() or 0
        impact_count = max(getattr(c, "impact_count", 1) or 1, child_count + 1)

    return {
        "id":                       c.id,
        "citizen_id":               c.citizen_id,
        "citizen_name":             citizen_name,
        "category_id":              c.category_id,
        "category_name":            category_name,
        "department_id":            department_id,
        "department_name":          department_name,
        "description":              c.description,
        "original_description":     c.original_description,
        "language":                 c.language,
        "detected_language":        c.detected_language,
        "audio_url":                c.audio_url,
        "location_latitude":        c.location_latitude,
        "location_longitude":       c.location_longitude,
        "location_address":         c.location_address,
        "status":                   c.status,
        "priority":                 c.priority,
        "assigned_officer_id":      c.assigned_officer_id,
        "assigned_officer_name":    assigned_officer_name,
        "duplicate_of_complaint_id": c.duplicate_of_complaint_id,
        "sla_deadline":             c.sla_deadline.isoformat() if c.sla_deadline else None,
        "sla_status":               c.sla_status or "Normal",
        "is_escalated":             c.is_escalated or False,
        "citizen_verified":         c.citizen_verified,
        "citizen_feedback_rating":  c.citizen_feedback_rating,
        "citizen_feedback_remarks": c.citizen_feedback_remarks,
        "reopen_count":             c.reopen_count or 0,
        "created_at":               c.created_at,
        "updated_at":               c.updated_at,
        "images":                   images_res,
        "status_history":           history_res,
        "ai_prediction":            ai_pred_res,
        "evidence_check":           evidence_res,
        "sla_summary":              sla_res,
        "is_duplicate":             is_duplicate,
        "parent_complaint_id":      parent_complaint_id,
        "child_report_id":          child_report_id,
        "parent_status":            parent_status,
        "impact_count":             impact_count,
        "message":                  dup_message,
        "parent_status_history":    parent_history_res,
        "linked_reports_count":     child_count if not is_duplicate else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints/check-duplicate
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/check-duplicate", response_model=DuplicateWarningResponse)
def check_duplicate(
    latitude:      float = Form(...),
    longitude:     float = Form(...),
    description:   str   = Form(...),
    category_name: str   = Form(...),
    db: Session = Depends(get_db)
):
    category = db.query(ComplaintCategory).filter(ComplaintCategory.name == category_name).first()
    if not category:
        return {"is_duplicate": False, "duplicate_of_id": None, "similarity_score": 0.0,
                "message": "Category not found."}

    is_dup, dup_id, score = check_duplicate_complaint(
        db, latitude, longitude, description, category.id,
        distance_threshold_m=100.0, similarity_threshold=0.85
    )

    if is_dup and dup_id:
        parent = db.query(Complaint).filter(Complaint.id == dup_id).first()
        parent_status = parent.status if parent else "In Progress"
        parent_category = parent.category.name if parent and parent.category else category_name
        parent_location = (parent.location_address or f"({parent.location_latitude:.4f}, {parent.location_longitude:.4f})") if parent else "Nearby"
        impact_count = (parent.impact_count or 1) if parent else 1

        return {
            "is_duplicate": True,
            "duplicate_of_id": dup_id,
            "parent_complaint_id": dup_id,
            "similarity_score": round(score, 4),
            "parent_status": parent_status,
            "parent_category": parent_category,
            "parent_location": parent_location,
            "impact_count": impact_count,
            "message": f"This issue has already been reported nearby. Linked to Complaint #{dup_id}.",
        }
    return {
        "is_duplicate": False,
        "duplicate_of_id": None,
        "parent_complaint_id": None,
        "similarity_score": round(score, 4),
        "parent_status": None,
        "parent_category": None,
        "parent_location": None,
        "impact_count": 1,
        "message": "No duplicate issues detected nearby.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints  — raise a new complaint (text, voice, or image)
# ─────────────────────────────────────────────────────────────────────────────
@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def raise_complaint(
    description:        str            = Form(...),
    language:           str            = Form("English"),
    location_latitude:  float          = Form(...),
    location_longitude: float          = Form(...),
    location_address:   Optional[str]  = Form(None),
    category_id:        Optional[int]  = Form(None),
    department_id:      Optional[int]  = Form(None),
    duplicate_of_id:    Optional[int]  = Form(None),
    gps_accuracy:       Optional[float] = Form(None),
    file:               Optional[UploadFile] = File(None),
    audio_file:         Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_citizen)
):
    original_description = description
    audio_url: Optional[str] = None
    transcription_used = False

    # ── 0. Voice / Audio Transcription ────────────────────────────────────────
    if audio_file:
        audio_ext = os.path.splitext(audio_file.filename or "audio.wav")[1] or ".wav"
        audio_filename = f"audio_{uuid.uuid4()}{audio_ext}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        audio_path = os.path.join(settings.UPLOAD_DIR, audio_filename)
        with open(audio_path, "wb") as buf:
            shutil.copyfileobj(audio_file.file, buf)
        audio_url = f"/static/uploads/{audio_filename}"

        transcribed, src = transcribe_audio(audio_path)
        if transcribed and src == "speech_recognition":
            description = transcribed
            transcription_used = True
        elif transcribed:
            # Append to description if auto-transcription not available
            description = f"{description} | [Voice Note: {transcribed}]"

    # ── 1. Translation and Language Detection ─────────────────────────────────
    translated_desc, detected_lang, trans_time = translate_text(description)

    # ── 2. Category Selection / AI Classification ─────────────────────────────
    # Check if citizen explicitly specified a category
    category = None
    if category_id:
        category = db.query(ComplaintCategory).filter(ComplaintCategory.id == category_id).first()

    predicted_cat_name, cat_conf = classify_complaint(translated_desc)
    
    if not category:
        category = db.query(ComplaintCategory).filter(ComplaintCategory.name == predicted_cat_name).first()
        if not category:
            category = db.query(ComplaintCategory).filter(ComplaintCategory.name == "Others").first()
            predicted_cat_name = "Others"
            cat_conf = 0.50
    else:
        # If user explicitly chose, keep category confidence high
        cat_conf = 1.0

    # ── 3. AI Priority Prediction ─────────────────────────────────────────────
    predicted_priority, prio_conf = predict_priority(translated_desc, category.name)

    # ── 4. Duplicate Detection ────────────────────────────────────────────────
    assigned_duplicate_id = duplicate_of_id
    duplicate_score = 0.0
    if not assigned_duplicate_id:
        is_dup, dup_id, score = check_duplicate_complaint(
            db, location_latitude, location_longitude, translated_desc, category.id,
            distance_threshold_m=100.0, similarity_threshold=0.85
        )
        if is_dup:
            assigned_duplicate_id = dup_id
            duplicate_score = score
    else:
        duplicate_score = 1.0

    # Ensure assigned_duplicate_id links to root operational complaint
    parent_complaint = None
    if assigned_duplicate_id:
        parent_candidate = db.query(Complaint).filter(Complaint.id == assigned_duplicate_id).first()
        if parent_candidate:
            if parent_candidate.duplicate_of_complaint_id:
                root_parent = db.query(Complaint).filter(Complaint.id == parent_candidate.duplicate_of_complaint_id).first()
                if root_parent:
                    assigned_duplicate_id = root_parent.id
                    parent_complaint = root_parent
                else:
                    parent_complaint = parent_candidate
            else:
                parent_complaint = parent_candidate
        else:
            assigned_duplicate_id = None

    # Idempotency check: did this citizen already submit a duplicate report for this parent complaint?
    if assigned_duplicate_id and parent_complaint:
        from datetime import datetime as dt
        existing_report = db.query(Complaint).filter(
            Complaint.citizen_id == current_user.id,
            Complaint.duplicate_of_complaint_id == assigned_duplicate_id,
        ).order_by(Complaint.created_at.desc()).first()

        if existing_report:
            time_diff = (dt.utcnow() - existing_report.created_at).total_seconds()
            if existing_report.description == translated_desc or existing_report.original_description == original_description or time_diff < 600:
                # Idempotent response: return existing child complaint without duplicate creation or impact inflation
                return serialize_complaint(existing_report, db)

    # ── 5. Compute SLA Deadline ───────────────────────────────────────────────
    from datetime import datetime
    sla_deadline = compute_sla_deadline(db, category.id, predicted_priority)

    # Status for child report should reflect parent's status (never silently Closed!)
    initial_status = parent_complaint.status if (assigned_duplicate_id and parent_complaint) else "Registered"

    # ── 6. Create Complaint DB record ─────────────────────────────────────────
    complaint = Complaint(
        citizen_id=current_user.id,
        category_id=category.id,
        description=translated_desc,
        original_description=original_description,
        language=language,
        detected_language=detected_lang,
        audio_url=audio_url,
        location_latitude=location_latitude,
        location_longitude=location_longitude,
        location_address=location_address,
        status=initial_status,
        priority=predicted_priority,
        duplicate_of_complaint_id=assigned_duplicate_id,
        impact_count=1,
        sla_deadline=sla_deadline,
        sla_status="Normal",
        is_escalated=False,
        reopen_count=0,
    )
    db.add(complaint)
    db.flush()

    # Status history entry
    if assigned_duplicate_id:
        db.add(ComplaintStatusHistory(
            complaint_id=complaint.id,
            status=initial_status,
            remarks=f"Report linked to existing Complaint #{assigned_duplicate_id}.",
            changed_by_user_id=current_user.id
        ))
    else:
        db.add(ComplaintStatusHistory(
            complaint_id=complaint.id,
            status="Registered",
            remarks="Complaint registered in system.",
            changed_by_user_id=current_user.id
        ))

    # AI Predictions record
    db.add(AIPrediction(
        complaint_id=complaint.id,
        predicted_category_id=category.id,
        category_confidence=cat_conf,
        predicted_priority=predicted_priority,
        priority_confidence=prio_conf,
        translation_time=trans_time,
        transcription_used=transcription_used,
    ))

    # ── 7. Handle Duplicate / Original paths ──────────────────────────────────
    if assigned_duplicate_id and parent_complaint:
        db.add(DuplicateComplaintMapping(
            original_complaint_id=assigned_duplicate_id,
            duplicate_complaint_id=complaint.id,
            similarity_score=duplicate_score or 0.90,
        ))
        
        # Increment parent's impact / citizen-report count
        parent_complaint.impact_count = (parent_complaint.impact_count or 1) + 1
        db.flush()

        db.add(Notification(
            user_id=current_user.id,
            complaint_id=complaint.id,
            message=f"Your report #{complaint.id} has been linked to Complaint #{assigned_duplicate_id}. Current status: {initial_status}.",
            notification_type="General",
        ))
    else:
        # Route to department officer only for unique/parent complaint
        assign_officer_to_complaint(db, complaint)

    # ── 8. Handle Image Upload & Multimodal Evidence Verification ─────────────
    image_path = None
    web_url = None
    if file:
        file_ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        web_url = f"/static/uploads/{unique_filename}"
        image_path = file_path

    # ── 9. Compute Hard-Gate Evidence Verification & Trust Score ──────────────
    from datetime import datetime
    evidence_data = compute_evidence_trust(
        live_lat=location_latitude,
        live_lon=location_longitude,
        image_path=image_path,
        category_name=predicted_cat_name,
        submission_timestamp=datetime.utcnow(),
        gps_accuracy=gps_accuracy,
        db=db,
        complaint_description=translated_desc,
    )

    if image_path:
        is_verified = (evidence_data["verification_decision"] in ["VERIFIED", "PARTIALLY_VERIFIED"])
        img_conf = evidence_data["semantic_confidence"]

        db_image = ComplaintImage(
            complaint_id=complaint.id,
            image_url=web_url,
            image_type="Reporting",
            is_verified=is_verified,
            confidence_score=img_conf,
            bounding_boxes=evidence_data.get("bounding_boxes"),
            quality_status=evidence_data.get("quality_check"),
            perceptual_hash=evidence_data.get("perceptual_hash"),
        )
        db.add(db_image)
        db.flush()

    ev_check = ComplaintEvidenceCheck(
        complaint_id=complaint.id,
        live_gps_provided=evidence_data["live_gps_provided"],
        exif_gps_found=evidence_data["exif_gps_found"],
        gps_distance_m=evidence_data["gps_distance_m"],
        gps_match=evidence_data["gps_match"],
        vision_objects_detected=evidence_data["vision_objects_detected"],
        vision_agreement_score=evidence_data["vision_agreement_score"],
        timestamp_valid=evidence_data["timestamp_valid"],
        trust_score=evidence_data["trust_score"],
        trust_level=evidence_data["trust_level"],
        verification_details=evidence_data["verification_details"],
        # Phase 8/9 hardening fields:
        verification_decision=evidence_data["verification_decision"],
        geo_status=evidence_data["geo_status"],
        gps_accuracy=evidence_data["gps_accuracy"],
        freshness_status=evidence_data["freshness_status"],
        semantic_match_status=evidence_data["semantic_match_status"],
        semantic_confidence=evidence_data["semantic_confidence"],
        image_category=evidence_data["image_category"],
        is_reused_image=evidence_data["is_reused_image"],
        reused_complaint_id=evidence_data["reused_complaint_id"],
        perceptual_hash=evidence_data["perceptual_hash"],
        quality_check=evidence_data["quality_check"],
        gate_reasons=evidence_data["gate_reasons"],
    )
    db.add(ev_check)

    db.commit()
    db.refresh(complaint)
    return serialize_complaint(complaint, db)


# ─────────────────────────────────────────────────────────────────────────────
# GET /complaints  — list (role-filtered)
# ─────────────────────────────────────────────────────────────────────────────
@router.get("", response_model=List[ComplaintResponse])
def get_complaints(
    status_filter: Optional[str] = None,
    category_id:   Optional[int] = None,
    priority:      Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Complaint)

    if current_user.role.name == "Citizen":
        query = query.filter(Complaint.citizen_id == current_user.id)
    elif current_user.role.name == "Officer":
        officer = db.query(Officer).filter(Officer.user_id == current_user.id).first()
        if not officer:
            raise HTTPException(status_code=400, detail="Officer profile not found")
        query = query.filter(Complaint.assigned_officer_id == officer.id)
    # Admin sees everything

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if category_id:
        query = query.filter(Complaint.category_id == category_id)
    if priority:
        query = query.filter(Complaint.priority == priority)

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return [serialize_complaint(c, db) for c in complaints]


# ─────────────────────────────────────────────────────────────────────────────
# GET /complaints/nearby
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/nearby", response_model=List[ComplaintResponse])
def get_nearby_complaints(
    latitude:      float,
    longitude:     float,
    radius_meters: float = 1000.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    delta = 0.01
    candidates = db.query(Complaint).filter(
        Complaint.location_latitude.between(latitude - delta, latitude + delta),
        Complaint.location_longitude.between(longitude - delta, longitude + delta)
    ).all()

    nearby = []
    for c in candidates:
        dist = haversine_distance(latitude, longitude, c.location_latitude, c.location_longitude)
        if dist <= radius_meters:
            nearby.append(serialize_complaint(c, db))
    return nearby


# ─────────────────────────────────────────────────────────────────────────────
# GET /complaints/{id}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id}", response_model=ComplaintResponse)
def get_complaint_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if current_user.role.name == "Citizen" and complaint.citizen_id != current_user.id:
        is_linked = db.query(Complaint).filter(
            Complaint.duplicate_of_complaint_id == complaint.id,
            Complaint.citizen_id == current_user.id
        ).first() is not None
        if not is_linked:
            raise HTTPException(status_code=403, detail="Not authorized to view this complaint")
    return serialize_complaint(complaint, db)


# ─────────────────────────────────────────────────────────────────────────────
# GET /complaints/{id}/evidence — Phase 9 Hard Gate & Evidence Check Details
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id}/evidence", response_model=EvidenceCheckResponse)
def get_complaint_evidence(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if current_user.role.name == "Citizen" and complaint.citizen_id != current_user.id:
        is_linked = db.query(Complaint).filter(
            Complaint.duplicate_of_complaint_id == complaint.id,
            Complaint.citizen_id == current_user.id
        ).first() is not None
        if not is_linked:
            raise HTTPException(status_code=403, detail="Not authorized to view this complaint")
    if not complaint.evidence_check:
        raise HTTPException(status_code=404, detail="Evidence check not found for this complaint")

    ev = complaint.evidence_check
    return {
        "verification_decision":    getattr(ev, "verification_decision", "VERIFIED") or "VERIFIED",
        "trust_score":              ev.trust_score,
        "trust_level":              ev.trust_level,
        "live_gps_provided":        ev.live_gps_provided,
        "exif_gps_found":           ev.exif_gps_found,
        "gps_distance_m":           ev.gps_distance_m,
        "gps_match":                ev.gps_match,
        "gps_accuracy":             getattr(ev, "gps_accuracy", None),
        "geo_status":               getattr(ev, "geo_status", "MATCH") or "MATCH",
        "timestamp_valid":          ev.timestamp_valid,
        "freshness_status":         getattr(ev, "freshness_status", "FRESH") or "FRESH",
        "vision_objects_detected":  ev.vision_objects_detected,
        "vision_agreement_score":   ev.vision_agreement_score,
        "semantic_match_status":    getattr(ev, "semantic_match_status", "MATCH") or "MATCH",
        "semantic_confidence":      getattr(ev, "semantic_confidence", 0.0) or 0.0,
        "image_category":           getattr(ev, "image_category", None),
        "is_reused_image":          getattr(ev, "is_reused_image", False) or False,
        "reused_complaint_id":      getattr(ev, "reused_complaint_id", None),
        "quality_check":            getattr(ev, "quality_check", None),
        "gate_reasons":             getattr(ev, "gate_reasons", None),
        "verification_details":     ev.verification_details,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUT /complaints/{id}/status  — officer status transitions
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/{id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    id: int,
    status_update: ComplaintStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_status = complaint.status
    new_status = status_update.status

    if current_user.role.name == "Citizen":
        if complaint.citizen_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if new_status != "Closed":
            raise HTTPException(status_code=400, detail="Citizens can only transition status to 'Closed'")

    elif current_user.role.name == "Officer":
        officer = db.query(Officer).filter(Officer.user_id == current_user.id).first()
        if not officer or complaint.assigned_officer_id != officer.id:
            raise HTTPException(status_code=403, detail="Unauthorized: Officer is not assigned to this complaint")

        valid_transitions = {
            "Registered":  ["Accepted", "Closed"],
            "Accepted":    ["In Progress", "Closed"],
            "In Progress": ["Resolved", "Closed"],
            "Reopened":    ["In Progress", "Resolved"],
            "Resolved":    [],
        }
        if new_status not in valid_transitions.get(old_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transition from '{old_status}' to '{new_status}'"
            )
        if new_status == "Resolved":
            raise HTTPException(
                status_code=400,
                detail="Use the /resolve endpoint which requires a resolution photo upload."
            )

    complaint.status = new_status
    db.add(ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=new_status,
        remarks=status_update.remarks or f"Status updated from {old_status} to {new_status}.",
        changed_by_user_id=current_user.id
    ))
    db.add(Notification(
        user_id=complaint.citizen_id,
        complaint_id=complaint.id,
        message=f"Your complaint #{complaint.id} status has changed to '{new_status}'.",
        notification_type="General",
    ))

    # Synchronize status to all linked child complaints
    duplicates = db.query(Complaint).filter(
        Complaint.duplicate_of_complaint_id == complaint.id
    ).all()
    for dup in duplicates:
        dup.status = new_status
        db.add(ComplaintStatusHistory(
            complaint_id=dup.id,
            status=new_status,
            remarks=status_update.remarks or f"Status updated to '{new_status}' via parent Complaint #{complaint.id}.",
            changed_by_user_id=current_user.id
        ))
        db.add(Notification(
            user_id=dup.citizen_id,
            complaint_id=dup.id,
            message=f"Update on your linked report #{dup.id}: Parent issue #{complaint.id} status is now '{new_status}'.",
            notification_type="General",
        ))
    db.commit()
    db.refresh(complaint)
    return serialize_complaint(complaint, db)


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints/{id}/resolve  — officer uploads resolution proof
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{id}/resolve", response_model=ComplaintResponse)
def resolve_complaint(
    id: int,
    remarks: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer)
):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    officer = db.query(Officer).filter(Officer.user_id == current_user.id).first()
    if not officer or complaint.assigned_officer_id != officer.id:
        raise HTTPException(status_code=403, detail="Unauthorized: You are not assigned to this complaint")

    # Save resolution image
    file_ext = os.path.splitext(file.filename or "resolution.jpg")[1] or ".jpg"
    unique_filename = f"resolution_{uuid.uuid4()}{file_ext}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    web_url = f"/static/uploads/{unique_filename}"
    is_verified, img_conf = verify_image(file_path, complaint.category.name)

    db.add(ComplaintImage(
        complaint_id=complaint.id,
        image_url=web_url,
        image_type="Resolution",
        is_verified=is_verified,
        confidence_score=img_conf,
    ))

    # Move to Resolved — awaiting citizen verification
    complaint.status = "Resolved"
    complaint.citizen_verified = None  # Reset: citizen hasn't verified yet

    db.add(ComplaintStatusHistory(
        complaint_id=complaint.id,
        status="Resolved",
        remarks=remarks,
        changed_by_user_id=current_user.id
    ))

    # Notify Citizen to verify resolution
    db.add(Notification(
        user_id=complaint.citizen_id,
        complaint_id=complaint.id,
        message=(
            f"Complaint #{complaint.id} has been marked Resolved by "
            f"Officer {current_user.name}. Please verify and either "
            f"Approve (to close) or Reject (to reopen) the resolution."
        ),
        notification_type="Resolution",
    ))

    # Auto-resolve duplicates
    duplicates = db.query(Complaint).filter(
        Complaint.duplicate_of_complaint_id == complaint.id
    ).all()
    for dup in duplicates:
        if dup.status != "Resolved":
            dup.status = "Resolved"
            db.add(ComplaintStatusHistory(
                complaint_id=dup.id,
                status="Resolved",
                remarks=f"Resolution submitted on parent Complaint #{complaint.id}.",
                changed_by_user_id=current_user.id
            ))
            db.add(Notification(
                user_id=dup.citizen_id,
                complaint_id=dup.id,
                message=(
                    f"The issue you reported (linked to Complaint #{complaint.id}) has been marked Resolved. "
                    f"Your report #{dup.id} is now Resolved."
                ),
                notification_type="Resolution",
            ))

    db.commit()
    db.refresh(complaint)
    return serialize_complaint(complaint, db)


# ─────────────────────────────────────────────────────────────────────────────
# POST /complaints/{id}/verify-resolution  — citizen approves or rejects resolution
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/{id}/verify-resolution", response_model=ComplaintResponse)
def citizen_verify_resolution(
    id: int,
    verify_in: CitizenVerifyResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_citizen)
):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to verify this complaint")

    if complaint.status != "Resolved":
        raise HTTPException(
            status_code=400,
            detail="Complaint must be in 'Resolved' status to verify."
        )

    complaint.citizen_verified = verify_in.approve
    complaint.citizen_feedback_rating = verify_in.feedback_rating
    complaint.citizen_feedback_remarks = verify_in.feedback_remarks

    if verify_in.approve:
        # ── Citizen APPROVES → Close complaint ────────────────────────────────
        complaint.status = "Closed"
        db.add(ComplaintStatusHistory(
            complaint_id=complaint.id,
            status="Closed",
            remarks=f"Citizen approved the resolution. Rating: {verify_in.feedback_rating}/5. "
                    f"Remarks: {verify_in.feedback_remarks or 'None'}",
            changed_by_user_id=current_user.id
        ))

        # Notify officer
        if complaint.assigned_officer_id:
            officer = db.query(Officer).filter(Officer.id == complaint.assigned_officer_id).first()
            if officer:
                officer_user = db.query(User).filter(User.id == officer.user_id).first()
                if officer_user:
                    db.add(Notification(
                        user_id=officer_user.id,
                        complaint_id=complaint.id,
                        message=(
                            f"✅ Citizen approved the resolution for Complaint #{complaint.id}. "
                            f"Rating: {verify_in.feedback_rating}/5. Complaint is now Closed."
                        ),
                        notification_type="General",
                    ))
    else:
        # ── Citizen REJECTS → Reopen complaint ────────────────────────────────
        complaint.status = "Reopened"
        complaint.reopen_count = (complaint.reopen_count or 0) + 1
        # Reset SLA deadline on reopen (give a fresh window)
        complaint.sla_deadline = compute_sla_deadline(db, complaint.category_id, complaint.priority)
        complaint.sla_status = "Normal"
        complaint.is_escalated = False

        remarks = (
            f"Citizen rejected resolution and reopened the complaint. "
            f"Citizen remarks: {verify_in.feedback_remarks or 'None'} "
            f"(Reopen count: {complaint.reopen_count})"
        )
        db.add(ComplaintStatusHistory(
            complaint_id=complaint.id,
            status="Reopened",
            remarks=remarks,
            changed_by_user_id=current_user.id
        ))

        # Notify officer to re-address
        if complaint.assigned_officer_id:
            officer = db.query(Officer).filter(Officer.id == complaint.assigned_officer_id).first()
            if officer:
                officer_user = db.query(User).filter(User.id == officer.user_id).first()
                if officer_user:
                    db.add(Notification(
                        user_id=officer_user.id,
                        complaint_id=complaint.id,
                        message=(
                            f"🔁 Complaint #{complaint.id} has been REOPENED by the citizen. "
                            f"Reason: {verify_in.feedback_remarks or 'Not satisfied with resolution'}. "
                            f"Please re-address and submit a new resolution."
                        ),
                        notification_type="Reopen",
                    ))

    # Synchronize resolution approval / reopen to linked duplicates
    duplicates = db.query(Complaint).filter(
        Complaint.duplicate_of_complaint_id == complaint.id
    ).all()
    for dup in duplicates:
        dup.status = complaint.status
        dup.citizen_verified = complaint.citizen_verified
        db.add(ComplaintStatusHistory(
            complaint_id=dup.id,
            status=complaint.status,
            remarks=f"Parent Complaint #{complaint.id} was {'closed after citizen verification approval' if verify_in.approve else 'reopened following citizen review'}.",
            changed_by_user_id=current_user.id
        ))
        db.add(Notification(
            user_id=dup.citizen_id,
            complaint_id=dup.id,
            message=(
                f"Parent Complaint #{complaint.id} (linked to your report #{dup.id}) "
                f"has been {'Closed' if verify_in.approve else 'Reopened for officer re-inspection'}."
            ),
            notification_type="General" if verify_in.approve else "Reopen",
        ))

    db.commit()
    db.refresh(complaint)
    return serialize_complaint(complaint, db)


# ─────────────────────────────────────────────────────────────────────────────
# GET /complaints/{id}/evidence  — inspect evidence trust breakdown
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/{id}/evidence")
def get_complaint_evidence(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if current_user.role.name == "Citizen" and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    ev = complaint.evidence_check
    if not ev:
        return {"message": "No evidence check record found for this complaint."}

    return {
        "complaint_id": id,
        "trust_score": ev.trust_score,
        "trust_level": ev.trust_level,
        "live_gps_provided": ev.live_gps_provided,
        "exif_gps_found": ev.exif_gps_found,
        "gps_distance_m": ev.gps_distance_m,
        "gps_match": ev.gps_match,
        "vision_agreement_score": ev.vision_agreement_score,
        "vision_objects_detected": ev.vision_objects_detected,
        "timestamp_valid": ev.timestamp_valid,
        "verification_details": ev.verification_details,
        "created_at": ev.created_at,
    }
