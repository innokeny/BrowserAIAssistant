from infrastructure.db.quota_repository_impl import QuotaRepositoryImpl
from infrastructure.db.request_history_repository_impl import RequestHistoryRepositoryImpl
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
import time

class ResourceManager:
    def __init__(self):
        self.quota_repository = QuotaRepositoryImpl()
        self.request_history_repository = RequestHistoryRepositoryImpl()
        self.credit_repository = CreditRepositoryImpl()
        
        # Define credit costs for different scenarios
        self.credit_costs = {
            'scenario_basic': 1,  # 1 credit per basic scenario usage
            'scenario_llm': 2,    # 2 credits per LLM scenario usage
        }
    
    def check_quota(self, user_id, resource_type):
        """
        Check if a user has quota available for a resource.
        
        Args:
            user_id: ID of the user
            resource_type: Type of resource (e.g., "scenario_basic", "scenario_llm")
            
        Returns:
            Tuple of (has_quota, quota_data)
        """
        # First check credit balance
        credit_balance = self.credit_repository.get_user_balance(user_id)
        required_credits = self.credit_costs.get(resource_type, 1)
        
        if credit_balance < required_credits:
            return False, {"error": "Insufficient credits"}
        
        # Then check quota
        quota_data = self.quota_repository.get_user_quota(user_id, resource_type)
        
        if not quota_data:
            # No quota found, assume unlimited
            return True, None
        
        # Check if quota has expired
        if quota_data["reset_date"]:
            reset_date = time.mktime(time.strptime(quota_data["reset_date"], "%Y-%m-%dT%H:%M:%S"))
            if time.time() > reset_date:
                # Quota has expired, reset it
                quota_data = self.quota_repository.update_usage(user_id, resource_type, 0)
                return True, quota_data
        
        # Check if user has quota available
        if quota_data["current_usage"] < quota_data["limit"]:
            return True, quota_data
        
        return False, quota_data
    
    def track_usage(self, user_id, resource_type, request_data=None, response_data=None, 
                   status="success", error_message=None, processing_time=None):
        """
        Track resource usage and save request history.
        
        Args:
            user_id: ID of the user
            resource_type: Type of resource (e.g., "scenario_basic", "scenario_llm")
            request_data: Input data (truncated if needed)
            response_data: Response data (truncated if needed)
            status: Status of the request (e.g., "success", "error")
            error_message: Error message if status is "error"
            processing_time: Processing time in milliseconds
            
        Returns:
            Tuple of (request_history, quota_data)
        """
        # Save request history
        request_history = self.request_history_repository.save_request(
            user_id=user_id,
            request_type=resource_type,
            request_data=request_data,
            response_data=response_data,
            status=status,
            error_message=error_message,
            processing_time=processing_time
        )
        
        # Update quota usage and spend credits if request was successful
        quota_data = None
        if status == "success":
            # Spend credits
            required_credits = self.credit_costs.get(resource_type, 1)
            success, result = self.credit_repository.spend_credits(
                user_id=user_id,
                amount=required_credits,
                scenario_type=resource_type,
                description=f"Used {resource_type} scenario"
            )
            
            if not success:
                return request_history, {"error": result}
            
            # Update quota
            quota_data = self.quota_repository.update_usage(user_id, resource_type)
        
        return request_history, quota_data
    
    def create_default_quotas(self, user_id):
        """
        Create default quotas for a new user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of created quota objects
        """
        default_quotas = [
            {"resource_type": "scenario_basic", "limit": 1000},
            {"resource_type": "scenario_llm", "limit": 500}
        ]
        
        created_quotas = []
        for quota in default_quotas:
            quota_data = self.quota_repository.create_quota(
                user_id=user_id,
                resource_type=quota["resource_type"],
                limit=quota["limit"]
            )
            created_quotas.append(quota_data)
        
        return created_quotas 