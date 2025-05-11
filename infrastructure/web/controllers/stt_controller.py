from fastapi import APIRouter, UploadFile, HTTPException
from core.use_cases.stt_use_cases import SpeechToTextUseCase
from infrastructure.ml_models.whisper.model import WhisperModel
import numpy as np
import soundfile as sf
import io
from io import BytesIO
from core.entities.audio import AudioInput
import logging
from pydub import AudioSegment


router = APIRouter(prefix="/stt", tags=["speech-to-text"])

model = WhisperModel()
use_case = SpeechToTextUseCase(model)

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile, language: str = None):
    try:
        logger = logging.getLogger(__name__)
        logger.info("Received audio file: %s", file.filename)
        
        raw_data = await file.read()
        logger.debug("Audio size: %d bytes", len(raw_data))
        
        audio = AudioSegment.from_file(
            io.BytesIO(raw_data), 
            format="webm"  # Для Chrome
            # format="ogg"  # Для Firefox
        )
        
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        audio_data, sample_rate = sf.read(wav_buffer)
        logger.info("Audio params: shape=%s, sr=%d", audio_data.shape, sample_rate)
        
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
            
        audio_data /= np.max(np.abs(audio_data))
        
        audio_input = AudioInput(data=audio_data, sample_rate=sample_rate)
        
        result = await use_case.transcribe(audio_input, language)
        logger.debug("Transcription result: %s", result)

        if result is None:
            raise HTTPException(500, detail="Internal error: No transcription result")
            
        if not result.is_success:
            raise HTTPException(400, detail=result.error_message)
        
        logger.info(f"text: {result.text}")
        return {"text": result.text}
    except Exception as e:
        logger.error("Transcription failed: %s", str(e), exc_info=True)
        raise HTTPException(500, detail=str(e))