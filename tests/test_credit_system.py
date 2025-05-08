import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.db.init_db import init_db
from infrastructure.db.db_connection import get_db_session
from infrastructure.db.models import User
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
from infrastructure.db.resource_manager import ResourceManager
from datetime import datetime

def test_credit_system():
    print("\n=== Testing Credit System ===")
    
    # Initialize database
    init_db()
    
    # Create test user
    with get_db_session() as session:
        test_user = User(
            name="Test User",
            email="test_credits@example.com",
            password_hash="hashed_password"
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        user_id = test_user.id
        print(f"\nCreated test user with ID: {user_id}")
    
    # Initialize repositories
    credit_repo = CreditRepositoryImpl()
    resource_manager = ResourceManager()
    
    # Test 1: Check initial balance
    initial_balance = credit_repo.get_user_balance(user_id)
    print(f"\nTest 1: Initial Balance")
    print(f"Initial balance: {initial_balance} credits")
    assert initial_balance == 100, "Initial balance should be 100 credits"
    
    # Test 2: Use basic scenario
    print(f"\nTest 2: Using Basic Scenario")
    has_quota, quota_data = resource_manager.check_quota(user_id, "scenario_basic")
    print(f"Has quota: {has_quota}")
    print(f"Quota data: {quota_data}")
    
    if has_quota:
        request_history, quota_data = resource_manager.track_usage(
            user_id=user_id,
            resource_type="scenario_basic",
            request_data="Test request",
            response_data="Test response"
        )
        print(f"Request tracked: {request_history is not None}")
    
    # Check balance after basic scenario
    balance_after_basic = credit_repo.get_user_balance(user_id)
    print(f"Balance after basic scenario: {balance_after_basic} credits")
    assert balance_after_basic == 99, "Balance should be 99 after using basic scenario"
    
    # Test 3: Use LLM scenario
    print(f"\nTest 3: Using LLM Scenario")
    has_quota, quota_data = resource_manager.check_quota(user_id, "scenario_llm")
    print(f"Has quota: {has_quota}")
    print(f"Quota data: {quota_data}")
    
    if has_quota:
        request_history, quota_data = resource_manager.track_usage(
            user_id=user_id,
            resource_type="scenario_llm",
            request_data="Test LLM request",
            response_data="Test LLM response"
        )
        print(f"Request tracked: {request_history is not None}")
    
    # Check balance after LLM scenario
    balance_after_llm = credit_repo.get_user_balance(user_id)
    print(f"Balance after LLM scenario: {balance_after_llm} credits")
    assert balance_after_llm == 97, "Balance should be 97 after using LLM scenario"
    
    # Test 4: Check transaction history
    print(f"\nTest 4: Transaction History")
    transactions = credit_repo.get_transaction_history(user_id)
    print("Transaction history:")
    for t in transactions:
        print(f"- {t['transaction_type']}: {t['amount']} credits ({t['description']})")
    
    assert len(transactions) == 3, "Should have 3 transactions (initial + basic + LLM)"
    
    print("\n=== All tests passed! ===")

if __name__ == "__main__":
    test_credit_system() 