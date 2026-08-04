import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User, Officer
from backend.app.models.complaint import (
    Complaint, ComplaintCategory, ComplaintImage,
    ComplaintStatusHistory, AIPrediction, DuplicateComplaintMapping, Notification
)
from backend.app.schemas.complaint import ComplaintResponse, DuplicateWarningResponse, ComplaintStatusUpdate
from backend.app.routers.deps import get_current_active_user, get_current_citizen, get_current_officer
from backend.app.services import (
    translate_text, classify_complaint, predict_priority,
    verify_image, check_duplicate_complaint, assign_officer_to_complaint
)
from backend.app.core.config import settings

router = APIRouter(prefix="/complaints", tags=["Complaints"])

@router.post("/check-duplicate", response_model=DuplicateWarningResponse)
def check_duplicate(
    latitude: float = Form(...),
    longitude: float = Form(...),
    description: str = Form(...),
    category_name: str = Form(...),
    db: Session = Depends(get_db)
):
    # Get category
    category = db.query(ComplaintCategory).filter(ComplaintCategory.name == category_name).first()
    if not category:
        return {
            "is_duplicate": False,
            "duplicate_of_id": None,
            "similarity_score": 0.0,
            "message": "Category not found."
        }
        
    # Translate text before similarity checking if it's in Kannada/Hinglish
    translated, _, _ = translate_text(description)
    
    is_dup, dup_id, score = check_duplicate_complaint(
        db, latitude, longitude, translated, category.id
    )
    
    if is_dup:
        return {
            "is_duplicate": True,
            "duplicate_of_id": dup_id,
            "similarity_score": round(score, 4),
            "message": "This issue has already been reported nearby. You can join the existing complaint instead."
        }
        
    return {
        "is_duplicate": False,
        "duplicate_of_id": None,
        "similarity_score": round(score, 4),
        "message": "No duplicate issues detected nearby."
    }

@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def raise_complaint(
    description: str = Form(...),
    language: str = Form("English"),
    location_latitude: float = Form(...),
    location_longitude: float = Form(...),
    location_address: Optional[str] = Form(None),
    duplicate_of_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_citizen)
):
    # 1. Translation and Language Detection
    translated_desc, detected_lang, trans_time = translate_text(description)
    
    # 2. AI Complaint Classification
    predicted_cat_name, cat_conf = classify_complaint(translated_desc)
    
    # Fetch predicted category
    category = db.query(ComplaintCategory).filter(ComplaintCategory.name == predicted_cat_name).first()
    if not category:
        # Fallback to Others
        category = db.query(ComplaintCategory).filter(ComplaintCategory.name == "Others").first()
        predicted_cat_name = "Others"
        cat_conf = 0.50
        
    # 3. AI Priority Prediction
    predicted_priority, prio_conf = predict_priority(translated_desc, predicted_cat_name)
    
    # 4. Check Duplicate (if not explicitly joined by frontend)
    assigned_duplicate_id = duplicate_of_id
    if not assigned_duplicate_id:
        is_dup, dup_id, score = check_duplicate_complaint(
            db, location_latitude, location_longitude, translated_desc, category.id
        )
        if is_dup:
            assigned_duplicate_id = dup_id
            
    # Create complaint
    complaint = Complaint(
        citizen_id=current_user.id,
        category_id=category.id,
        description=translated_desc,
        original_description=description,
        language=language,
        detected_language=detected_lang,
        location_latitude=location_latitude,
        location_longitude=location_longitude,
        location_address=location_address,
        status="Registered",
        priority=predicted_priority,
        duplicate_of_complaint_id=assigned_duplicate_id
    )
    db.add(complaint)
    db.flush()  # Generate complaint.id
    
    # Save Status History
    db.add(ComplaintStatusHistory(
        complaint_id=complaint.id,
        status="Registered",
        remarks="Complaint registered in system.",
        changed_by_user_id=current_user.id
    ))
    
    # Save AI Predictions record
    ai_pred = AIPrediction(
        complaint_id=complaint.id,
        predicted_category_id=category.id,
        category_confidence=cat_conf,
        predicted_priority=predicted_priority,
        priority_confidence=prio_conf,
        translation_time=trans_time
    )
    db.add(ai_pred)
    
    # Create duplicate mapping if applicable
    if assigned_duplicate_id:
        # User is joining an existing complaint
        db.add(DuplicateComplaintMapping(
            original_complaint_id=assigned_duplicate_id,
            duplicate_complaint_id=complaint.id,
            similarity_score=0.90  # Joined mapping
        ))
        complaint.status = "Closed"  # Auto-close the duplicate
        db.add(ComplaintStatusHistory(
            complaint_id=complaint.id,
            status="Closed",
            remarks=f"Citizen joined original complaint #{assigned_duplicate_id}.",
            changed_by_user_id=current_user.id
        ))
        
        # Notify citizen of joining
        db.add(Notification(
            user_id=current_user.id,
            complaint_id=complaint.id,
            message=f"You joined complaint #{assigned_duplicate_id} successfully. You will receive updates about this issue."
        ))
    else:
        # 5. Route Department & Assign Officer (Only for original complaints)
        assign_officer_to_complaint(db, complaint)
        
    # 6. Save Image (if uploaded)
    if file:
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        web_url = f"/static/uploads/{unique_filename}"
        
        # Verify image using YOLO
        is_verified, img_conf = verify_image(file_path, predicted_cat_name)
        
        db_image = ComplaintImage(
            complaint_id=complaint.id,
            image_url=web_url,
            image_type="Reporting",
            is_verified=is_verified,
            confidence_score=img_conf
        )
        db.add(db_image)
        db.flush()
        
    db.commit()
    db.refresh(complaint)
    
    # Populate extra response fields
    return serialize_complaint(complaint, db)

