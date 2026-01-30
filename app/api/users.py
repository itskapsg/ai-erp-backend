"""
Users API Management
Admin-only endpoints for managing system users.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.api.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """List all users (Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return [
        UserResponse(
            id=str(u.id),
            username=u.username,
            email=u.email,
            role=u.role.value,
            is_active=u.is_active
        ) for u in users
    ]

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)"""
    # Check if username or email exists
    if db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first():
        raise HTTPException(status_code=400, detail="Username or Email already exists")
    
    try:
        role_enum = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        role=role_enum
    )
    new_user.set_password(user_data.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email,
        role=new_user.role.value,
        is_active=new_user.is_active
    )
