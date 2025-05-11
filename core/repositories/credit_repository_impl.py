from infrastructure.db.db_connection import get_db_session, get_redis_client
from infrastructure.db.models import UserCredits, CreditTransaction
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
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
            user_credits = session.query(UserCredits)\
                .filter(UserCredits.user_id == user_id)\
                .first()
            
            if not user_credits:
                return 0
                
            self.redis_client.setex(cache_key, 300, str(user_credits.balance))
            return user_credits.balance
    
    def add_credits(self, user_id: int, amount: int, transaction_type: str, description: Optional[str] = None) -> tuple[bool, int|str]:
        """Add credits to user's balance"""
        with get_db_session() as session:
            try:
                user_credits = session.query(UserCredits).filter(
                    UserCredits.user_id == user_id
                ).first()
                
                if not user_credits:
                    user_credits = UserCredits(user_id=user_id, balance=amount)
                else:
                    user_credits.balance += amount
                    
                session.add(user_credits)
                
                transaction = CreditTransaction(
                    user_id=user_id,
                    amount=amount,
                    transaction_type=transaction_type,
                    description=description
                )
                session.add(transaction)
                session.commit()
                
                cache_key = f"credits:{user_id}"
                self.redis_client.setex(cache_key, 300, str(user_credits.balance))
                
                return True, user_credits.balance
                
            except Exception as e:
                session.rollback()
                return False, str(e)
    
    def spend_credits(self, user_id, amount, scenario_type=None, description=None):
        """Spend credits from user's balance"""
        with get_db_session() as session:
            current_balance = self.get_user_balance(user_id)
            
            if current_balance < amount:
                return False, "Insufficient credits"
            
            user_credits = session.query(UserCredits).filter(
                UserCredits.user_id == user_id
            ).first()
            
            if not user_credits:
                user_credits = UserCredits(user_id=user_id, balance=0)
                session.add(user_credits)
            
            transaction = CreditTransaction(
                user_id=user_id,
                amount=-amount,
                transaction_type='scenario_usage',
                scenario_type=scenario_type,
                description=description
            )
            user_credits.balance -= amount
            session.add(user_credits)
            session.commit()
            
            cache_key = f"credits:{user_id}"
            self.redis_client.delete(cache_key)
            
            total_balance = self.get_user_balance(user_id)
            
            return True, total_balance
    
    def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's transaction history"""
        with get_db_session() as session:
            transactions = session.query(CreditTransaction)\
                .filter(CreditTransaction.user_id == user_id)\
                .order_by(desc(CreditTransaction.created_at))\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return [{
                "id": t.id,
                "user_id": t.user_id,
                "amount": t.amount,
                "transaction_type": t.transaction_type,
                "scenario_type": t.scenario_type,
                "description": t.description,
                "created_at": t.created_at.isoformat()
            } for t in transactions]

    def get_scenario_usage_stats(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get usage statistics for different scenarios"""
        with get_db_session() as session:
            transactions = session.query(CreditTransaction).filter(
                CreditTransaction.user_id == user_id,
                CreditTransaction.created_at >= start_date,
                CreditTransaction.created_at <= end_date,
                CreditTransaction.amount < 0  
            ).all()

            usage_by_type = {}
            for t in transactions:
                scenario_type = t.scenario_type or t.transaction_type
                if scenario_type not in usage_by_type:
                    usage_by_type[scenario_type] = {
                        "scenario_type": scenario_type,
                        "total_usage": 0,
                        "usage_count": 0
                    }
                usage_by_type[scenario_type]["total_usage"] += abs(t.amount)
                usage_by_type[scenario_type]["usage_count"] += 1

            return list(usage_by_type.values())

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

    def create_transaction(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new credit transaction"""
        with get_db_session() as session:
            current_balance = self.get_user_balance(user_id)
            
            if amount < 0 and current_balance + amount < 0:
                raise ValueError("Insufficient credit balance")
            
            transaction = CreditTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                created_at=datetime.now()
            )
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            
            new_balance = current_balance + amount
            
            cache_key = f"credits:{user_id}"
            self.redis_client.setex(cache_key, 300, str(new_balance))
            
            return {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "transaction_type": transaction.transaction_type,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
                "balance": new_balance
            } 