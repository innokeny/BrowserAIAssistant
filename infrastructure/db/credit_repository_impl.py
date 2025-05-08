from infrastructure.db.db_connection import get_db_session, get_redis_client
from infrastructure.db.models import UserCredits, CreditTransaction
from datetime import datetime, timedelta
import json
from typing import List, Optional
from sqlalchemy import func, desc

class CreditRepositoryImpl:
    def __init__(self):
        self.redis_client = get_redis_client()
    
    def get_user_balance(self, user_id: int) -> int:
        """Get user's current credit balance"""
        cache_key = f"credits:{user_id}"
        cached_balance = self.redis_client.get(cache_key)
        
        if cached_balance:
            return int(cached_balance)
        
        with get_db_session() as session:
            # Get sum of all transactions
            transaction_sum = session.query(func.sum(CreditTransaction.amount))\
                .filter(CreditTransaction.user_id == user_id)\
                .scalar() or 0
            
            # Cache the result
            self.redis_client.setex(cache_key, 300, str(transaction_sum))
            
            return transaction_sum
    
    def add_credits(self, user_id: int, amount: int, transaction_type: str, description: Optional[str] = None) -> int:
        """Add credits to user's balance"""
        with get_db_session() as session:
            # Update UserCredits balance
            user_credits = session.query(UserCredits).filter(
                UserCredits.user_id == user_id
            ).first()
            
            if not user_credits:
                user_credits = UserCredits(user_id=user_id, balance=0)
                session.add(user_credits)
            
            # Create transaction record
            transaction = CreditTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description
            )
            session.add(transaction)
            session.commit()
            
            # Clear cache before getting new balance
            cache_key = f"credits:{user_id}"
            self.redis_client.delete(cache_key)
            
            # Get total balance including transactions
            total_balance = self.get_user_balance(user_id)
            
            return total_balance
    
    def spend_credits(self, user_id, amount, scenario_type=None, description=None):
        """Spend credits from user's balance"""
        with get_db_session() as session:
            # Get current balance including transactions
            current_balance = self.get_user_balance(user_id)
            
            if current_balance < amount:
                return False, "Insufficient credits"
            
            # Get or create UserCredits record
            user_credits = session.query(UserCredits).filter(
                UserCredits.user_id == user_id
            ).first()
            
            if not user_credits:
                user_credits = UserCredits(user_id=user_id, balance=0)
                session.add(user_credits)
            
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
            
            # Clear cache before getting new balance
            cache_key = f"credits:{user_id}"
            self.redis_client.delete(cache_key)
            
            # Get total balance including transactions
            total_balance = self.get_user_balance(user_id)
            
            return True, total_balance
    
    def get_transaction_history(self, user_id: int, limit: int = 50) -> List[dict]:
        """Get user's transaction history"""
        with get_db_session() as session:
            transactions = session.query(CreditTransaction)\
                .filter(CreditTransaction.user_id == user_id)\
                .order_by(desc(CreditTransaction.created_at))\
                .limit(limit)\
                .all()
            
            return [{
                "id": t.id,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "scenario_type": t.scenario_type,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            } for t in transactions]

    def get_scenario_usage_stats(self, user_id: int, start_date: datetime, end_date: datetime) -> List[dict]:
        with get_db_session() as session:
            stats = session.query(
                CreditTransaction.scenario_type,
                func.sum(CreditTransaction.amount).label('total_usage'),
                func.count(CreditTransaction.id).label('usage_count')
            ).filter(
                CreditTransaction.user_id == user_id,
                CreditTransaction.transaction_type == 'scenario_usage',
                CreditTransaction.created_at.between(start_date, end_date)
            ).group_by(CreditTransaction.scenario_type).all()

            return [{
                "scenario_type": stat.scenario_type,
                "total_usage": abs(stat.total_usage),
                "credit_cost": abs(stat.total_usage),
                "usage_count": stat.usage_count
            } for stat in stats]

    def get_period_stats(self, user_id: int, period: str) -> List[dict]:
        with get_db_session() as session:
            now = datetime.utcnow()
            
            if period == "day":
                intervals = [(now - timedelta(hours=i), now - timedelta(hours=i-1)) 
                           for i in range(24, 0, -1)]
                period_format = "%H:00"
            elif period == "week":
                intervals = [(now - timedelta(days=i), now - timedelta(days=i-1)) 
                           for i in range(7, 0, -1)]
                period_format = "%Y-%m-%d"
            elif period == "month":
                intervals = [(now - timedelta(days=i), now - timedelta(days=i-1)) 
                           for i in range(30, 0, -1)]
                period_format = "%Y-%m-%d"
            else:  # year
                intervals = [(now - timedelta(days=i*30), now - timedelta(days=(i-1)*30)) 
                           for i in range(12, 0, -1)]
                period_format = "%Y-%m"

            stats = []
            for start, end in intervals:
                period_stats = session.query(
                    func.sum(CreditTransaction.amount).label('total_spent')
                ).filter(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.transaction_type == 'scenario_usage',
                    CreditTransaction.created_at.between(start, end)
                ).scalar() or 0

                scenario_stats = session.query(
                    CreditTransaction.scenario_type,
                    func.sum(CreditTransaction.amount).label('total_usage'),
                    func.count(CreditTransaction.id).label('usage_count')
                ).filter(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.transaction_type == 'scenario_usage',
                    CreditTransaction.created_at.between(start, end)
                ).group_by(CreditTransaction.scenario_type).all()

                stats.append({
                    "period": start.strftime(period_format),
                    "total_spent": abs(period_stats),
                    "scenario_breakdown": [{
                        "scenario_type": stat.scenario_type,
                        "total_usage": abs(stat.total_usage),
                        "credit_cost": abs(stat.total_usage),
                        "usage_count": stat.usage_count
                    } for stat in scenario_stats]
                })

            return stats 