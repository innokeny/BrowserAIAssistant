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
                    else:
                        return None
                else:
                    # Create new user
                    db_user = UserModel(
                        name=user.name,
                        email=user.email
                    )
                    session.add(db_user)
                
                session.commit()
                session.refresh(db_user)
                
                # Convert to domain entity
                return User(
                    id=db_user.id,
                    name=db_user.name,
                    email=db_user.email
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
                    email=db_user.email
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
                    email=db_user.email
                )
            return None