def serialize_complaint(c: Complaint, db: Session) -> dict:
    citizen_name = c.citizen.name
    category_name = c.category.name
    department_name = c.category.department.name
    department_id = c.category.department.id
    
    assigned_officer_name = None
    if c.assigned_officer:
        officer_user = db.query(User).filter(User.id == c.assigned_officer.user_id).first()
        if officer_user:
            assigned_officer_name = officer_user.name
            
    images_res = []
    for img in c.images:
        images_res.append({
            "id": img.id,
            "image_url": img.image_url,
            "image_type": img.image_type,
            "is_verified": img.is_verified,
            "confidence_score": img.confidence_score,
            "created_at": img.created_at
        })
        
    history_res = []
    for hist in c.status_history:
        history_res.append({
            "id": hist.id,
            "status": hist.status,
            "remarks": hist.remarks,
            "changed_by_name": hist.changed_by_user.name,
            "created_at": hist.created_at
        })
        
    ai_pred_res = None
    if c.ai_prediction:
        ai_pred_res = {
            "id": c.ai_prediction.id,
            "predicted_category_name": c.ai_prediction.predicted_category.name,
            "category_confidence": c.ai_prediction.category_confidence,
            "predicted_priority": c.ai_prediction.predicted_priority,
            "priority_confidence": c.ai_prediction.priority_confidence,
            "translation_time": c.ai_prediction.translation_time,
            "created_at": c.ai_prediction.created_at
        }
        
    return {
        "id": c.id,
        "citizen_id": c.citizen_id,
        "citizen_name": citizen_name,
        "category_id": c.category_id,
        "category_name": category_name,
        "department_id": department_id,
        "department_name": department_name,
        "description": c.description,
        "original_description": c.original_description,
        "language": c.language,
        "detected_language": c.detected_language,
        "location_latitude": c.location_latitude,
        "location_longitude": c.location_longitude,
        "location_address": c.location_address,
        "status": c.status,
        "priority": c.priority,
        "assigned_officer_id": c.assigned_officer_id,
        "assigned_officer_name": assigned_officer_name,
        "duplicate_of_complaint_id": c.duplicate_of_complaint_id,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
        "images": images_res,
        "status_history": history_res,
        "ai_prediction": ai_pred_res
    }

@router.get("", response_model=List[ComplaintResponse])
def get_complaints(
    status_filter: Optional[str] = None,
    category_id: Optional[int] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Complaint)
    
    # Role-based filtering
    if current_user.role.name == "Citizen":
        query = query.filter(Complaint.citizen_id == current_user.id)
    elif current_user.role.name == "Officer":
        # Get officer profile
        officer = db.query(Officer).filter(Officer.user_id == current_user.id).first()
        if not officer:
            raise HTTPException(status_code=400, detail="Officer profile not found")
        query = query.filter(Complaint.assigned_officer_id == officer.id)
    # Admin sees everything
    
    # Filter applications
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if category_id:
        query = query.filter(Complaint.category_id == category_id)
    if priority:
        query = query.filter(Complaint.priority == priority)
        
    complaints = query.order_by(Complaint.created_at.desc()).all()
    
    return [serialize_complaint(c, db) for c in complaints]

