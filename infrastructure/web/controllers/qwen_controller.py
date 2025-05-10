from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Dict, Any, List
from core.use_cases.qwen_use_cases import QwenUseCase
from core.entities.text import LLMInput
from core.entities.user import User
from infrastructure.web.auth_service import get_current_user
from infrastructure.db.resource_manager import ResourceManager
from infrastructure.db.models import User as DBUser
from infrastructure.db.qwen_repository_impl import QwenRepositoryImpl
from infrastructure.db.credit_repository_impl import CreditRepositoryImpl
from infrastructure.db.quota_repository_impl import QuotaRepositoryImpl
from infrastructure.web.schemas.qwen_schema import QwenRequest, QwenResponse, QwenHistory
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["qwen"])
use_case = QwenUseCase()
resource_manager = ResourceManager()
qwen_repo = QwenRepositoryImpl()
credit_repo = CreditRepositoryImpl()
quota_repo = QuotaRepositoryImpl()

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

@router.post("/chat", response_model=QwenResponse)
async def chat(
    request: QwenRequest,
    current_user: DBUser = Depends(get_current_user)
):
    """Process a chat request"""
    try:
        # Check credits
        current_balance = credit_repo.get_user_balance(current_user.id)
        if current_balance < 1:  # Assuming 1 credit per request
            raise HTTPException(
                status_code=400,
                detail="Insufficient credits"
            )
        
        # Check quota
        quota = quota_repo.get_user_quota(current_user.id, "qwen")
        if not quota:
            raise HTTPException(
                status_code=400,
                detail="No quota found for Qwen service"
            )
        
        quota = quota[0]  # Get first quota since we filtered by resource_type
        if quota["current_usage"] >= quota["limit"]:
            raise HTTPException(
                status_code=400,
                detail="Quota exceeded"
            )
        
        # Process request
        response = qwen_repo.process_request(
            user_id=current_user.id,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Deduct credits
        credit_repo.create_transaction(
            user_id=current_user.id,
            amount=-1,  # Deduct 1 credit
            transaction_type="qwen_chat",
            description="Qwen chat request"
        )
        
        # Update quota
        quota_repo.update_quota_usage(
            user_id=current_user.id,
            resource_type="qwen",
            usage=quota["current_usage"] + 1
        )
        
        return {
            "response": response,
            "tokens_used": len(response.split()),  # Simple token count
            "created_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/qwen/generate", response_model=GenerateTextResponse)
async def generate_text(
    request_data: GenerateTextRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate text using Qwen model"""
    try:
        # Check credits first
        current_balance = credit_repo.get_user_balance(current_user.id)
        if current_balance < 1:  # Assuming 1 credit per request
            logger.error(f"Insufficient credits for user {current_user.id}: {current_balance}")
            raise HTTPException(
                status_code=400,
                detail="Insufficient credits"
            )

        # Then check quota
        quota = quota_repo.get_user_quota(current_user.id, "qwen")
        if not quota:
            logger.error(f"No quota found for user {current_user.id}")
            raise HTTPException(
                status_code=400,
                detail="No quota found for Qwen service"
            )
        
        quota = quota[0]  # Get first quota since we filtered by resource_type
        if quota["current_usage"] >= quota["limit"]:
            logger.error(f"Quota exceeded for user {current_user.id}: {quota['current_usage']}/{quota['limit']}")
            raise HTTPException(
                status_code=400,
                detail="Quota exceeded"
            )
        
        input_data = LLMInput(prompt=request_data.prompt)
        logger.debug(f"Input data: {input_data}")
        
        start_time = datetime.now()
        result = await use_case.generate(
            input_data=input_data,
            max_length=request_data.max_tokens,
            temperature=request_data.temperature
        )
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        if not result.is_success:
            logger.error(f"Generation failed: {result.error_message}")
            raise HTTPException(400, detail=result.error_message)
        
        # Track usage with JSON strings
        resource_manager.track_usage(
            user_id=current_user.id,
            resource_type="qwen",
            request_data=json.dumps({"prompt": request_data.prompt}),
            response_data=json.dumps({"text": result.text}),
            status="success",
            processing_time=processing_time
        )
            
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

@router.post("/qwen/generate/stream")
async def generate_text_stream(
    request_data: GenerateTextRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate text using Qwen model with streaming response"""
    try:
        # Check credits first
        current_balance = credit_repo.get_user_balance(current_user.id)
        if current_balance < 1:  # Assuming 1 credit per request
            raise HTTPException(
                status_code=400,
                detail="Insufficient credits"
            )

        # Then check quota
        quota = quota_repo.get_user_quota(current_user.id, "qwen")
        if not quota:
            raise HTTPException(
                status_code=400,
                detail="No quota found for Qwen service"
            )
        
        quota = quota[0]  # Get first quota since we filtered by resource_type
        if quota["current_usage"] >= quota["limit"]:
            raise HTTPException(
                status_code=400,
                detail="Quota exceeded"
            )
        
        input_data = LLMInput(prompt=request_data.prompt)
        logger.debug(f"Input data: {input_data}")
        
        start_time = datetime.now()
        
        async def generate():
            try:
                async for chunk in use_case.generate_stream(
                    input_data=input_data,
                    max_length=request_data.max_tokens,
                    temperature=request_data.temperature
                ):
                    if not chunk.is_success:
                        logger.error(f"Streaming failed: {chunk.error_message}")
                        yield json.dumps({"error": chunk.error_message}) + "\n"
                        return
                    
                    yield json.dumps({"text": chunk.text}) + "\n"
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Track usage after streaming completes
                resource_manager.track_usage(
                    user_id=current_user.id,
                    resource_type="qwen",
                    request_data=json.dumps({"prompt": request_data.prompt}),
                    response_data=json.dumps({"streaming": True}),
                    status="success",
                    processing_time=processing_time
                )
                    
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}", exc_info=True)
                yield json.dumps({"error": str(e)}) + "\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=str(e)) 