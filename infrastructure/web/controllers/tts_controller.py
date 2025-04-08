from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from core.use_cases.tts_use_cases import TextToSpeechUseCase
from core.entities.text import TextInput
from infrastructure.ml_models.silero.model import SileroModel
from io import BytesIO


router = APIRouter(prefix="/tts", tags=["text-to-speech"])

model = SileroModel()
use_case = TextToSpeechUseCase(model)

class SynthesizeRequest(BaseModel):
    text: str
    speaker: str = "random"

@router.get("/synthesize")
async def synthesize_speech(
    text: str = Query(..., example="привет"),
    speaker: str = Query("random", example="random")
) -> StreamingResponse:
    try:
        text_input = TextInput(text=text)
        result = await use_case.synthesize(text_input=text_input, speaker=speaker)
        
        if not result.is_success:
            raise HTTPException(400, detail=result.error_message)
            
        return StreamingResponse(
            BytesIO(result.data),
            media_type="audio/wav",
            headers={"Sample-Rate": str(result.sample_rate)}
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))