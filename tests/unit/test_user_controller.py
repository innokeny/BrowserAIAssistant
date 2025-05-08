import sys
import os
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from fastapi.testclient import TestClient
from infrastructure.web.app import app
from infrastructure.db.db_connection import get_db_session, engine, get_redis_client
from infrastructure.db.models import User, UserCredits, Quota, RequestHistory, CreditTransaction, UserPreferences
from infrastructure.web.auth_service import AuthService

client = TestClient(app)
auth_service = AuthService()

class TestUserController:
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
            conn.execute(text("DELETE FROM user_preferences"))
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
            
            # Create user preferences
            preferences = UserPreferences(
                user_id=self.user_id,
                theme="light",
                language="en"
            )
            session.add(preferences)
            
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
            conn.execute(text("DELETE FROM user_preferences"))
            conn.execute(text("SET session_replication_role = 'origin'"))
            conn.commit()
        redis_client.flushall()

    def test_register_user_success(self):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/register",
            json={
                "name": "New User",
                "email": "new@example.com",
                "password": "test_password"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify user was created
        with get_db_session() as session:
            user = session.query(User).filter(User.email == "new@example.com").first()
            assert user is not None
            assert user.name == "New User"
            assert user.password_hash is not None
            assert user.password_hash != "test_password"  # Password should be hashed

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/v1/register",
            json={
                "name": "Another User",
                "email": "test@example.com",  # Using existing email
                "password": "test_password"
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_login_success(self):
        """Test successful user login"""
        # First register a user
        client.post(
            "/api/v1/register",
            json={
                "name": "Login Test User",
                "email": "login@example.com",
                "password": "test_password"
            }
        )
        
        # Then try to login
        response = client.post(
            "/api/v1/login",
            json={
                "email": "login@example.com",
                "password": "test_password"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # First register a user
        client.post(
            "/api/v1/register",
            json={
                "name": "Login Test User",
                "email": "login@example.com",
                "password": "test_password"
            }
        )
        
        # Then try to login with wrong password
        response = client.post(
            "/api/v1/login",
            json={
                "email": "login@example.com",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect password"

    def test_get_current_user_profile(self):
        """Test getting current user profile"""
        response = client.get("/api/v1/users/me", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.user_id
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"

    def test_get_current_user_profile_unauthorized(self):
        """Test getting current user profile without token"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_get_user_preferences(self):
        """Test getting user preferences"""
        response = client.get("/api/v1/users/me/preferences", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "theme" in data
        assert "language" in data
        assert data["theme"] == "light"  # Default value
        assert data["language"] == "en"  # Default value

    def test_get_user_by_id(self):
        """Test getting user by ID"""
        response = client.get(f"/api/v1/users/{self.user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.user_id
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"

    def test_get_user_by_id_not_found(self):
        """Test getting non-existent user by ID"""
        response = client.get("/api/v1/users/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_get_user_by_email(self):
        """Test getting user by email"""
        response = client.get("/api/v1/users/email/test@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.user_id
        assert data["name"] == "Test User"
        assert data["email"] == "test@example.com"

    def test_get_user_by_email_not_found(self):
        """Test getting non-existent user by email"""
        response = client.get("/api/v1/users/email/nonexistent@example.com")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_get_user_quota(self):
        """Test getting user quota"""
        # Create quota first
        with get_db_session() as session:
            quota = Quota(
                user_id=self.user_id,
                resource_type="scenario_basic",
                limit=1000,
                current_usage=0,
                reset_date=datetime.now(timezone.utc) + timedelta(days=30)
            )
            session.add(quota)
            session.commit()
        
        response = client.get(f"/api/v1/users/{self.user_id}/quotas/scenario_basic")
        
        assert response.status_code == 200
        data = response.json()
        assert data["resource_type"] == "scenario_basic"
        assert data["limit"] == 1000
        assert data["current_usage"] == 0
        assert data["reset_date"] is not None

    def test_get_user_quota_not_found(self):
        """Test getting non-existent user quota"""
        response = client.get(f"/api/v1/users/{self.user_id}/quotas/nonexistent")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Quota not found"

    def test_get_user_history(self):
        """Test getting user request history"""
        # Create some request history
        with get_db_session() as session:
            history = RequestHistory(
                user_id=self.user_id,
                request_type="scenario_basic",
                status="success",
                processing_time=100,
                created_at=datetime.now(timezone.utc)
            )
            session.add(history)
            session.commit()
        
        response = client.get(f"/api/v1/users/{self.user_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["request_type"] == "scenario_basic"
        assert data[0]["status"] == "success"
        assert data[0]["processing_time"] == 100 