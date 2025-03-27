from fastapi import APIRouter, HTTPException
from core.use_cases.llm_use_cases import LLMUseCase
from infrastructure.ml_models.tinyllama.model import TinyLlamaModel

router = APIRouter(prefix="/llm", tags=["language-model"])

model = TinyLlamaModel()
use_case = LLMUseCase(model)

@router.post("/generate")
async def generate_text(prompt: str, max_length: int = 128, temperature: float = 0.7):
    try:
        result = await use_case.generate(
            prompt=prompt,
            max_length=max_length,
            temperature=temperature
        )
        
        if not result.is_success:
            raise HTTPException(400, detail=result.error_message)
            
        return {"text": result.text}
    except Exception as e:
        raise HTTPException(500, detail=str(e))