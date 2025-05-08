from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
from infrastructure.web.auth_service import AuthService

router = APIRouter()
credit_repository = CreditRepositoryImpl()
auth_service = AuthService()

class CreditBalance(BaseModel):
    balance: int

class CreditTransaction(BaseModel):
    amount: int
    transaction_type: str
    scenario_type: Optional[str] = None
    description: Optional[str] = None

class CreditTransactionResponse(BaseModel):
    id: int
    amount: int
    transaction_type: str
    scenario_type: Optional[str]
    description: Optional[str]
    created_at: str

@router.get("/credits/balance", response_model=CreditBalance)
async def get_balance(user_id: int = Depends(auth_service.get_current_user_id)):
    """Get current credit balance"""
    balance = credit_repository.get_user_balance(user_id)
    return {"balance": balance}

@router.post("/credits/add", response_model=CreditBalance)
async def add_credits(
    transaction: CreditTransaction,
    user_id: int = Depends(auth_service.get_current_user_id)
):
    """Add credits to user's balance"""
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    new_balance = credit_repository.add_credits(
        user_id=user_id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        description=transaction.description
    )
    return {"balance": new_balance}

@router.get("/credits/history", response_model=List[CreditTransactionResponse])
async def get_transaction_history(
    user_id: int = Depends(auth_service.get_current_user_id),
    limit: int = 50
):
    """Get transaction history"""
    transactions = credit_repository.get_transaction_history(user_id, limit)
    return transactions 