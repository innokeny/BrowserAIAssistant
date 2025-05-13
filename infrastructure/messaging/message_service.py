from typing import Optional
from .tts_client import TTSRabbitMQClient
from .stt_client import STTRabbitMQClient
from .llm_client import LLMRabbitMQClient
import logging

logger = logging.getLogger(__name__)

class MessageService:
    _instance: Optional['MessageService'] = None
    _tts_client: Optional[TTSRabbitMQClient] = None
    _stt_client: Optional[STTRabbitMQClient] = None
    _llm_client: Optional[LLMRabbitMQClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        """Инициализация клиентов RabbitMQ"""
        try:
            self._tts_client = TTSRabbitMQClient()
            self._stt_client = STTRabbitMQClient()
            self._llm_client = LLMRabbitMQClient()

            # Подключаем клиенты к RabbitMQ
            await self._tts_client.connect()
            await self._stt_client.connect()
            await self._llm_client.connect()

            logger.info("RabbitMQ clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ clients: {e}")
            raise

    async def close(self):
        """Закрытие соединений с RabbitMQ"""
        try:
            if self._tts_client:
                await self._tts_client.close()
            if self._stt_client:
                await self._stt_client.close()
            if self._llm_client:
                await self._llm_client.close()
            logger.info("RabbitMQ connections closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connections: {e}")

    async def publish_tts_request(self, text: str, speaker: str = "baya"):
        """Публикация запроса на преобразование текста в речь"""
        if not self._tts_client:
            raise RuntimeError("TTS client not initialized")
        
        await self._tts_client.publish_tts_request({
            "text": text,
            "speaker": speaker
        })
        logger.info(f"Published TTS request for text: {text[:50]}...")

    async def publish_stt_request(self, audio_data: bytes):
        """Публикация запроса на преобразование речи в текст"""
        if not self._stt_client:
            raise RuntimeError("STT client not initialized")
        
        await self._stt_client.publish_stt_request({
            "audio_data": audio_data
        })
        logger.info("Published STT request")

    async def publish_llm_request(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7, request_id: str = None):
        """Публикация запроса к языковой модели"""
        if not self._llm_client:
            raise RuntimeError("LLM client not initialized")
        
        await self._llm_client.publish_llm_request({
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "request_id": request_id
        })
        logger.info(f"Published LLM request for prompt: {prompt[:50]}...") 