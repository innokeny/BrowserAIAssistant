from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List
from core.use_cases.user_use_cases import UserUseCases
from infrastructure.db.user_repository_impl import UserRepositoryImpl
from infrastructure.db.request_history_repository_impl import RequestHistoryRepositoryImpl
from infrastructure.web.auth_service import AuthService
from core.entities.user import User
from infrastructure.web.schemas.user_schema import (
    UserCreate,
    UserRegistration,
    UserLogin,
    UserResponse,
    TokenResponse,
    QuotaResponse,
    RequestHistoryResponse
)
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl


credit_repository = CreditRepositoryImpl()


router = APIRouter(prefix="/api", tags=["users"])
user_repository = UserRepositoryImpl()
request_history_repository = RequestHistoryRepositoryImpl()
user_use_cases = UserUseCases(user_repository)
auth_service = AuthService()

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
    """Register a new user with authentication, quotas and initial credits"""
    try:
        # Создание пользователя
        token_data, error = auth_service.register_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password
        )
        
        if error:
            raise HTTPException(status_code=400, detail=error)

        # Получение пользователя через репозиторий
        user = user_repository.get_by_email(user_data.email)
        if not user:
            raise HTTPException(status_code=500, detail="User creation failed")

        # Создание квот
        user_use_cases.register_user(user.name, user.email)
        
        # Добавление кредитов через use case
        success, result = credit_repository.add_credits(
            user_id=user.id,
            amount=100,
            transaction_type="initial",
            description="Initial registration credits"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=result)

        return token_data
        
    except HTTPException as he:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

# @router.get("/users/me/preferences", response_model=UserPreferences)
# async def get_user_preferences(current_user: User = Depends(get_current_user)):
#     """
#     Get user preferences.
#     """
#     preferences = user_use_cases.get_user_preferences(current_user.id)
#     if not preferences:
#         # Return default preferences
#         return UserPreferences()
#     return preferences

# @router.put("/users/me/preferences", response_model=UserPreferences)
# async def update_user_preferences(
#     preferences: UserPreferences,
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Update user preferences.
#     """
#     updated_preferences = user_use_cases.update_user_preferences(current_user.id, preferences)
#     if not updated_preferences:
#         raise HTTPException(status_code=400, detail="Failed to update preferences")
#     return updated_preferences

# Existing User Routes
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
