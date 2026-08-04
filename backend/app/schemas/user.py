from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class RoleBase(BaseModel):
    name: str

class RoleResponse(RoleBase):
    id: int
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role_name: str  # Citizen, Officer, Admin
    department_id: Optional[int] = None  # Required if role is Officer

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfileEdit(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    role_id: int
    role: RoleResponse
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    name: str
    email: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

class OfficerResponse(BaseModel):
    id: int
    user_id: int
    user: UserBase
    department_id: int
    department_name: str
    status: str
    
    class Config:
        from_attributes = True
