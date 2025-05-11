# from infrastructure.db.db_connection import get_db_session, get_redis_client
# from infrastructure.db.models import Quota as QuotaModel
# from datetime import datetime, timedelta, timezone
# import json
# from typing import List, Optional, Dict, Any

# class QuotaRepositoryImpl:
#     def __init__(self):
#         self.redis_client = get_redis_client()
    
#     def get_user_quota(self, user_id: int, resource_type: str) -> Optional[Dict]:
#         cache_key = f"quota:{user_id}:{resource_type}"
#         cached_data = self.redis_client.get(cache_key)
        
#         if cached_data:
#             return json.loads(cached_data)
        
#         # Если нет в кэше - загружаем из БД
#         with get_db_session() as session:
#             quota = session.query(QuotaModel).filter(
#                 QuotaModel.user_id == user_id,
#                 QuotaModel.resource_type == resource_type
#             ).first()
            
#             if quota:
#                 quota_data = self._serialize_quota(quota)
#                 self.redis_client.setex(cache_key, 300, json.dumps(quota_data))
#                 return quota_data
                
#         return None
    
#     def update_usage(self, user_id, resource_type, increment=1):
#         cache_key = f"quota:{user_id}:{resource_type}"
#         try:
#             with get_db_session() as session:
#                 # 1. Обновляем БД
#                 quota = session.query(QuotaModel).filter(
#                     QuotaModel.user_id == user_id,
#                     QuotaModel.resource_type == resource_type
#                 ).with_for_update().first()  # Блокировка строки
                
#                 if not quota:
#                     raise ValueError("Quota not found")
                
#                 # Логика обновления
#                 if quota.reset_date < datetime.now():
#                     quota.current_usage = 0
#                     quota.reset_date = datetime.now() + timedelta(days=30)
                
#                 quota.current_usage += increment
                
#                 # 2. Обновляем Redis
#                 self.redis_client.setex(
#                     cache_key, 
#                     300,
#                     json.dumps(quota)
#                 )
                
#                 session.commit()
#                 return self._serialize_quota(quota)
                
#         except Exception as e:
#             session.rollback()
#             self.redis_client.delete(cache_key)  
#             raise
    
#     def create_quota(self, user_id, resource_type, limit, reset_date=None):
#         """
#         Create a new quota for a user.
        
#         Args:
#             user_id: ID of the user
#             resource_type: Type of resource (e.g., "stt", "tts", "llm")
#             limit: Maximum allowed usage
#             reset_date: When the quota resets (default: 30 days from now)
            
#         Returns:
#             Created quota object
#         """
#         if reset_date is None:
#             reset_date = datetime.now(timezone.utc) + timedelta(days=30)
        
#         with get_db_session() as session:
#             db_quota = QuotaModel(
#                 user_id=user_id,
#                 resource_type=resource_type,
#                 limit=limit,
#                 current_usage=0,
#                 reset_date=reset_date
#             )
            
#             session.add(db_quota)
#             session.commit()
#             session.refresh(db_quota)
            
#             # Cache in Redis
#             cache_key = f"quota:{user_id}:{resource_type}"
#             quota_data = {
#                 "id": db_quota.id,
#                 "user_id": db_quota.user_id,
#                 "resource_type": db_quota.resource_type,
#                 "limit": db_quota.limit,
#                 "current_usage": db_quota.current_usage,
#                 "reset_date": db_quota.reset_date.astimezone(timezone.utc).isoformat() if db_quota.reset_date else None
#             }
            
#             self.redis_client.setex(
#                 cache_key,
#                 300,  # 5 minutes
#                 json.dumps(quota_data)
#             )
            
#             return quota_data

#     def update_quota_usage(self, user_id: int, resource_type: str, usage: int) -> bool:
#         """Update quota usage for a user"""
#         with get_db_session() as session:
#             quota = session.query(QuotaModel).filter(
#                 QuotaModel.user_id == user_id,
#                 QuotaModel.resource_type == resource_type
#             ).first()
            
#             if not quota:
#                 return False
            
#             quota.current_usage = usage
#             session.commit()
#             return True

#     def reset_quota(self, user_id: int, resource_type: str) -> bool:
#         """Reset quota usage for a user"""
#         with get_db_session() as session:
#             quota = session.query(QuotaModel).filter(
#                 QuotaModel.user_id == user_id,
#                 QuotaModel.resource_type == resource_type
#             ).first()
            
#             if not quota:
#                 return False
            
#             quota.current_usage = 0
#             quota.reset_date = datetime.now()
#             session.commit()
#             return True 
        
#     def delete_quota(self, user_id, resource_type):
#         with get_db_session() as session:
#             try:
#                 # 1. Удаление из БД
#                 quota = session.query(QuotaModel).filter(
#                     QuotaModel.user_id == user_id,
#                     QuotaModel.resource_type == resource_type
#                 ).delete()
                
#                 # 2. Инвалидация кэша
#                 cache_key = f"quota:{user_id}:{resource_type}"
#                 self.redis_client.delete(cache_key)
                
#                 session.commit()
                
#             except Exception as e:
#                 session.rollback()
#                 raise