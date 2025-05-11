from core.repositories.user_repository import UserRepository
from core.entities.user import User
from infrastructure.db.db_connection import get_db_session
from infrastructure.db.models import User as UserModel
from sqlalchemy.exc import IntegrityError

class UserRepositoryImpl(UserRepository):
    def save(self, user):
        """
        Save a user to the database.
        
        Args:
            user: User entity to save
            
        Returns:
            User entity with the ID from the database
        """
        with get_db_session() as session:
            try:
                # Check if user already exists
                if user.id:
                    db_user = session.query(UserModel).filter(UserModel.id == user.id).first()
                    if db_user:
                        db_user.name = user.name
                        db_user.email = user.email
                        db_user.password_hash = user.password_hash
                    else:
                        return None
                else:
                    # Create new user
                    db_user = UserModel(
                        name=user.name,
                        email=user.email,
                        password_hash=user.password_hash,
                        user_role=user.user_role  # Добавлено поле user_role
                    )
                    session.add(db_user)
                
                session.commit()
                session.refresh(db_user)
                
                # Convert to domain entity
                return User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email,
                    password_hash=db_user.password_hash,
                    user_role=db_user.user_role  # Добавлено поле user_role
                )
            except IntegrityError:
                session.rollback()
                # Handle unique constraint violation (e.g., duplicate email)
                return None
    
    def get_by_id(self, user_id):
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            User entity or None if not found
        """
        with get_db_session() as session:
            db_user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if db_user:
                return User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email,
                    password_hash=db_user.password_hash,
                    user_role=db_user.user_role  # Добавлено поле user_role
                )
            return None
    
    def get_by_email(self, email):
        """
        Get a user by email.
        
        Args:
            email: Email of the user to retrieve
            
        Returns:
            User entity or None if not found
        """
        with get_db_session() as session:
            db_user = session.query(UserModel).filter(UserModel.email == email).first()
            if db_user:
                return User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email,
                    password_hash=db_user.password_hash,
                    user_role=db_user.user_role  # Добавлено поле user_role
                )
            return None

    # def get_preferences(self, user_id):
    #     """
    #     Get user preferences.
        
    #     Args:
    #         user_id: ID of the user
            
    #     Returns:
    #         User preferences or None if not found
    #     """
    #     with get_db_session() as session:
    #         db_preferences = session.query(UserPreferencesModel).filter(
    #             UserPreferencesModel.user_id == user_id
    #         ).first()
            
    #         if db_preferences:
    #             return {
    #                 "theme": db_preferences.theme,
    #                 "language": db_preferences.language
    #             }
    #         return None
    
    # def update_preferences(self, user_id, preferences):
    #     """
    #     Update user preferences.
        
    #     Args:
    #         user_id: ID of the user
    #         preferences: New preferences
            
    #     Returns:
    #         Updated preferences or None if failed
    #     """
    #     with get_db_session() as session:
    #         try:
    #             db_preferences = session.query(UserPreferencesModel).filter(
    #                 UserPreferencesModel.user_id == user_id
    #             ).first()
                
    #             if db_preferences:
    #                 # Update existing preferences
    #                 db_preferences.theme = preferences.theme
    #                 db_preferences.language = preferences.language
    #             else:
    #                 # Create new preferences
    #                 db_preferences = UserPreferencesModel(
    #                     user_id=user_id,
    #                     theme=preferences.theme,
    #                     language=preferences.language
    #                 )
    #                 session.add(db_preferences)
                
    #             session.commit()
    #             session.refresh(db_preferences)
                
    #             return {
    #                 "theme": db_preferences.theme,
    #                 "language": db_preferences.language
    #             }
    #         except IntegrityError:
    #             session.rollback()
    #         return None
