import sys
import os
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from fastapi.testclient import TestClient
from infrastructure.web.app import app
from infrastructure.db.db_connection import get_db_session, engine, get_redis_client
from infrastructure.db.models import User, UserCredits, Quota, RequestHistory, CreditTransaction
from infrastructure.web.auth_service import AuthService

client = TestClient(app)
auth_service = AuthService()

class TestAnalyticsController:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database and create test user"""
        # Clean up database
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
            conn.execute(text("DELETE FROM request_history"))
            conn.execute(text("DELETE FROM quotas"))
            conn.execute(text("DELETE FROM credit_transactions"))
            conn.execute(text("DELETE FROM user_credits"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("SET session_replication_role = 'origin'"))
            conn.commit()
        
        # Clear Redis cache
        redis_client = get_redis_client()
        redis_client.flushall()
        
        # Create test user
        with get_db_session() as session:
            test_user = User(
                name="Test User",
                email="test@example.com",
                password_hash="hashed_password"
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)
            self.user_id = test_user.id
            
            # Initialize user credits
            user_credits = UserCredits(
                user_id=self.user_id,
                balance=100  # Start with 100 credits
            )
            session.add(user_credits)
            
            # Create initial transaction
            initial_transaction = CreditTransaction(
                user_id=self.user_id,
                amount=100,
                transaction_type="initial",
                description="Initial credit balance"
            )
            session.add(initial_transaction)
            
            # Create some request history
            now = datetime.now(timezone.utc)
            for i in range(3):
                history = RequestHistory(
                    user_id=self.user_id,
                    request_type="scenario_basic",
                    status="success",
                    processing_time=100 + i,
                    created_at=now - timedelta(hours=i)
                )
                session.add(history)
            
            # Create some quotas
            quota = Quota(
                user_id=self.user_id,
                resource_type="scenario_basic",
                limit=1000,
                current_usage=3,
                reset_date=now + timedelta(days=30)
            )
            session.add(quota)
            
            session.commit()
        
        # Create test token with both sub and user_id claims
        self.token = auth_service.create_access_token({
            "sub": str(self.user_id),
            "user_id": self.user_id,
            "email": "test@example.com"
        })
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        yield
        # Cleanup after tests
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
            conn.execute(text("DELETE FROM request_history"))
            conn.execute(text("DELETE FROM quotas"))
            conn.execute(text("DELETE FROM credit_transactions"))
            conn.execute(text("DELETE FROM user_credits"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("SET session_replication_role = 'origin'"))
            conn.commit()
        redis_client.flushall()

    def test_get_usage_statistics(self):
        """Test getting usage statistics"""
        response = client.get("/api/v1/analytics/usage", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "success_rate" in data
        assert "average_processing_time" in data
        assert "requests_by_type" in data
        
        assert data["total_requests"] == 3
        assert data["success_rate"] == 100.0
        assert data["average_processing_time"] == 101.0  # (100 + 101 + 102) / 3
        assert data["requests_by_type"]["scenario_basic"] == 3

    def test_get_usage_statistics_unauthorized(self):
        """Test getting usage statistics without token"""
        response = client.get("/api/v1/analytics/usage")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_credit_statistics(self):
        """Test getting credit statistics"""
        response = client.get("/api/v1/analytics/credits", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "current_balance" in data
        assert "total_earned" in data
        assert "total_spent" in data
        assert "transactions_by_type" in data
        
        assert data["current_balance"] == 100
        assert data["total_earned"] == 100
        assert data["total_spent"] == 0
        assert data["transactions_by_type"]["initial"] == 1

    def test_get_credit_statistics_unauthorized(self):
        """Test getting credit statistics without token"""
        response = client.get("/api/v1/analytics/credits")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_quota_statistics(self):
        """Test getting quota statistics"""
        response = client.get("/api/v1/analytics/quotas", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        
        quota = data[0]
        assert quota["resource_type"] == "scenario_basic"
        assert quota["limit"] == 1000
        assert quota["current_usage"] == 3
        assert quota["reset_date"] is not None

    def test_get_quota_statistics_unauthorized(self):
        """Test getting quota statistics without token"""
        response = client.get("/api/v1/analytics/quotas")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_request_history(self):
        """Test getting request history"""
        response = client.get("/api/v1/analytics/history", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verify history entries
        for i, entry in enumerate(data):
            assert entry["request_type"] == "scenario_basic"
            assert entry["status"] == "success"
            assert entry["processing_time"] == 100 + i
            assert entry["created_at"] is not None

    def test_get_request_history_unauthorized(self):
        """Test getting request history without token"""
        response = client.get("/api/v1/analytics/history")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_request_history_with_filters(self):
        """Test getting request history with filters"""
        response = client.get(
            "/api/v1/analytics/history",
            headers=self.headers,
            params={
                "request_type": "scenario_basic",
                "status": "success",
                "start_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                "end_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verify filtered history entries
        for i, entry in enumerate(data):
            assert entry["request_type"] == "scenario_basic"
            assert entry["status"] == "success"
            assert entry["processing_time"] == 100 + i
            assert entry["created_at"] is not None 