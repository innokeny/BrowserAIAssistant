from infrastructure.db.db_connection import get_db_session
from infrastructure.db.models import RequestHistory as RequestHistoryModel, CreditTransaction
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import func


class RequestHistoryRepositoryImpl:
    def save_request(self, user_id, request_type, request_data=None, response_data=None, 
                    status="success", error_message=None, processing_time=None):
        """
        Save a request to the history.
        
        Args:
            user_id: ID of the user
            request_type: Type of request (e.g., "stt", "tts", "llm")
            request_data: Input data (truncated if needed)
            response_data: Response data (truncated if needed)
            status: Status of the request (e.g., "success", "error")
            error_message: Error message if status is "error"
            processing_time: Processing time in milliseconds
            
        Returns:
            Created request history object
        """
        if request_data and len(request_data) > 1000:
            request_data = request_data[:997] + "..."
        
        if response_data and len(response_data) > 1000:
            response_data = response_data[:997] + "..."
        
        with get_db_session() as session:
            db_request = RequestHistoryModel(
                user_id=user_id,
                request_type=request_type,
                request_data=request_data,
                response_data=response_data,
                status=status,
                error_message=error_message,
                processing_time=processing_time,
                created_at=datetime.utcnow()
            )
            
            session.add(db_request)
            session.commit()
            session.refresh(db_request)
            
            return {
                "id": db_request.id,
                "user_id": db_request.user_id,
                "request_type": db_request.request_type,
                "status": db_request.status,
                "processing_time": db_request.processing_time,
                "created_at": db_request.created_at.isoformat() if db_request.created_at else None
            }
    
    def get_user_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        request_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get user request history with optional filters"""
        with get_db_session() as session:
            query = session.query(RequestHistoryModel).filter(RequestHistoryModel.user_id == user_id)
            
            if request_type:
                query = query.filter(RequestHistoryModel.request_type == request_type)
            if status:
                query = query.filter(RequestHistoryModel.status == status)
            if start_date:
                query = query.filter(RequestHistoryModel.created_at >= start_date)
            if end_date:
                query = query.filter(RequestHistoryModel.created_at <= end_date)
            
            history = query.order_by(RequestHistoryModel.created_at.desc()).offset(offset).limit(limit).all()
            
            return [
                {
                    "id": h.id,
                    "request_type": h.request_type,
                    "status": h.status,
                    "processing_time": h.processing_time,
                    "created_at": h.created_at.isoformat()
                }
                for h in history
            ]

    def get_usage_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        with get_db_session() as session:
            total_requests = session.query(func.count(RequestHistoryModel.id))\
                .filter(RequestHistoryModel.user_id == user_id).scalar()
            
            success_count = session.query(func.count(RequestHistoryModel.id))\
                .filter(RequestHistoryModel.user_id == user_id, RequestHistoryModel.status == "success").scalar()
            failed_count = total_requests - success_count
            success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
            
            avg_processing_time = session.query(func.avg(RequestHistoryModel.processing_time))\
                .filter(RequestHistoryModel.user_id == user_id).scalar() or 0
            
            requests_by_type = {}
            type_counts = session.query(
                RequestHistoryModel.request_type,
                func.count(RequestHistoryModel.id)
            ).filter(RequestHistoryModel.user_id == user_id)\
             .group_by(RequestHistoryModel.request_type).all()
            
            for request_type, count in type_counts:
                requests_by_type[request_type] = count
            
            return {
                "total_requests": total_requests,
                "successful_requests": success_count,
                "failed_requests": failed_count,
                "success_rate": success_rate,
                "average_processing_time": avg_processing_time,
                "requests_by_type": requests_by_type
            }

    def get_credit_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get credit statistics for a user"""
        with get_db_session() as session:
            current_balance = session.query(func.sum(CreditTransaction.amount))\
                .filter(CreditTransaction.user_id == user_id).scalar() or 0
            
            earned = session.query(func.sum(CreditTransaction.amount))\
                .filter(CreditTransaction.user_id == user_id, CreditTransaction.amount > 0).scalar() or 0
            spent = abs(session.query(func.sum(CreditTransaction.amount))\
                .filter(CreditTransaction.user_id == user_id, CreditTransaction.amount < 0).scalar() or 0)
            
            transactions_by_type = {}
            type_counts = session.query(
                CreditTransaction.transaction_type,
                func.count(CreditTransaction.id)
            ).filter(CreditTransaction.user_id == user_id)\
             .group_by(CreditTransaction.transaction_type).all()
            
            for transaction_type, count in type_counts:
                transactions_by_type[transaction_type] = count
            
            return {
                "current_balance": current_balance,
                "total_earned": earned,
                "total_spent": spent,
                "transactions_by_type": transactions_by_type
            }
    
    def get_request_details(self, request_id):
        """
        Get details of a specific request.
        
        Args:
            request_id: ID of the request
            
        Returns:
            Request history object or None if not found
        """
        with get_db_session() as session:
            db_request = session.query(RequestHistoryModel).filter(
                RequestHistoryModel.id == request_id
            ).first()
            
            if db_request:
                return {
                    "id": db_request.id,
                    "user_id": db_request.user_id,
                    "request_type": db_request.request_type,
                    "request_data": db_request.request_data,
                    "response_data": db_request.response_data,
                    "status": db_request.status,
                    "error_message": db_request.error_message,
                    "processing_time": db_request.processing_time,
                    "created_at": db_request.created_at.isoformat() if db_request.created_at else None
                }
            
            return None 