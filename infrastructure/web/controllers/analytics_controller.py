from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from core.repositories.request_history_repository_impl import RequestHistoryRepositoryImpl
from infrastructure.web.auth_service import get_current_user
from infrastructure.db.models import User, RequestHistory, QwenHistory
from infrastructure.db.db_connection import get_db_session
from sqlalchemy.orm import joinedload


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

class RequestHistoryCreate(BaseModel):
    request_type: str
    request_data: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    processing_time: Optional[int] = None

class QwenHistoryCreate(BaseModel):
    prompt: str
    response: str
    tokens_used: int

class RequestHistoryResponse(BaseModel):
    id: int
    request_type: str
    request_data: Optional[str]
    status: str
    error_message: Optional[str]
    processing_time: Optional[int]
    created_at: str
    qwen_history: Optional[QwenHistoryCreate] = None

@router.post("/analytics/history")
async def create_request_history(
    request_data: RequestHistoryCreate,
    qwen_data: Optional[QwenHistoryCreate] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new request history entry with optional Qwen history"""
    try:
        with get_db_session() as session:
            # Create request history
            request = RequestHistory(
                user_id=current_user.id,
                request_type=request_data.request_type,
                request_data=request_data.request_data,
                status=request_data.status,
                error_message=request_data.error_message,
                processing_time=request_data.processing_time
            )
            session.add(request)
            session.flush()  # Get the request ID

            # If this is a Qwen request, create Qwen history
            if qwen_data and request_data.request_type == "Общение с ИИ":
                qwen_history = QwenHistory(
                    request_id=request.id,
                    user_id=current_user.id,
                    prompt=qwen_data.prompt,
                    response=qwen_data.response,
                    tokens_used=qwen_data.tokens_used
                )
                session.add(qwen_history)

            session.commit()
            session.refresh(request)

            # Prepare response
            response = {
                "id": request.id,
                "request_type": request.request_type,
                "request_data": request.request_data,
                "status": request.status,
                "error_message": request.error_message,
                "processing_time": request.processing_time,
                "created_at": request.created_at.isoformat()
            }

            if request.qwen_history:
                response["qwen_history"] = {
                    "prompt": request.qwen_history.prompt,
                    "response": request.qwen_history.response,
                    "tokens_used": request.qwen_history.tokens_used
                }

            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.get("/analytics/history", response_model=List[RequestHistoryResponse])
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
        with get_db_session() as session:
            query = session.query(RequestHistory)\
                .options(joinedload(RequestHistory.qwen_history))\
                .filter(RequestHistory.user_id == current_user.id)
            
            if request_type:
                query = query.filter(RequestHistory.request_type == request_type)
            if status:
                query = query.filter(RequestHistory.status == status)
            if start_date:
                query = query.filter(RequestHistory.created_at >= start_date)
            if end_date:
                query = query.filter(RequestHistory.created_at <= end_date)
            
            history = query.order_by(RequestHistory.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return [
                {
                    "id": h.id,
                    "request_type": h.request_type,
                    "request_data": h.request_data,
                    "status": h.status,
                    "error_message": h.error_message,
                    "processing_time": h.processing_time,
                    "created_at": h.created_at.isoformat(),
                    "qwen_history": {
                        "prompt": h.qwen_history.prompt,
                        "response": h.qwen_history.response,
                        "tokens_used": h.qwen_history.tokens_used
                    } if h.qwen_history else None
                }
                for h in history
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 