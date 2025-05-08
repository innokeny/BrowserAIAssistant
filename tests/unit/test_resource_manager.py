import sys
import os
import pytest
from datetime import datetime, timedelta
from sqlalchemy import text, func
from infrastructure.db.resource_manager import ResourceManager
from infrastructure.db.db_connection import get_db_session, engine
from infrastructure.db.models import User, UserCredits, Quota, RequestHistory, CreditTransaction

class TestResourceManager:
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
        
        # Create test user
        with get_db_session() as session:
            test_user = User(
                name="Test User",
                email="test@example.com",
                password_hash="hashed_password"
            )
            session.add(test_user)
            session.commit()
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
        
        self.resource_manager = ResourceManager()
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

    def test_create_default_quotas(self):
        """Test creating default quotas for a new user"""
        quotas = self.resource_manager.create_default_quotas(self.user_id)
        
        assert len(quotas) == 2
        assert any(q["resource_type"] == "scenario_basic" for q in quotas)
        assert any(q["resource_type"] == "scenario_llm" for q in quotas)
        
        # Verify quotas in database
        with get_db_session() as session:
            db_quotas = session.query(Quota).filter(
                Quota.user_id == self.user_id
            ).all()
            assert len(db_quotas) == 2

    def test_check_quota_with_sufficient_credits(self):
        """Test checking quota when user has sufficient credits"""
        # Create default quotas
        self.resource_manager.create_default_quotas(self.user_id)
        
        # Check quota for basic scenario
        has_quota, quota_data = self.resource_manager.check_quota(
            self.user_id,
            "scenario_basic"
        )
        assert has_quota
        assert quota_data is not None
        assert quota_data["resource_type"] == "scenario_basic"
        assert quota_data["current_usage"] == 0

    def test_check_quota_with_insufficient_credits(self):
        """Test checking quota when user has insufficient credits"""
        # Create default quotas
        self.resource_manager.create_default_quotas(self.user_id)
        
        # Spend all credits
        with get_db_session() as session:
            transaction = CreditTransaction(
                user_id=self.user_id,
                amount=-100,
                transaction_type="scenario_usage",
                scenario_type="test_scenario",
                description="Spend all credits"
            )
            session.add(transaction)
            session.commit()
        
        # Check quota
        has_quota, quota_data = self.resource_manager.check_quota(
            self.user_id,
            "scenario_basic"
        )
        assert not has_quota
        assert quota_data == {"error": "Insufficient credits"}

    def test_track_usage_success(self):
        """Test tracking successful resource usage"""
        # Create default quotas
        self.resource_manager.create_default_quotas(self.user_id)
        
        # Track usage
        request_history, quota_data = self.resource_manager.track_usage(
            user_id=self.user_id,
            resource_type="scenario_basic",
            request_data="Test request",
            response_data="Test response",
            processing_time=100
        )
        
        # Verify request history
        assert request_history is not None
        assert request_history["status"] == "success"
        assert request_history["processing_time"] == 100
        
        # Verify quota update
        assert quota_data is not None
        assert quota_data["current_usage"] == 1
        
        # Verify credit deduction
        with get_db_session() as session:
            balance = session.query(func.sum(CreditTransaction.amount))\
                .filter(CreditTransaction.user_id == self.user_id)\
                .scalar()
            assert balance == 99  # 100 - 1 credit for basic scenario

    def test_track_usage_failure(self):
        """Test tracking failed resource usage"""
        # Create default quotas
        self.resource_manager.create_default_quotas(self.user_id)
        
        # Track failed usage
        request_history, quota_data = self.resource_manager.track_usage(
            user_id=self.user_id,
            resource_type="scenario_basic",
            request_data="Test request",
            response_data=None,
            status="error",
            error_message="Test error",
            processing_time=100
        )
        
        # Verify request history
        assert request_history is not None
        assert request_history["status"] == "error"
        assert request_history["error_message"] == "Test error"
        
        # Verify no quota update
        assert quota_data is None
        
        # Verify no credit deduction
        with get_db_session() as session:
            balance = session.query(func.sum(CreditTransaction.amount))\
                .filter(CreditTransaction.user_id == self.user_id)\
                .scalar()
            assert balance == 100  # No credits spent 