import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from infrastructure.web.app import app
from infrastructure.db.init_db import init_db
from infrastructure.db.db_connection import get_db_session, engine, get_redis_client
from infrastructure.db.models import User, CreditTransaction, UserCredits
from infrastructure.web.auth_service import AuthService
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
from infrastructure.db.resource_manager import ResourceManager
from datetime import datetime, timedelta
from sqlalchemy import text

client = TestClient(app)
auth_service = AuthService()

def test_billing_system():
    print("\n=== Testing Complete Billing System ===")
    
    # Clean up database and cache
    with engine.connect() as conn:
        # Disable foreign key checks temporarily
        conn.execute(text("SET session_replication_role = 'replica'"))
        
        # Delete all data from tables in correct order
        conn.execute(text("DELETE FROM credit_transactions"))
        conn.execute(text("DELETE FROM user_credits"))
        conn.execute(text("DELETE FROM user_preferences"))
        conn.execute(text("DELETE FROM request_history"))
        conn.execute(text("DELETE FROM quotas"))
        conn.execute(text("DELETE FROM users"))
        
        # Re-enable foreign key checks
        conn.execute(text("SET session_replication_role = 'origin'"))
        conn.commit()
    
    # Clear Redis cache
    redis_client = get_redis_client()
    redis_client.flushall()
    
    # Initialize database
    init_db()
    
    # Create test user
    with get_db_session() as session:
        test_user = User(
            name="Test User",
            email="test_billing@example.com",
            password_hash="hashed_password"
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        user_id = test_user.id
        print(f"\nCreated test user with ID: {user_id}")
        
        # Initialize user credits with zero balance
        user_credits = UserCredits(
            user_id=user_id,
            balance=0
        )
        session.add(user_credits)
        
        # Create initial transaction
        initial_transaction = CreditTransaction(
            user_id=user_id,
            amount=100,
            transaction_type="initial",
            description="Initial credit balance"
        )
        session.add(initial_transaction)
        session.commit()
    
    # Create test token
    token = auth_service.create_access_token({"sub": str(user_id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Initialize repositories
    credit_repo = CreditRepositoryImpl()
    resource_manager = ResourceManager()
    
    # Test 1: Initial Balance
    print("\nTest 1: Check Initial Balance")
    response = client.get("/api/v1/credits/balance", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["balance"] == 100
    
    # Test 2: Add Credits
    print("\nTest 2: Add Credits")
    response = client.post(
        "/api/v1/credits/add",
        headers=headers,
        json={
            "amount": 50,
            "transaction_type": "manual",
            "description": "Test credit addition"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["balance"] == 150
    
    # Test 3: Use Basic Scenario
    print("\nTest 3: Using Basic Scenario")
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
    
    # Test 4: Use LLM Scenario
    print("\nTest 4: Using LLM Scenario")
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
    
    # Test 5: Create Additional Usage Transactions
    print("\nTest 5: Create Additional Usage Transactions")
    scenarios = [
        ("search", 10, "Search scenario usage"),
        ("chat", 20, "Chat scenario usage"),
        ("navigation", 15, "Navigation scenario usage")
    ]
    
    for scenario_type, amount, description in scenarios:
        success, result = credit_repo.spend_credits(
            user_id=user_id,
            amount=amount,
            scenario_type=scenario_type,
            description=description
        )
        assert success, f"Failed to spend credits for {scenario_type}"
    
    # Test 6: Check Updated Balance
    print("\nTest 6: Check Updated Balance")
    response = client.get("/api/v1/credits/balance", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    # 150 - (1 for basic scenario) - (2 for LLM scenario) - (10 + 20 + 15 for additional transactions)
    assert response.json()["balance"] == 102
    
    # Test 7: Get Transaction History
    print("\nTest 7: Get Transaction History")
    response = client.get("/api/v1/credits/history", headers=headers)
    print(f"Status: {response.status_code}")
    print("Transactions:")
    for t in response.json():
        print(f"- {t['transaction_type']}: {t['amount']} credits ({t['description']})")
    assert response.status_code == 200
    assert len(response.json()) == 7  # Initial + manual + basic + LLM + 3 usage transactions
    
    # Test 8: Get Scenario Usage Stats
    print("\nTest 8: Get Scenario Usage Stats")
    response = client.get("/api/v1/analytics/scenario-usage", headers=headers)
    print(f"Status: {response.status_code}")
    print("Scenario Usage:")
    for stat in response.json():
        print(f"- {stat['scenario_type']}: {stat['total_usage']} credits, {stat['usage_count']} uses")
    assert response.status_code == 200
    assert len(response.json()) == 5  # Five different scenarios (basic, LLM, search, chat, navigation)
    
    # Test 9: Get Period Stats
    print("\nTest 9: Get Period Stats")
    response = client.get("/api/v1/analytics/period-stats?period=day", headers=headers)
    print(f"Status: {response.status_code}")
    print("Period Stats:")
    for stat in response.json():
        print(f"Period {stat['period']}: {stat['total_spent']} credits spent")
    assert response.status_code == 200
    
    print("\n=== All Billing System Tests Passed! ===")

if __name__ == "__main__":
    test_billing_system() 