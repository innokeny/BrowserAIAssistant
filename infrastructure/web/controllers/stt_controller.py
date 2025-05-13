from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from core.use_cases.stt_use_cases import SpeechToTextUseCase
from core.entities.audio import AudioInput
from infrastructure.ml_models.whisper.model import WhisperModel
from infrastructure.messaging.message_service import MessageService
import base64
import numpy as np
import soundfile as sf
import io
from pydub import AudioSegment
import logging

router = APIRouter(prefix="/stt", tags=["speech-to-text"])
logger = logging.getLogger(__name__)

model = WhisperModel()
use_case = SpeechToTextUseCase(model)
message_service = MessageService()

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...)
) -> JSONResponse:
    try:
        # Читаем аудио файл
        raw_data = await file.read()
        
        # Конвертируем в нужный формат
        audio = AudioSegment.from_file(
            io.BytesIO(raw_data), 
            format="webm"  # Для Chrome
            # format="ogg"  # Для Firefox
        )
        
        # Устанавливаем нужные параметры
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Конвертируем в WAV
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        # Читаем аудио данные и частоту дискретизации
        audio_data, sample_rate = sf.read(wav_buffer)
        
        # Нормализуем данные
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        audio_data /= np.max(np.abs(audio_data))
        
        # Кодируем аудио данные в base64 для очереди
        audio_base64 = base64.b64encode(raw_data).decode('utf-8')
        
        # Публикуем запрос в очередь
        await message_service.publish_stt_request(audio_base64)
        logger.info("STT request published to queue")

        # Для обратной совместимости продолжаем синхронную обработку
        audio_input = AudioInput(
            data=audio_data,
            sample_rate=sample_rate
        )
        result = await use_case.transcribe(audio_input=audio_input)
        
        if not result.is_success:
            logger.error(f"STT failed: {result.error_message}")
            raise HTTPException(400, detail=result.error_message)
            
        return JSONResponse(
            content={"text": result.text}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"STT error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail="Internal server error")