from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from core.use_cases.tts_use_cases import TextToSpeechUseCase
from infrastructure.ml_models.silero.model import SileroModel
from io import BytesIO

router = APIRouter(prefix="/tts", tags=["text-to-speech"])

model = SileroModel()
use_case = TextToSpeechUseCase(model)

@router.post("/synthesize")
async def synthesize_speech(text: str, speaker: str = "random"):
    try:
        result = await use_case.synthesize(text=text, speaker=speaker)
        
        if not result.is_success:
            raise HTTPException(400, detail=result.error_message)
            
        return StreamingResponse(
            BytesIO(result.data),
            media_type="audio/wav",
            headers={
                "Sample-Rate": str(result.sample_rate)
            }
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))