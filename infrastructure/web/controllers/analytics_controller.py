from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
from infrastructure.web.auth_service import AuthService

router = APIRouter()
credit_repository = CreditRepositoryImpl()
auth_service = AuthService()

class ScenarioUsageStats(BaseModel):
    scenario_type: str
    total_usage: int
    credit_cost: int
    usage_count: int

class PeriodStats(BaseModel):
    period: str
    total_spent: int
    scenario_breakdown: List[ScenarioUsageStats]

@router.get("/analytics/scenario-usage", response_model=List[ScenarioUsageStats])
async def get_scenario_usage_stats(
    user_id: int = Depends(auth_service.get_current_user_id),
    days: int = Query(30, ge=1, le=365)
):
    """Get usage statistics by scenario type for the specified period"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return credit_repository.get_scenario_usage_stats(user_id, start_date, end_date)

@router.get("/analytics/period-stats", response_model=List[PeriodStats])
async def get_period_stats(
    user_id: int = Depends(auth_service.get_current_user_id),
    period: str = Query("month", regex="^(day|week|month|year)$")
):
    """Get usage statistics broken down by time periods"""
    return credit_repository.get_period_stats(user_id, period) 