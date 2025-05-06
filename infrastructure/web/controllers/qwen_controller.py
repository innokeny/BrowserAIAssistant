from fastapi import APIRouter, HTTPException
from core.use_cases.qwen_use_cases import QwenUseCase
from core.entities.text import LLMInput
import logging

router = APIRouter(prefix="/qwen", tags=["qwen"])
logger = logging.getLogger(__name__)

use_case = QwenUseCase()

@router.post("/generate")
async def generate_text(
    request_data: dict  
):
    try:
        prompt = request_data.get("prompt")
        if not prompt:
            raise HTTPException(400, detail="Prompt is required")
            
        max_length = request_data.get("max_length", 512)
        temperature = request_data.get("temperature", 0.7)
        
        input_data = LLMInput(prompt=prompt)
        logger.debug(f"Input data: {input_data}")
        
        result = await use_case.generate(
            input_data=input_data,
            max_length=max_length,
            temperature=temperature
        )
        
        if not result.is_success:
            logger.error(f"Generation failed: {result.error_message}")
            raise HTTPException(400, detail=result.error_message)
            
        logger.info(f"Successfully generated {len(result.text)} symbols")
        return {"text": result.text}
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=str(e)) 