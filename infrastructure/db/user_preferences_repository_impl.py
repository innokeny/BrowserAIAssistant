# from infrastructure.db.db_connection import get_db_session
# from infrastructure.db.models import UserPreferences as UserPreferencesModel
# from datetime import datetime

# class UserPreferencesRepositoryImpl:
#     def get_user_preferences(self, user_id):
#         """
#         Get user preferences.
        
#         Args:
#             user_id: ID of the user
            
#         Returns:
#             User preferences object or None if not found
#         """
#         with get_db_session() as session:
#             db_preferences = session.query(UserPreferencesModel).filter(
#                 UserPreferencesModel.user_id == user_id
#             ).first()
            
#             if db_preferences:
#                 return {
#                     "id": db_preferences.id,
#                     "user_id": db_preferences.user_id,
#                     "theme": db_preferences.theme,
#                     "language": db_preferences.language,
#                     "notifications_enabled": db_preferences.notifications_enabled,
#                     "created_at": db_preferences.created_at.isoformat() if db_preferences.created_at else None,
#                     "updated_at": db_preferences.updated_at.isoformat() if db_preferences.updated_at else None
#                 }
#             return None
    
#     def update_user_preferences(self, user_id, preferences_data):
#         """
#         Update user preferences.
        
#         Args:
#             user_id: ID of the user
#             preferences_data: Dictionary containing preference updates
            
#         Returns:
#             Updated user preferences object
#         """
#         with get_db_session() as session:
#             db_preferences = session.query(UserPreferencesModel).filter(
#                 UserPreferencesModel.user_id == user_id
#             ).first()
            
#             if not db_preferences:
#                 # Create new preferences if they don't exist
#                 db_preferences = UserPreferencesModel(
#                     user_id=user_id,
#                     theme=preferences_data.get("theme", "light"),
#                     language=preferences_data.get("language", "en"),
#                     notifications_enabled=preferences_data.get("notifications_enabled", True)
#                 )
#                 session.add(db_preferences)
#             else:
#                 # Update existing preferences
#                 if "theme" in preferences_data:
#                     db_preferences.theme = preferences_data["theme"]
#                 if "language" in preferences_data:
#                     db_preferences.language = preferences_data["language"]
#                 if "notifications_enabled" in preferences_data:
#                     db_preferences.notifications_enabled = preferences_data["notifications_enabled"]
            
#             session.commit()
#             session.refresh(db_preferences)
            
#             return {
#                 "id": db_preferences.id,
#                 "user_id": db_preferences.user_id,
#                 "theme": db_preferences.theme,
#                 "language": db_preferences.language,
#                 "notifications_enabled": db_preferences.notifications_enabled,
#                 "created_at": db_preferences.created_at.isoformat() if db_preferences.created_at else None,
#                 "updated_at": db_preferences.updated_at.isoformat() if db_preferences.updated_at else None
#             } 