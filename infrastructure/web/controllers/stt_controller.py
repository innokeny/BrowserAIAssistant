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
        
        # Чтение аудио
        raw_data = await file.read()
        logger.debug("Audio size: %d bytes", len(raw_data))
        
                # Конвертация WebM → WAV
        audio = AudioSegment.from_file(
            io.BytesIO(raw_data), 
            format="webm"  # Для Chrome
            # format="ogg"  # Для Firefox
        )
        
        # Приведение к нужным параметрам
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Экспорт в WAV
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        # Чтение WAV
        audio_data, sample_rate = sf.read(wav_buffer)
        logger.info("Audio params: shape=%s, sr=%d", audio_data.shape, sample_rate)
        
        # Проверка формата данных
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
            
        # Нормализация
        audio_data /= np.max(np.abs(audio_data))
        
        # Создание объекта AudioInput
        audio_input = AudioInput(data=audio_data, sample_rate=sample_rate)
        
        # Транскрибация
        result = await use_case.transcribe(audio_input, language)
        logger.debug("Transcription result: %s", result)

        if result is None:
            raise HTTPException(500, detail="Internal error: No transcription result")
            
        if not result.is_success:
            raise HTTPException(400, detail=result.error_message)
            
        return {"text": result.text}
    except Exception as e:
        logger.error("Transcription failed: %s", str(e), exc_info=True)
        raise HTTPException(500, detail=str(e))