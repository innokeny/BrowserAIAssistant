from pathlib import Path
import torch
import os
import whisper
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

def download_silero_model(save_dir: Path):
    """Загрузка модели Silero TTS с правильной инициализацией"""
    try:
        # Явно указываем путь для кеширования
        torch.hub.set_dir(str(save_dir))
        
        # Загружаем модель с правильными параметрами
        model = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language='ru',
            speaker='v3_1_ru',
            trust_repo=True,
            verbose=False  # Отключаем вывод логов загрузки
        )
        
        # Сохраняем только необходимые компоненты модели
        torch.save({
            'model_state_dict': model.state_dict(),
            'symbols': model.symbols,
            'speakers': model.speakers
        }, save_dir / "silero_model.pt")
        
        print(f"Silero model components saved to {save_dir/'silero_model.pt'}")
        return model
    except Exception as e:
        print(f"Error saving Silero components: {e}")
        raise

def download_whisper_model(model_name: str, save_dir: Path):
    """Загрузка модели Whisper"""
    save_dir.mkdir(parents=True, exist_ok=True)
    os.environ["WHISPER_MODEL_DIR"] = str(save_dir)
    
    try:
        model = whisper.load_model(model_name, download_root=save_dir)
        print(f"Whisper model {model_name} downloaded to {save_dir}")
        return model
    except Exception as e:
        print(f"Error downloading Whisper: {e}")
        raise

def download_all_models():
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    try:
        print("Downloading Silero TTS model...")
        silero_dir = models_dir / "silero"
        silero_dir.mkdir(exist_ok=True)
        download_silero_model(silero_dir)
    except Exception as e:
        print(f"Final Silero download error: {str(e)}")
        print("Consider manual download from:")
        print("https://models.silero.ai/models/tts/ru/v3_1_ru.pt")

if __name__ == "__main__":
    download_all_models()