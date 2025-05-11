from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
from infrastructure.web.auth_service import get_current_user
from infrastructure.db.models import User
from infrastructure.web.schemas.credit_schema import CreditBalance, CreditTransaction, CreditTransactionCreate, CreditTransactionResponse
from pydantic import ConfigDict


router = APIRouter(prefix="/api", tags=["credits"])
credit_repository = CreditRepositoryImpl()

class CreditTransactionResponse(BaseModel):
    id: int
    amount: int
    transaction_type: str
    description: Optional[str]
    created_at: str
    balance: int

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "id": 1,
            "amount": 100,
            "transaction_type": "initial",
            "description": "Initial credits",
            "created_at": "2024-05-10T12:00:00Z",
            "balance": 100
        }]
    })

@router.get("/credits/balance", response_model=CreditBalance)
async def get_balance(current_user: User = Depends(get_current_user)):
    """Get current credit balance"""
    balance = credit_repository.get_user_balance(current_user.id)
    return {"balance": balance, "user_id": current_user.id}

@router.get("/credits/history", response_model=List[CreditTransactionResponse])
async def get_credit_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get credit transaction history"""
    history = credit_repository.get_transaction_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    # Add balance to each transaction
    for transaction in history:
        transaction["balance"] = credit_repository.get_user_balance(current_user.id)
    
    return history

@router.post("/credits/add", response_model=CreditTransactionResponse)
async def add_credits(
    transaction: CreditTransaction,
    current_user: User = Depends(get_current_user)
):
    """Add credits to user account"""
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = credit_repository.create_transaction(
        user_id=current_user.id,
        amount=transaction.amount,
        transaction_type="add",
        description=transaction.description
    )

    # Get updated balance
    balance = credit_repository.get_user_balance(current_user.id)
    result["balance"] = balance
    return result

@router.post("/credits/deduct", response_model=CreditTransactionResponse)
async def deduct_credits(
    transaction: CreditTransaction,
    current_user: User = Depends(get_current_user)
):
    """Deduct credits from user account"""
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    current_balance = credit_repository.get_user_balance(current_user.id)
    if current_balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient credit balance")

    result = credit_repository.create_transaction(
        user_id=current_user.id,
        amount=-transaction.amount,  # Store negative amount for deduction
        transaction_type="deduct",
        description=transaction.description
    )

    # Get updated balance
    balance = credit_repository.get_user_balance(current_user.id)
    result["balance"] = balance
    return result

@router.post("/credits/transactions", response_model=CreditTransaction)
async def create_transaction(
    transaction: CreditTransactionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new credit transaction"""
    try:
        if transaction.amount < 0:
            # Check if user has enough credits for negative transactions
            current_balance = credit_repository.get_user_balance(current_user.id)
            if current_balance + transaction.amount < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient credit balance"
                )
        
        result = credit_repository.create_transaction(
            user_id=current_user.id,
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            description=transaction.description
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance", response_model=CreditBalance)
async def get_credit_balance(current_user: User = Depends(get_current_user)):
    """Get current credit balance"""
    try:
        balance = credit_repository.get_user_balance(current_user.id)
        return {"balance": balance, "user_id": current_user.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 