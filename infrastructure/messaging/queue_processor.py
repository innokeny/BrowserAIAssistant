import asyncio
import logging
import base64
import numpy as np
import soundfile as sf
import io
from pydub import AudioSegment
from typing import Dict, Any
from .message_service import MessageService
from core.use_cases.tts_use_cases import TextToSpeechUseCase
from core.use_cases.stt_use_cases import SpeechToTextUseCase
from core.use_cases.qwen_use_cases import QwenUseCase
from core.entities.audio import AudioInput
from core.entities.text import LLMInput
from infrastructure.ml_models.silero.model import SileroModel
from infrastructure.ml_models.whisper.model import WhisperModel
from infrastructure.ml_models.qwen.model import QwenModel
from infrastructure.web.controllers.qwen_controller import response_futures

logger = logging.getLogger(__name__)

class QueueProcessor:
    def __init__(self):
        self.message_service = MessageService()
        self.tts_use_case = TextToSpeechUseCase(SileroModel())
        self.stt_use_case = SpeechToTextUseCase(WhisperModel())
        self.llm_use_case = QwenUseCase()

    async def process_tts_message(self, message: Dict[str, Any]):
        """Обработка сообщения из очереди TTS"""
        try:
            text = message["data"]["text"]
            speaker = message["data"].get("speaker", "baya")
            
            logger.info(f"Processing TTS request: {text[:50]}...")

            
        except Exception as e:
            logger.error(f"Error processing TTS message: {e}")

    async def process_stt_message(self, message: Dict[str, Any]):
        """Обработка сообщения из очереди STT"""
        try:
            # Декодируем base64 обратно в бинарные данные
            audio_base64 = message["data"]["audio_data"]
            raw_data = base64.b64decode(audio_base64)
            
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
            
            # Создаем входные данные для STT
            audio_input = AudioInput(
                data=audio_data,
                sample_rate=sample_rate
            )
            
            # Обрабатываем аудио
            result = await self.stt_use_case.transcribe(audio_input=audio_input)
            
            if not result.is_success:
                logger.error(f"STT processing failed: {result.error_message}")
                return
                
            logger.info(f"STT processing successful: {result.text[:50]}...")
            
            
        except Exception as e:
            logger.error(f"Error processing STT message: {e}")

    async def process_llm_message(self, message: Dict[str, Any]):
        """Обработка сообщения из очереди LLM"""
        try:
            prompt = message["data"]["prompt"]
            max_tokens = message["data"].get("max_tokens", 500)
            temperature = message["data"].get("temperature", 0.7)
            request_id = message["data"].get("request_id")
            
            logger.info(f"Processing LLM request: {prompt[:50]}...")
            
            # Создаем входные данные для LLM
            input_data = LLMInput(prompt=prompt)
            
            # Обрабатываем запрос
            result = await self.llm_use_case.generate(
                input_data=input_data,
                max_length=max_tokens,
                temperature=temperature
            )
            
            if not result.is_success:
                logger.error(f"LLM processing failed: {result.error_message}")
                if request_id and request_id in response_futures:
                    response_futures[request_id].set_exception(
                        Exception(result.error_message)
                    )
                return
                
            logger.info(f"LLM processing successful: {result.text[:50]}...")
            
            # Отправляем результат обратно в контроллер
            if request_id and request_id in response_futures:
                response_futures[request_id].set_result(result.text)
            
        except Exception as e:
            logger.error(f"Error processing LLM message: {e}")
            if request_id and request_id in response_futures:
                response_futures[request_id].set_exception(e)

    async def start_processing(self):
        """Запуск обработки сообщений из всех очередей"""
        try:
            # Подписываемся на очереди
            await self.message_service._tts_client.consume_tts_requests(
                self.process_tts_message
            )
            await self.message_service._stt_client.consume_stt_requests(
                self.process_stt_message
            )
            await self.message_service._llm_client.consume_llm_requests(
                self.process_llm_message
            )
            
            logger.info("Started processing messages from all queues")
            
            # Держим процессор запущенным
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in queue processor: {e}")
            raise 