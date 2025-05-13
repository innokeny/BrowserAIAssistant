from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from core.use_cases.tts_use_cases import TextToSpeechUseCase
from core.entities.text import TextInput
from infrastructure.ml_models.silero.model import SileroModel
from infrastructure.messaging.message_service import MessageService
from io import BytesIO
import logging


router = APIRouter(prefix="/tts", tags=["text-to-speech"])
logger = logging.getLogger(__name__)

model = SileroModel()
use_case = TextToSpeechUseCase(model)
message_service = MessageService()

def is_russian_text(text: str) -> bool:
    """Проверяет, содержит ли текст только русские символы"""
    try:
        allowed_symbols = {' ', ',', '.', '!', '?', ':', '%', '-', '(', ')', '/'}
        return all(
            '\u0400' <= char <= '\u04FF' or  
            char in allowed_symbols or       
            char.isdigit()                   
            for char in text
        )
    except Exception as e:
        logger.error(f"Language check error: {str(e)}")
        return False

@router.post("/synthesize")
async def synthesize_speech(
    request_data: dict  # {"text": "текст", "speaker": "aidar"}
) -> StreamingResponse:
    text = request_data.get("text", "")
    speaker = request_data.get("speaker", "baya")
    try:
        if not is_russian_text(text):
            raise HTTPException(400, detail="Поддерживается только русский язык")

        # Публикуем запрос в очередь
        await message_service.publish_tts_request(text, speaker)
        logger.info(f"TTS request published to queue: {text[:50]}...")

        # Для обратной совместимости продолжаем синхронную обработку
        text_input = TextInput(text=text)
        result = await use_case.synthesize(text_input=text_input, speaker=speaker)
        
        if not result.is_success:
            logger.error(f"TTS failed: {result.error_message}")
            raise HTTPException(400, detail=result.error_message)
            
        return StreamingResponse(
            BytesIO(result.data),
            media_type="audio/wav",
            headers={"Sample-Rate": str(result.sample_rate)}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"TTS error: {str(e)}", exc_info=True)
        raise HTTPException(500, detail="Internal server error")