@router.get("/nearby", response_model=List[ComplaintResponse])
def get_nearby_complaints(
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,  # 1km default
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Fetch active/resolved complaints within a bounding box (1km is approx 0.01 degrees)
    delta = 0.01
    candidates = db.query(Complaint).filter(
        Complaint.location_latitude.between(latitude - delta, latitude + delta),
        Complaint.location_longitude.between(longitude - delta, longitude + delta)
    ).all()
    
    nearby_list = []
    for c in candidates:
        dist = haversine_distance(latitude, longitude, c.location_latitude, c.location_longitude)
        if dist <= radius_meters:
            nearby_list.append(serialize_complaint(c, db))
            
    return nearby_list

@router.get("/{id}", response_model=ComplaintResponse)
def get_complaint_by_id(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    # Check access permission
    if current_user.role.name == "Citizen" and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this complaint")
        
    return serialize_complaint(complaint, db)

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
    
    # Access controls for status transitions
    if current_user.role.name == "Citizen":
        # Citizens can only close resolved/in progress complaints
        if complaint.citizen_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if new_status != "Closed":
            raise HTTPException(status_code=400, detail="Citizens can only transition status to 'Closed'")
            
    elif current_user.role.name == "Officer":
        officer = db.query(Officer).filter(Officer.user_id == current_user.id).first()
        if not officer or complaint.assigned_officer_id != officer.id:
            raise HTTPException(status_code=403, detail="Unauthorized: Officer is not assigned to this complaint")
            
        valid_officer_transitions = {
            "Registered": ["Accepted", "Closed"],
            "Accepted": ["In Progress", "Closed"],
            "In Progress": ["Resolved", "Closed"],
            "Resolved": []
        }
        
        if new_status not in valid_officer_transitions.get(old_status, []):
            raise HTTPException(status_code=400, detail=f"Invalid status transition from {old_status} to {new_status}")
            
        # Resolved requires resolution image, which is handled via a separate upload endpoint
        if new_status == "Resolved":
            raise HTTPException(
                status_code=400,
                detail="Resolving a complaint requires uploading a resolution image. Use the resolve endpoint."
            )
            
    complaint.status = new_status
    db.add(ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=new_status,
        remarks=status_update.remarks or f"Status updated from {old_status} to {new_status}.",
        changed_by_user_id=current_user.id
    ))
    
    # Notify Citizen of update
    db.add(Notification(
        user_id=complaint.citizen_id,
        complaint_id=complaint.id,
        message=f"Your complaint #{complaint.id} status has changed to '{new_status}'."
    ))
    
    db.commit()
    db.refresh(complaint)
    return serialize_complaint(complaint, db)

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
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"resolution_{uuid.uuid4()}{file_extension}"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    web_url = f"/static/uploads/{unique_filename}"
    
    # Image verification for resolution
    is_verified, img_conf = verify_image(file_path, complaint.category.name)
    
    db_image = ComplaintImage(
        complaint_id=complaint.id,
        image_url=web_url,
        image_type="Resolution",
        is_verified=is_verified,
        confidence_score=img_conf
    )
    db.add(db_image)
    
    # Transition status to Resolved
    complaint.status = "Resolved"
    
    db.add(ComplaintStatusHistory(
        complaint_id=complaint.id,
        status="Resolved",
        remarks=remarks,
        changed_by_user_id=current_user.id
    ))
    
    # Notify Citizen
    db.add(Notification(
        user_id=complaint.citizen_id,
        complaint_id=complaint.id,
        message=f"Great news! Your complaint #{complaint.id} has been marked as Resolved by Officer {current_user.name}. Please verify and close it."
    ))
    
    # Auto-resolve duplicates associated with this original complaint!
    duplicates = db.query(Complaint).filter(Complaint.duplicate_of_complaint_id == complaint.id).all()
    for dup in duplicates:
        if dup.status != "Closed":
            dup.status = "Resolved"
            db.add(ComplaintStatusHistory(
                complaint_id=dup.id,
                status="Resolved",
                remarks=f"Auto-resolved because the original complaint #{complaint.id} was resolved.",
                changed_by_user_id=current_user.id
            ))
            db.add(Notification(
                user_id=dup.citizen_id,
                complaint_id=dup.id,
                message=f"The issue you joined (Original Complaint #{complaint.id}) has been marked as Resolved. Your duplicate complaint #{dup.id} has also been resolved."
            ))
            
    db.commit()
    db.refresh(complaint)
    return serialize_complaint(complaint, db)
