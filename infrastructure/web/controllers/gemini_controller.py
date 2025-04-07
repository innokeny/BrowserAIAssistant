from fastapi import APIRouter, HTTPException
from core.use_cases.gemini_use_cases import GeminiUseCase
from config.gemini import GEMINI_MODEL_NAME
from core.entities.text import LLMInput

router = APIRouter(prefix="/gemini", tags=["gemini"])

use_case = GeminiUseCase(model_name=GEMINI_MODEL_NAME)

@router.post("/generate")
async def generate_text(prompt: str, max_length: int = 512, temperature: float = 0.7):
    try:
        input_data = LLMInput(prompt=prompt)
        result = await use_case.generate(
            input_data=input_data,
            max_length=max_length,
            temperature=temperature
        )
        
        if not result.is_success:
            raise HTTPException(400, detail=result.error_message)
            
        return {"text": result.text}
    except Exception as e:
        raise HTTPException(500, detail=str(e))