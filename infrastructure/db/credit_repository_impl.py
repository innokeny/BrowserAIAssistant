from infrastructure.db.db_connection import get_db_session, get_redis_client
from infrastructure.db.models import UserCredits, CreditTransaction
from datetime import datetime
import json

class CreditRepositoryImpl:
    def __init__(self):
        self.redis_client = get_redis_client()
    
    def get_user_balance(self, user_id):
        """Get user's current credit balance"""
        cache_key = f"credits:{user_id}"
        cached_balance = self.redis_client.get(cache_key)
        
        if cached_balance:
            return int(cached_balance)
        
        with get_db_session() as session:
            user_credits = session.query(UserCredits).filter(
                UserCredits.user_id == user_id
            ).first()
            
            if user_credits:
                self.redis_client.setex(cache_key, 300, str(user_credits.balance))
                return user_credits.balance
            
            # Create initial balance if not exists
            user_credits = UserCredits(user_id=user_id, balance=100)
            session.add(user_credits)
            session.commit()
            
            # Add initial transaction
            transaction = CreditTransaction(
                user_id=user_id,
                amount=100,
                transaction_type='initial',
                description='Initial credits'
            )
            session.add(transaction)
            session.commit()
            
            self.redis_client.setex(cache_key, 300, '100')
            return 100
    
    def add_credits(self, user_id, amount, transaction_type='manual', description=None):
        """Add credits to user's balance"""
        with get_db_session() as session:
            user_credits = session.query(UserCredits).filter(
                UserCredits.user_id == user_id
            ).first()
            
            if not user_credits:
                user_credits = UserCredits(user_id=user_id, balance=amount)
                session.add(user_credits)
            else:
                user_credits.balance += amount
            
            # Record transaction
            transaction = CreditTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description
            )
            session.add(transaction)
            session.commit()
            
            # Update cache
            cache_key = f"credits:{user_id}"
            self.redis_client.setex(cache_key, 300, str(user_credits.balance))
            
            return user_credits.balance
    
    def spend_credits(self, user_id, amount, scenario_type=None, description=None):
        """Spend credits from user's balance"""
        with get_db_session() as session:
            user_credits = session.query(UserCredits).filter(
                UserCredits.user_id == user_id
            ).first()
            
            if not user_credits or user_credits.balance < amount:
                return False, "Insufficient credits"
            
            user_credits.balance -= amount
            
            # Record transaction
            transaction = CreditTransaction(
                user_id=user_id,
                amount=-amount,
                transaction_type='scenario_usage',
                scenario_type=scenario_type,
                description=description
            )
            session.add(transaction)
            session.commit()
            
            # Update cache
            cache_key = f"credits:{user_id}"
            self.redis_client.setex(cache_key, 300, str(user_credits.balance))
            
            return True, user_credits.balance
    
    def get_transaction_history(self, user_id, limit=50):
        """Get user's transaction history"""
        with get_db_session() as session:
            transactions = session.query(CreditTransaction).filter(
                CreditTransaction.user_id == user_id
            ).order_by(CreditTransaction.created_at.desc()).limit(limit).all()
            
            return [{
                'id': t.id,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'scenario_type': t.scenario_type,
                'description': t.description,
                'created_at': t.created_at.isoformat()
            } for t in transactions] 