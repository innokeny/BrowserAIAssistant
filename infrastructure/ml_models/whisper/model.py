import torch
import numpy as np
from typing import Optional
from pathlib import Path
from config.whisper import WHISPER_MODEL, WHISPER_MODEL_DIR, WHISPER_DEVICE
import asyncio
import logging


logger = logging.getLogger(__name__)

class WhisperModel:
    def __init__(self, model_size: str = WHISPER_MODEL, model_dir: Path = WHISPER_MODEL_DIR):
        logger.info("Loading Whisper model...")
        self.device = WHISPER_DEVICE
        self.model = self._load_model(model_size, model_dir)

    def _load_model(self, model_size: str, model_dir: Path):
        import whisper
        model_path = model_dir / f"{model_size}.pt"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Whisper model not found at {model_path}")
            
        return whisper.load_model(model_size, device=self.device, download_root=model_dir)

    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        language: Optional[str] = None
    ) -> str:
        try:
            logger.info("Starting transcription...")
            
            # Ресемплинг до 16 кГц
            if sample_rate != 16000:
                audio_data = self._resample(audio_data, sample_rate)
            
            # Преобразование в формат, ожидаемый Whisper
            audio_data = audio_data.reshape(-1)  # Конвертация в 1D массив
            audio_data = audio_data.astype(np.float32)
            
            # Выполнение транскрибации
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.transcribe(audio_data, language=language)
            )
            
            logger.info("Transcription successful")
            return result["text"]
        
        except Exception as e:
            logger.error("Whisper error: %s", str(e))
            raise

    def _resample(self, audio_data: np.ndarray, original_rate: int) -> np.ndarray:
        import librosa
        return librosa.resample(
            audio_data.astype(np.float32),  
            orig_sr=original_rate,
            target_sr=16000
        )