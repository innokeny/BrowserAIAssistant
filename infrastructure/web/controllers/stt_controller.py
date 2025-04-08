from fastapi import APIRouter, UploadFile, HTTPException
from core.use_cases.stt_use_cases import SpeechToTextUseCase
from infrastructure.ml_models.whisper.model import WhisperModel
import numpy as np
import soundfile as sf
from io import BytesIO
from core.entities.audio import AudioInput

router = APIRouter(prefix="/stt", tags=["speech-to-text"])

model = WhisperModel()
use_case = SpeechToTextUseCase(model)

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile, language: str = None):
    try:
        audio_data, sample_rate = sf.read(BytesIO(await file.read()))
        audio_input = AudioInput(data=audio_data, sample_rate=sample_rate)
        result = await use_case.transcribe(
            audio_input=audio_input,
            language=language
        )
        
        if result is None:
            raise HTTPException(500, detail="Internal error: No transcription result")
            
        if not result.is_success:
            raise HTTPException(400, detail=result.error_message)
            
        return {"text": result.text}
    except Exception as e:
        raise HTTPException(500, detail=str(e))