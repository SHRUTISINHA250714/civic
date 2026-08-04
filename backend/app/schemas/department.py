from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DepartmentBase(BaseModel):
    name: str
    code: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplaintCategoryBase(BaseModel):
    name: str
    department_id: int
    default_priority: str = "Medium"
    is_active: bool = True

class ComplaintCategoryCreate(ComplaintCategoryBase):
    pass

class ComplaintCategoryResponse(ComplaintCategoryBase):
    id: int
    department_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class RoutingRuleUpdate(BaseModel):
    department_id: int
    default_priority: Optional[str] = None
