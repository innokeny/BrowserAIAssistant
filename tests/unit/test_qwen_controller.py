import sys
import os
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from fastapi.testclient import TestClient
from infrastructure.web.app import app
from infrastructure.db.db_connection import get_db_session, engine, get_redis_client
from infrastructure.db.models import User, UserCredits, Quota, RequestHistory, CreditTransaction
from infrastructure.web.auth_service import AuthService
from core.entities.text import LLMResult, LLMInput

# Set environment variable to use local model
os.environ["QWEN_MODEL_PATH"] = "models/qwen"

client = TestClient(app)
auth_service = AuthService()

class TestQwenController:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database and create test user"""
        # Clean up database
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
            conn.execute(text("DELETE FROM request_history"))
            conn.execute(text("DELETE FROM quotas"))
            conn.execute(text("DELETE FROM user_credits"))
            conn.execute(text("DELETE FROM credit_transactions"))
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
            
            # Create quota for Qwen
            quota = Quota(
                user_id=self.user_id,
                resource_type="qwen",
                limit=1000,
                current_usage=0,
                reset_date=datetime.now(timezone.utc) + timedelta(days=30)
            )
            session.add(quota)
            
            session.commit()
        
        # Create test token with both sub and user_id claims
        self.token = auth_service.create_access_token({
            "sub": str(self.user_id),
            "user_id": self.user_id,
            "email": "test@example.com"
        })
        
        # Store token in Redis
        redis_client.setex(
            f"token:{self.token}",
            900,  # 15 minutes in seconds
            str(self.user_id)
        )
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        yield
        # Cleanup after tests
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
            conn.execute(text("DELETE FROM request_history"))
            conn.execute(text("DELETE FROM quotas"))
            conn.execute(text("DELETE FROM user_credits"))
            conn.execute(text("DELETE FROM credit_transactions"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("SET session_replication_role = 'origin'"))
            conn.commit()
        redis_client.flushall()

    @pytest.mark.asyncio
    @patch('infrastructure.ml_models.qwen.model.QwenModel.generate')
    async def test_generate_text_success(self, mock_generate):
        """Test successful text generation"""
        # Mock the generate method to return a successful result
        mock_generate.return_value = LLMResult(
            text="Test response",
            is_success=True,
            error_message=None
        )
        
        response = client.post(
            "/api/v1/qwen/generate",
            headers=self.headers,
            json={
                "prompt": "Test prompt",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert data["text"] == "Test response"
        
        # Verify request history was created
        with get_db_session() as session:
            history = session.query(RequestHistory)\
                .filter(RequestHistory.user_id == self.user_id)\
                .order_by(RequestHistory.created_at.desc())\
                .first()
            assert history is not None
            assert history.request_type == "qwen"
            assert history.status == "success"
            assert history.processing_time is not None

    def test_generate_text_insufficient_credits(self):
        """Test text generation with insufficient credits"""
        # Set user credits to 0
        with get_db_session() as session:
            # Update UserCredits balance
            user_credits = session.query(UserCredits).filter(UserCredits.user_id == self.user_id).first()
            user_credits.balance = 0
            
            # Create a transaction to set balance to 0
            transaction = CreditTransaction(
                user_id=self.user_id,
                amount=-100,  # Deduct all credits
                transaction_type="test",
                description="Setting balance to 0 for test"
            )
            session.add(transaction)
            session.commit()
        
        # Clear Redis cache
        redis_client = get_redis_client()
        redis_client.delete(f"credits:{self.user_id}")
        
        response = client.post(
            "/api/v1/qwen/generate",
            headers=self.headers,
            json={
                "prompt": "Test prompt",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Insufficient credits"

    def test_generate_text_quota_exceeded(self):
        """Test text generation with exceeded quota"""
        # Set quota usage to limit
        with get_db_session() as session:
            quota = session.query(Quota).filter(Quota.user_id == self.user_id).first()
            quota.current_usage = quota.limit
            session.commit()
        
        response = client.post(
            "/api/v1/qwen/generate",
            headers=self.headers,
            json={
                "prompt": "Test prompt",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Quota exceeded"

    def test_generate_text_invalid_parameters(self):
        """Test text generation with invalid parameters"""
        response = client.post(
            "/api/v1/qwen/generate",
            headers=self.headers,
            json={
                "prompt": "",  # Empty prompt
                "max_tokens": 0,  # Invalid max_tokens
                "temperature": 2.0  # Invalid temperature
            }
        )
        
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_generate_text_unauthorized(self):
        """Test text generation without token"""
        response = client.post(
            "/api/v1/qwen/generate",
            json={
                "prompt": "Test prompt",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    @patch('infrastructure.ml_models.qwen.model.QwenModel.generate_stream')
    async def test_generate_text_with_streaming(self, mock_generate_stream):
        """Test text generation with streaming enabled"""
        # Mock the generate_stream method to return a successful result
        mock_generate_stream.return_value = AsyncMock()
        mock_generate_stream.return_value.__aiter__.return_value = [
            LLMResult(
                text="Test response",
                is_success=True,
                error_message=None
            )
        ]
        
        response = client.post(
            "/api/v1/qwen/generate/stream",
            headers=self.headers,
            json={
                "prompt": "Test prompt",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify request history was created
        with get_db_session() as session:
            history = session.query(RequestHistory)\
                .filter(RequestHistory.user_id == self.user_id)\
                .order_by(RequestHistory.created_at.desc())\
                .first()
            assert history is not None
            assert history.request_type == "qwen"
            assert history.status == "success"
            assert history.processing_time is not None

    def test_generate_text_with_streaming_unauthorized(self):
        """Test text generation with streaming without token"""
        response = client.post(
            "/api/v1/qwen/generate/stream",
            json={
                "prompt": "Test prompt",
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated" 