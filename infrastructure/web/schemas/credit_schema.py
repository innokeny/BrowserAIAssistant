from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreditBalance(BaseModel):
    balance: int
    user_id: int

class CreditTransaction(BaseModel):
    amount: int = Field(..., description="Amount of credits to add/deduct")
    description: Optional[str] = Field(None, description="Description of the transaction")

class CreditTransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: int
    transaction_type: str
    description: Optional[str] = None
    created_at: str

class CreditTransactionCreate(BaseModel):
    amount: int = Field(..., description="Amount of credits to add/deduct")
    transaction_type: str = Field(..., description="Type of transaction")
    description: Optional[str] = Field(None, description="Description of the transaction") 