import torch
from pathlib import Path
from config.silero import SILERO_MODEL_DIR, SILERO_DEVICE

class SileroModel:
    def __init__(self, model_dir: Path = SILERO_MODEL_DIR):
        self.device = SILERO_DEVICE
        self.model, self.symbols, self.speakers = self._load_model(model_dir)

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
        speaker: str = "random",
        sample_rate: int = 24000
    ) -> bytes:
        audio = self.model.apply_tts(
            text=text,
            speaker=speaker,
            sample_rate=sample_rate
        )
        return audio.numpy().tobytes()