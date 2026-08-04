from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.core.config import settings
from backend.app.models.user import User, Role, Officer
from backend.app.models.department import Department
from backend.app.schemas.user import UserCreate, Token, UserResponse, ProfileEdit
from backend.app.routers.deps import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Get role
    role = db.query(Role).filter(Role.name == user_in.role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{user_in.role_name}' does not exist"
        )
        
    # Validation for Officer registration
    if user_in.role_name == "Officer":
        if not user_in.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department ID is required for registering an Officer"
            )
        dept = db.query(Department).filter(Department.id == user_in.department_id).first()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
            
    # Hash password
    hashed_password = get_password_hash(user_in.password)
    
    # Create user
    db_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hashed_password,
        role_id=role.id,
        phone=user_in.phone,
        status="Active"
    )
    db.add(db_user)
    db.flush()  # get db_user.id
    
    # If officer, create officer profile
    if user_in.role_name == "Officer":
        db_officer = Officer(
            user_id=db_user.id,
            department_id=user_in.department_id,
            status="On Duty"
        )
        db.add(db_officer)
        
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm uses form_data.username for email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif user.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    # Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.name,
        "user_id": user.id,
        "name": user.name,
        "email": user.email
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(profile: ProfileEdit, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if profile.name is not None:
        current_user.name = profile.name
    if profile.phone is not None:
        current_user.phone = profile.phone
    if profile.password is not None:
        current_user.hashed_password = get_password_hash(profile.password)
        
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
