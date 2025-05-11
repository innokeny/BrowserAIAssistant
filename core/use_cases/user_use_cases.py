from core.entities.user import User


class UserUseCases:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register_user(self, name: str, email: str):
        """
        Register a new user and create default quotas.
        
        Args:
            name: User's name
            email: User's email
            
        Returns:
            User entity
        """
        user = User(id=None, name=name, email=email)
        saved_user = self.user_repository.save(user)
        
        return saved_user
    
    def get_user_by_id(self, user_id: int):
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User entity or None if not found
        """
        return self.user_repository.get_by_id(user_id)
    
    def get_user_by_email(self, email: str):
        """
        Get a user by email.
        
        Args:
            email: Email of the user
            
        Returns:
            User entity or None if not found
        """
        return self.user_repository.get_by_email(email)
    
    def update_user(self, user):
        """
        Update a user's profile.
        
        Args:
            user: User entity with updated information
            
        Returns:
            Updated user entity or None if update failed
        """
        return self.user_repository.save(user)
    
    def get_user_preferences(self, user_id: int):
        """
        Get user preferences.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User preferences or None if not found
        """
        return self.user_repository.get_preferences(user_id)
    
    def update_user_preferences(self, user_id: int, preferences):
        """
        Update user preferences.
        
        Args:
            user_id: ID of the user
            preferences: New preferences
            
        Returns:
            Updated preferences or None if failed
        """
        return self.user_repository.update_preferences(user_id, preferences)
    
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
        return self.request_history_repository.get_user_history(user_id, limit, offset)
