from core.entities.user import User
from infrastructure.db.resource_manager import ResourceManager

class UserUseCases:
    def __init__(self, user_repository):
        self.user_repository = user_repository
        self.resource_manager = ResourceManager()

    def register_user(self, name: str, email: str):
        """
        Register a new user and create default quotas.
        
        Args:
            name: User's name
            email: User's email
            
        Returns:
            User entity
        """
        # Create user
        user = User(id=None, name=name, email=email)
        saved_user = self.user_repository.save(user)
        
        if saved_user:
            # Create default quotas for the user
            self.resource_manager.create_default_quotas(saved_user.id)
        
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
    
    def check_resource_quota(self, user_id: int, resource_type: str):
        """
        Check if a user has quota available for a resource.
        
        Args:
            user_id: ID of the user
            resource_type: Type of resource (e.g., "stt", "tts", "llm")
            
        Returns:
            Tuple of (has_quota, quota_data)
        """
        return self.resource_manager.check_quota(user_id, resource_type)
    
    def track_resource_usage(self, user_id: int, resource_type: str, request_data=None, 
                           response_data=None, status="success", error_message=None, 
                           processing_time=None):
        """
        Track resource usage and save request history.
        
        Args:
            user_id: ID of the user
            resource_type: Type of resource (e.g., "stt", "tts", "llm")
            request_data: Input data (truncated if needed)
            response_data: Response data (truncated if needed)
            status: Status of the request (e.g., "success", "error")
            error_message: Error message if status is "error"
            processing_time: Processing time in milliseconds
            
        Returns:
            Tuple of (request_history, quota_data)
        """
        return self.resource_manager.track_usage(
            user_id=user_id,
            resource_type=resource_type,
            request_data=request_data,
            response_data=response_data,
            status=status,
            error_message=error_message,
            processing_time=processing_time
        )
