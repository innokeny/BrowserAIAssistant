from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from core.repositories.request_history_repository_impl import RequestHistoryRepositoryImpl
from infrastructure.web.auth_service import get_current_user
from infrastructure.db.models import User


router = APIRouter(prefix="/api", tags=["analytics"])
request_history_repository = RequestHistoryRepositoryImpl()

class UsageStatistics(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_processing_time: float
    requests_by_type: Dict[str, int]

class CreditStatistics(BaseModel):
    current_balance: int
    total_earned: int
    total_spent: int
    transactions_by_type: Dict[str, int]

@router.get("/analytics/usage", response_model=UsageStatistics)
async def get_usage_statistics(current_user: User = Depends(get_current_user)):
    """Get usage statistics for the current user"""
    try:
        stats = request_history_repository.get_usage_statistics(current_user.id)
        return UsageStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/credits", response_model=CreditStatistics)
async def get_credit_statistics(current_user: User = Depends(get_current_user)):
    """Get credit statistics for the current user"""
    try:
        stats = request_history_repository.get_credit_statistics(current_user.id)
        return CreditStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/history")
async def get_request_history(
    request_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get request history for the current user with optional filters"""
    try:
        history = request_history_repository.get_user_history(
            user_id=current_user.id,
            request_type=request_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 