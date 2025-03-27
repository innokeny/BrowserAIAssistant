from pathlib import Path
from config.settings import MODELS_DIR
import torch

WHISPER_MODEL = "small"
WHISPER_MODEL_DIR = MODELS_DIR / "whisper"
WHISPER_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'