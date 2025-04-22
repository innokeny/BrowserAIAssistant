from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from core.use_cases.user_use_cases import UserUseCases
from infrastructure.db.user_repository_impl import UserRepositoryImpl
from core.entities.user import User

router = APIRouter()
user_repository = UserRepositoryImpl()
user_use_cases = UserUseCases(user_repository)

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class QuotaResponse(BaseModel):
    resource_type: str
    limit: int
    current_usage: int
    reset_date: Optional[str]

class RequestHistoryResponse(BaseModel):
    id: int
    request_type: str
    status: str
    processing_time: Optional[int]
    created_at: str

@router.post("/users", response_model=UserResponse)
def register_user(user: UserCreate):
    """
    Register a new user.
    """
    saved_user = user_use_cases.register_user(user.name, user.email)
    if not saved_user:
        raise HTTPException(status_code=400, detail="Failed to register user. Email may already be in use.")
    return saved_user

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    """
    Get a user by ID.
    """
    user = user_use_cases.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/email/{email}", response_model=UserResponse)
def get_user_by_email(email: str):
    """
    Get a user by email.
    """
    user = user_use_cases.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users/{user_id}/quotas/{resource_type}", response_model=QuotaResponse)
def get_user_quota(user_id: int, resource_type: str):
    """
    Get a user's quota for a specific resource type.
    """
    has_quota, quota_data = user_use_cases.check_resource_quota(user_id, resource_type)
    if not quota_data:
        raise HTTPException(status_code=404, detail="Quota not found")
    return quota_data

@router.get("/users/{user_id}/history", response_model=List[RequestHistoryResponse])
def get_user_history(user_id: int, limit: int = 10, offset: int = 0):
    """
    Get a user's request history.
    """
    # This would be implemented in the user use cases
    # For now, we'll return an empty list
    return []
