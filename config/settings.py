from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"

class Settings:
    APP_NAME: str = "ML Services API"
    DEBUG: bool = True

settings = Settings()