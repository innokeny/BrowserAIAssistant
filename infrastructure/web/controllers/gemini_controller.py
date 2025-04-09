from fastapi import APIRouter, HTTPException
from core.use_cases.gemini_use_cases import GeminiUseCase
from config.gemini import GEMINI_MODEL_NAME
from core.entities.text import LLMInput
import logging

router = APIRouter(prefix="/gemini", tags=["gemini"])
logger = logging.getLogger(__name__)

use_case = GeminiUseCase(model_name=GEMINI_MODEL_NAME)

@router.post("/generate")
async def generate_text(
    request_data: dict  
):
    try:
        prompt = request_data.get("prompt")
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
        logger.info(f"text: {result.text}")
        return {"text": result.text}
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=str(e))