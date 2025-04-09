import torch
import torchaudio
import io
import logging
import random
from pathlib import Path
from config.silero import SILERO_MODEL_DIR, SILERO_DEVICE

logger = logging.getLogger(__name__)

class SileroModel:
    def __init__(self, model_dir: Path = SILERO_MODEL_DIR):
        self.device = SILERO_DEVICE
        self.model, self.symbols, self.speakers = self._load_model(model_dir)
        logger.info(f"Loaded Silero model. Speakers: {self.speakers}")

    def _load_model(self, model_dir: Path):
        model_path = model_dir / "v3_1_ru.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Silero model not found at {model_path}")
            
        model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
        model.to(self.device)
        return model, model.symbols, model.speakers

    async def synthesize(
        self,
        text: str,
        speaker: str = "aidar",
        sample_rate: int = 24000
    ) -> bytes:
        try:
            # Проверка и выбор спикера
            if speaker == "random":
                speaker = random.choice(self.speakers)
            elif speaker not in self.speakers:
                raise ValueError(f"Speaker {speaker} not in {self.speakers}")

            # Генерация аудио
            audio = self.model.apply_tts(
                text=text,
                speaker=speaker,
                sample_rate=sample_rate
            )

            # Конвертация в WAV
            buffer = io.BytesIO()
            torchaudio.save(
                buffer, 
                audio.unsqueeze(0), 
                sample_rate, 
                format="wav",
                encoding="PCM_S",
                bits_per_sample=16
            )
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Silero synthesis error: {str(e)}", exc_info=True)
            raise RuntimeError(f"TTS failed: {str(e)}")