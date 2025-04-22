from infrastructure.db.db_connection import get_db_session
from infrastructure.db.models import RequestHistory as RequestHistoryModel
from datetime import datetime

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
        # Truncate data if needed
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
    
    def get_user_history(self, user_id, limit=10, offset=0):
        """
        Get a user's request history.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of request history objects
        """
        with get_db_session() as session:
            db_requests = session.query(RequestHistoryModel).filter(
                RequestHistoryModel.user_id == user_id
            ).order_by(
                RequestHistoryModel.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return [{
                "id": req.id,
                "user_id": req.user_id,
                "request_type": req.request_type,
                "status": req.status,
                "processing_time": req.processing_time,
                "created_at": req.created_at.isoformat() if req.created_at else None
            } for req in db_requests]
    
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