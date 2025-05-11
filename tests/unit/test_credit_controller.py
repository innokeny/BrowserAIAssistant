import sys
import os
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from fastapi.testclient import TestClient
from infrastructure.web.app import app
from infrastructure.db.db_connection import get_db_session, engine, get_redis_client
from infrastructure.db.models import User, UserCredits, CreditTransaction
from infrastructure.web.auth_service import AuthService

client = TestClient(app)
auth_service = AuthService()

class TestCreditController:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database and create test user"""
        # Clean up database
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
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
            conn.execute(text("DELETE FROM credit_transactions"))
            conn.execute(text("DELETE FROM user_credits"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("SET session_replication_role = 'origin'"))
            conn.commit()
        redis_client.flushall()

    def test_get_credit_balance(self):
        """Test getting user credit balance"""
        response = client.get("/api/v1/credits/balance", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 100
        assert data["user_id"] == self.user_id

    def test_get_credit_balance_unauthorized(self):
        """Test getting credit balance without token"""
        response = client.get("/api/v1/credits/balance")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_credit_history(self):
        """Test getting user credit history"""
        response = client.get("/api/v1/credits/history", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1  # Only initial transaction
        assert data[0]["amount"] == 100
        assert data[0]["transaction_type"] == "initial"
        assert data[0]["description"] == "Initial credit balance"

    def test_get_credit_history_unauthorized(self):
        """Test getting credit history without token"""
        response = client.get("/api/v1/credits/history")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_add_credits_success(self):
        """Test adding credits successfully"""
        response = client.post(
            "/api/v1/credits/add",
            headers=self.headers,
            json={
                "amount": 50,
                "description": "Test credit addition"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 150  # 100 initial + 50 added
        
        # Verify transaction was created
        with get_db_session() as session:
            transaction = session.query(CreditTransaction)\
                .filter(CreditTransaction.user_id == self.user_id)\
                .order_by(CreditTransaction.created_at.desc())\
                .first()
            assert transaction is not None
            assert transaction.amount == 50
            assert transaction.transaction_type == "add"
            assert transaction.description == "Test credit addition"

    def test_add_credits_negative_amount(self):
        """Test adding negative credits"""
        response = client.post(
            "/api/v1/credits/add",
            headers=self.headers,
            json={
                "amount": -50,
                "description": "Test negative credit addition"
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Amount must be positive"

    def test_add_credits_unauthorized(self):
        """Test adding credits without token"""
        response = client.post(
            "/api/v1/credits/add",
            json={
                "amount": 50,
                "description": "Test credit addition"
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_deduct_credits_success(self):
        """Test deducting credits successfully"""
        response = client.post(
            "/api/v1/credits/deduct",
            headers=self.headers,
            json={
                "amount": 30,
                "description": "Test credit deduction"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 70  # 100 initial - 30 deducted
        
        # Verify transaction was created
        with get_db_session() as session:
            transaction = session.query(CreditTransaction)\
                .filter(CreditTransaction.user_id == self.user_id)\
                .order_by(CreditTransaction.created_at.desc())\
                .first()
            assert transaction is not None
            assert transaction.amount == -30  # Deductions are stored as negative amounts

    def test_deduct_credits_insufficient_balance(self):
        """Test deducting more credits than available"""
        response = client.post(
            "/api/v1/credits/deduct",
            headers=self.headers,
            json={
                "amount": 150,  # More than initial balance
                "description": "Test insufficient balance"
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Insufficient credit balance"

    def test_deduct_credits_negative_amount(self):
        """Test deducting negative credits"""
        response = client.post(
            "/api/v1/credits/deduct",
            headers=self.headers,
            json={
                "amount": -30,
                "description": "Test negative credit deduction"
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Amount must be positive"

    def test_deduct_credits_unauthorized(self):
        """Test deducting credits without token"""
        response = client.post(
            "/api/v1/credits/deduct",
            json={
                "amount": 30,
                "description": "Test credit deduction"
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated" 