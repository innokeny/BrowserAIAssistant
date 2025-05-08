from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from core.use_cases.user_use_cases import UserUseCases
from infrastructure.db.user_repository_impl import UserRepositoryImpl
from infrastructure.db.request_history_repository_impl import RequestHistoryRepositoryImpl
from infrastructure.web.auth_service import AuthService
from core.entities.user import User

router = APIRouter()
user_repository = UserRepositoryImpl()
request_history_repository = RequestHistoryRepositoryImpl()
user_use_cases = UserUseCases(user_repository)
auth_service = AuthService()

# User Models
class UserCreate(BaseModel):
    name: str
    email: str

class UserRegistration(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

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

class UserPreferences(BaseModel):
    theme: str = "light"
    language: str = "en"

# Authentication dependency
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    user, error = auth_service.validate_token(token)
    
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    return user

# Authentication Routes
@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegistration):
    """
    Register a new user with authentication.
    """
    token_data, error = auth_service.register_user(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return token_data

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """
    Authenticate a user and return access token.
    """
    token_data, error = auth_service.authenticate_user(
        email=user_data.email,
        password=user_data.password
    )
    
    if error:
        raise HTTPException(status_code=401, detail=error)
    
    return token_data

@router.get("/users/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }

@router.get("/users/me/preferences", response_model=UserPreferences)
async def get_user_preferences(current_user: User = Depends(get_current_user)):
    """
    Get user preferences.
    """
    preferences = user_use_cases.get_user_preferences(current_user.id)
    if not preferences:
        # Return default preferences
        return UserPreferences()
    return preferences

@router.put("/users/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_user)
):
    """
    Update user preferences.
    """
    updated_preferences = user_use_cases.update_user_preferences(current_user.id, preferences)
    if not updated_preferences:
        raise HTTPException(status_code=400, detail="Failed to update preferences")
    return updated_preferences

# Existing User Routes
@router.post("/users", response_model=UserResponse)
def register_user(user: UserCreate):
    """
    Register a new user (legacy endpoint).
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
    history = request_history_repository.get_user_history(
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    return history
