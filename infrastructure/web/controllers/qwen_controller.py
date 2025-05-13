from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List
from core.use_cases.qwen_use_cases import QwenUseCase
from core.entities.text import LLMInput, TextInput
from core.entities.user import User
from infrastructure.web.auth_service import get_current_user
from infrastructure.db.models import User as DBUser
from core.repositories.qwen_repository_impl import QwenRepositoryImpl
from core.repositories.credit_repository_impl import CreditRepositoryImpl
from infrastructure.web.schemas.qwen_schema import QwenHistory
from fastapi.responses import JSONResponse
from infrastructure.ml_models.qwen.model import QwenModel
from infrastructure.messaging.message_service import MessageService
import logging
import asyncio
from uuid import uuid4

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/qwen", tags=["qwen"])
use_case = QwenUseCase()
qwen_repo = QwenRepositoryImpl()
credit_repo = CreditRepositoryImpl()
model = QwenModel()
message_service = MessageService()

# Словарь для хранения результатов обработки
response_futures = {}

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

@router.post("/generate")
async def generate_text(
    request_data: dict  # {"prompt": "текст", "max_tokens": 500, "temperature": 0.7}
) -> JSONResponse:
    try:
        prompt = request_data.get("prompt", "")
        max_tokens = request_data.get("max_tokens", 500)
        temperature = request_data.get("temperature", 0.7)

        # Генерируем уникальный ID для запроса
        request_id = str(uuid4())
        
        # Создаем Future для ожидания результата
        future = asyncio.Future()
        response_futures[request_id] = future

        # Публикуем запрос в очередь
        await message_service.publish_llm_request(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            request_id=request_id  # Добавляем ID запроса
        )
        logger.info(f"LLM request published to queue: {prompt[:50]}...")

        # Ждем результат
        try:
            result = await asyncio.wait_for(future, timeout=30.0)  # 30 секунд таймаут
            return JSONResponse(content={"text": result})
        except asyncio.TimeoutError:
            raise HTTPException(504, detail="Request timeout")
        finally:
            # Удаляем Future из словаря
            response_futures.pop(request_id, None)
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"LLM error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail="Internal server error")
