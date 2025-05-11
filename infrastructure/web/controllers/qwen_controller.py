from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List
from core.use_cases.qwen_use_cases import QwenUseCase
from core.entities.text import LLMInput
from core.entities.user import User
from infrastructure.web.auth_service import get_current_user
from infrastructure.db.models import User as DBUser
from core.repositories.qwen_repository_impl import QwenRepositoryImpl
from core.repositories.credit_repository_impl import CreditRepositoryImpl
from infrastructure.web.schemas.qwen_schema import QwenHistory
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/qwen", tags=["qwen"])
use_case = QwenUseCase()
qwen_repo = QwenRepositoryImpl()
credit_repo = CreditRepositoryImpl()

# Models
class GenerateTextRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt cannot be empty")
    max_tokens: Optional[int] = Field(100, gt=0, description="Max tokens must be positive")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Temperature must be between 0 and 1")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Test prompt",
                "max_tokens": 100,
                "temperature": 0.7
            }
        }
        validate_assignment = True
        extra = "forbid"

class GenerateTextResponse(BaseModel):
    text: str


@router.get("/history", response_model=List[QwenHistory])
async def get_history(
    limit: int = 50,
    offset: int = 0,
    current_user: DBUser = Depends(get_current_user)
):
    """Get chat history"""
    try:
        history = qwen_repo.get_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "id": h.id,
                "prompt": h.prompt,
                "response": h.response,
                "tokens_used": h.tokens_used,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate", response_model=GenerateTextResponse)
async def generate_text(
    request_data: GenerateTextRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate text using Qwen model"""
    try:
        # Проверяем баланс до генерации
        current_balance = credit_repo.get_user_balance(current_user.id)
        logger.info(f"Current balance for user {current_user.id}: {current_balance}")
        
        # Проверяем наличие 10 кредитов для LLM-чата
        if current_balance < 10: 
            logger.error(f"Insufficient credits for user {current_user.id}: {current_balance}")
            raise HTTPException(
                status_code=400,
                detail="Insufficient credits. LLM chat requires 10 credits."
            )
        
        input_data = LLMInput(prompt=request_data.prompt)
        logger.debug(f"Input data: {input_data}")
        
        result = await use_case.generate(
            input_data=input_data,
            max_length=request_data.max_tokens,
            temperature=request_data.temperature
        )
        
        if not result.is_success:
            logger.error(f"Generation failed: {result.error_message}")
            raise HTTPException(400, detail=result.error_message)

        # Списываем 10 кредитов после успешной генерации
        try:
            transaction_result = credit_repo.create_transaction(
            user_id=current_user.id,
                amount=-10,
            transaction_type="scenario_llm",
                description="Запрос к LLM (10 кредитов)"
        )
            logger.info(f"Credit transaction created: {transaction_result}")
            
            # Проверяем новый баланс
            new_balance = credit_repo.get_user_balance(current_user.id)
            logger.info(f"New balance after deduction: {new_balance}")
            
            if new_balance >= current_balance:
                logger.error("Credit deduction failed - balance not decreased")
                raise HTTPException(500, detail="Failed to deduct credits")
                
        except Exception as e:
            logger.error(f"Failed to create credit transaction: {str(e)}")
            raise HTTPException(500, detail="Failed to process credit transaction")
            
        logger.info(f"Successfully generated {len(result.text)} symbols")
        return {"text": result.text}
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=str(e))
