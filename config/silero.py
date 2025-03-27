from pathlib import Path
from config.settings import MODELS_DIR
import torch

SILERO_MODEL_DIR = MODELS_DIR / "silero"
SILERO_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'