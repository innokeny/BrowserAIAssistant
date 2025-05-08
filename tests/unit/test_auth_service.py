import sys
import os
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from infrastructure.web.auth_service import AuthService
from infrastructure.db.db_connection import get_db_session, engine, get_redis_client
from infrastructure.db.models import User, UserCredits, Quota, RequestHistory, CreditTransaction

class TestAuthService:
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
        
        self.auth_service = AuthService()
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

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password"
        hashed_password = self.auth_service.get_password_hash(password)
        
        # Verify hash is different from original password
        assert hashed_password != password
        
        # Verify password verification works
        assert self.auth_service.verify_password(password, hashed_password)
        assert not self.auth_service.verify_password("wrong_password", hashed_password)

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "test@example.com", "user_id": 1}
        token = self.auth_service.create_access_token(data)
        
        # Verify token is created
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token is stored in Redis
        assert self.auth_service.redis_client.exists(f"token:{token}")

    def test_register_user_success(self):
        """Test successful user registration"""
        name = "Test User"
        email = "test@example.com"
        password = "test_password"
        
        token_data, error = self.auth_service.register_user(name, email, password)
        
        # Verify registration was successful
        assert error is None
        assert token_data is not None
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Verify user was created in database
        with get_db_session() as session:
            user = session.query(User).filter(User.email == email).first()
            assert user is not None
            assert user.name == name
            assert user.password_hash is not None
            assert user.password_hash != password  # Password should be hashed
            
            # Verify default quotas were created
            quotas = session.query(Quota).filter(Quota.user_id == user.id).all()
            assert len(quotas) == 2
            assert any(q.resource_type == "scenario_basic" for q in quotas)
            assert any(q.resource_type == "scenario_llm" for q in quotas)

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email"""
        # Register first user
        name1 = "Test User 1"
        email = "test@example.com"
        password = "test_password"
        
        token_data1, error1 = self.auth_service.register_user(name1, email, password)
        assert error1 is None
        
        # Try to register second user with same email
        name2 = "Test User 2"
        token_data2, error2 = self.auth_service.register_user(name2, email, password)
        
        # Verify second registration failed
        assert error2 == "Email already registered"
        assert token_data2 is None

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Register user first
        name = "Test User"
        email = "test@example.com"
        password = "test_password"
        
        self.auth_service.register_user(name, email, password)
        
        # Try to authenticate
        token_data, error = self.auth_service.authenticate_user(email, password)
        
        # Verify authentication was successful
        assert error is None
        assert token_data is not None
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password"""
        # Register user first
        name = "Test User"
        email = "test@example.com"
        password = "test_password"
        
        self.auth_service.register_user(name, email, password)
        
        # Try to authenticate with wrong password
        token_data, error = self.auth_service.authenticate_user(email, "wrong_password")
        
        # Verify authentication failed
        assert error == "Incorrect password"
        assert token_data is None

    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        token_data, error = self.auth_service.authenticate_user("nonexistent@example.com", "password")
        
        # Verify authentication failed
        assert error == "User not found"
        assert token_data is None

    def test_validate_token_success(self):
        """Test successful token validation"""
        # Register user first
        name = "Test User"
        email = "test@example.com"
        password = "test_password"
        
        token_data, _ = self.auth_service.register_user(name, email, password)
        token = token_data["access_token"]
        
        # Validate token
        user, error = self.auth_service.validate_token(token)
        
        # Verify validation was successful
        assert error is None
        assert user is not None
        assert user.email == email
        assert user.name == name

    def test_validate_token_invalid(self):
        """Test validation of invalid token"""
        user, error = self.auth_service.validate_token("invalid_token")
        
        # Verify validation failed
        assert error == "Invalid token"
        assert user is None

    def test_validate_token_expired(self):
        """Test validation of expired token"""
        # Create token with short expiration
        data = {"sub": "test@example.com", "user_id": 1}
        token = self.auth_service.create_access_token(data, timedelta(seconds=1))
        
        # Wait for token to expire
        import time
        time.sleep(2)
        
        # Try to validate expired token
        user, error = self.auth_service.validate_token(token)
        
        # Verify validation failed
        assert error == "Token has expired"
        assert user is None 