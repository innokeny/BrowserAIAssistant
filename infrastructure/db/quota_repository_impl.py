from infrastructure.db.db_connection import get_db_session, get_redis_client
from infrastructure.db.models import Quota as QuotaModel
from datetime import datetime, timedelta, timezone
import json
from typing import List, Optional, Dict, Any

class QuotaRepositoryImpl:
    def __init__(self):
        self.redis_client = get_redis_client()
    
    def get_user_quota(self, user_id: int, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user quotas, optionally filtered by resource type"""
        with get_db_session() as session:
            query = session.query(QuotaModel).filter(QuotaModel.user_id == user_id)
            
            if resource_type:
                query = query.filter(QuotaModel.resource_type == resource_type)
            
            quotas = query.all()
            
            return [
                {
                    "resource_type": q.resource_type,
                    "limit": q.limit,
                    "current_usage": q.current_usage,
                    "reset_date": q.reset_date.isoformat() if q.reset_date else None
                }
                for q in quotas
            ]
    
    def update_usage(self, user_id, resource_type, increment=1):
        """
        Increment the usage count for a user's quota.
        
        Args:
            user_id: ID of the user
            resource_type: Type of resource (e.g., "stt", "tts", "llm")
            increment: Amount to increment by (default: 1)
            
        Returns:
            Updated quota object or None if not found
        """
        with get_db_session() as session:
            db_quota = session.query(QuotaModel).filter(
                QuotaModel.user_id == user_id,
                QuotaModel.resource_type == resource_type
            ).first()
            
            if db_quota:
                # Check if quota has expired
                now = datetime.now(timezone.utc)
                if db_quota.reset_date and db_quota.reset_date.astimezone(timezone.utc) < now:
                    # Reset the quota
                    db_quota.current_usage = increment
                    # Set new reset date (e.g., next month)
                    db_quota.reset_date = now + timedelta(days=30)
                else:
                    # Increment usage
                    db_quota.current_usage += increment
                
                session.commit()
                session.refresh(db_quota)
                
                # Update Redis cache
                cache_key = f"quota:{user_id}:{resource_type}"
                quota_data = {
                    "id": db_quota.id,
                    "user_id": db_quota.user_id,
                    "resource_type": db_quota.resource_type,
                    "limit": db_quota.limit,
                    "current_usage": db_quota.current_usage,
                    "reset_date": db_quota.reset_date.astimezone(timezone.utc).isoformat() if db_quota.reset_date else None
                }
                
                self.redis_client.setex(
                    cache_key,
                    300,  # 5 minutes
                    json.dumps(quota_data)
                )
                
                return quota_data
            
            return None
    
    def create_quota(self, user_id, resource_type, limit, reset_date=None):
        """
        Create a new quota for a user.
        
        Args:
            user_id: ID of the user
            resource_type: Type of resource (e.g., "stt", "tts", "llm")
            limit: Maximum allowed usage
            reset_date: When the quota resets (default: 30 days from now)
            
        Returns:
            Created quota object
        """
        if reset_date is None:
            reset_date = datetime.now(timezone.utc) + timedelta(days=30)
        
        with get_db_session() as session:
            db_quota = QuotaModel(
                user_id=user_id,
                resource_type=resource_type,
                limit=limit,
                current_usage=0,
                reset_date=reset_date
            )
            
            session.add(db_quota)
            session.commit()
            session.refresh(db_quota)
            
            # Cache in Redis
            cache_key = f"quota:{user_id}:{resource_type}"
            quota_data = {
                "id": db_quota.id,
                "user_id": db_quota.user_id,
                "resource_type": db_quota.resource_type,
                "limit": db_quota.limit,
                "current_usage": db_quota.current_usage,
                "reset_date": db_quota.reset_date.astimezone(timezone.utc).isoformat() if db_quota.reset_date else None
            }
            
            self.redis_client.setex(
                cache_key,
                300,  # 5 minutes
                json.dumps(quota_data)
            )
            
            return quota_data

    def update_quota_usage(self, user_id: int, resource_type: str, usage: int) -> bool:
        """Update quota usage for a user"""
        with get_db_session() as session:
            quota = session.query(QuotaModel).filter(
                QuotaModel.user_id == user_id,
                QuotaModel.resource_type == resource_type
            ).first()
            
            if not quota:
                return False
            
            quota.current_usage = usage
            session.commit()
            return True

    def reset_quota(self, user_id: int, resource_type: str) -> bool:
        """Reset quota usage for a user"""
        with get_db_session() as session:
            quota = session.query(QuotaModel).filter(
                QuotaModel.user_id == user_id,
                QuotaModel.resource_type == resource_type
            ).first()
            
            if not quota:
                return False
            
            quota.current_usage = 0
            quota.reset_date = datetime.now()
            session.commit()
            return True 