import sys
import os
import pytest
from datetime import datetime, timedelta
from sqlalchemy import text
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
from infrastructure.db.db_connection import get_db_session, engine
from infrastructure.db.models import User, UserCredits, CreditTransaction

class TestCreditRepository:
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
                balance=0
            )
            session.add(user_credits)
            session.commit()
        
        self.repository = CreditRepositoryImpl()
        yield
        # Cleanup after tests
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'replica'"))
            conn.execute(text("DELETE FROM credit_transactions"))
            conn.execute(text("DELETE FROM user_credits"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("SET session_replication_role = 'origin'"))
            conn.commit()

    def test_get_user_balance_initial(self):
        """Test getting initial user balance"""
        balance = self.repository.get_user_balance(self.user_id)
        assert balance == 0

    def test_add_credits(self):
        """Test adding credits to user balance"""
        # Add initial credits
        balance = self.repository.add_credits(
            user_id=self.user_id,
            amount=100,
            transaction_type="initial",
            description="Initial balance"
        )
        assert balance == 100

        # Add more credits
        balance = self.repository.add_credits(
            user_id=self.user_id,
            amount=50,
            transaction_type="manual",
            description="Manual addition"
        )
        assert balance == 150

    def test_spend_credits(self):
        """Test spending credits"""
        # First add some credits
        self.repository.add_credits(
            user_id=self.user_id,
            amount=100,
            transaction_type="initial",
            description="Initial balance"
        )

        # Try to spend credits
        success, result = self.repository.spend_credits(
            user_id=self.user_id,
            amount=50,
            scenario_type="test_scenario",
            description="Test spending"
        )
        assert success
        assert result == 50  # New balance

        # Try to spend more than available
        success, result = self.repository.spend_credits(
            user_id=self.user_id,
            amount=100,
            scenario_type="test_scenario",
            description="Test overspending"
        )
        assert not success
        assert result == "Insufficient credits"

    def test_get_transaction_history(self):
        """Test getting transaction history"""
        # Create some transactions
        self.repository.add_credits(
            user_id=self.user_id,
            amount=100,
            transaction_type="initial",
            description="Initial balance"
        )
        self.repository.spend_credits(
            user_id=self.user_id,
            amount=30,
            scenario_type="test_scenario",
            description="Test spending"
        )

        # Get history
        history = self.repository.get_transaction_history(self.user_id)
        assert len(history) == 2
        assert history[0]["amount"] == -30  # Most recent transaction (spending)
        assert history[1]["amount"] == 100  # Initial transaction

    def test_get_scenario_usage_stats(self):
        """Test getting scenario usage statistics"""
        # Create transactions for different scenarios
        self.repository.add_credits(
            user_id=self.user_id,
            amount=100,
            transaction_type="initial",
            description="Initial balance"
        )
        
        scenarios = [
            ("search", 10),
            ("chat", 20),
            ("search", 15),
            ("navigation", 5)
        ]
        
        for scenario_type, amount in scenarios:
            self.repository.spend_credits(
                user_id=self.user_id,
                amount=amount,
                scenario_type=scenario_type,
                description=f"Test {scenario_type}"
            )

        # Get stats
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        stats = self.repository.get_scenario_usage_stats(
            self.user_id,
            start_date,
            end_date
        )

        # Verify stats
        assert len(stats) == 3  # Three different scenarios
        search_stats = next(s for s in stats if s["scenario_type"] == "search")
        assert search_stats["total_usage"] == 25  # 10 + 15
        assert search_stats["usage_count"] == 2 