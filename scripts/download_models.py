from pathlib import Path
import torch
import os
import whisper
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

def download_silero_model(save_dir: Path):
    """Загрузка модели Silero TTS"""
    try:
        # Устанавливаем директорию для кэша torch.hub
        torch.hub.set_dir(str(save_dir))
        
        # Загружаем модель (она автоматически сохранится в кэше)
        model, sample_rate = torch.hub.load(
            repo_or_dir='snakers4/silero-models',
            model='silero_tts',
            language='ru',
            speaker='v3_1_ru',
            trust_repo=True,
            verbose=False  
        )
        
        print(f"Silero model downloaded to {save_dir}")
        return model
    except Exception as e:
        print(f"Error downloading Silero model: {e}")
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
        print(f"Error downloading Whisper model: {e}")
        raise

if __name__ == "__main__":
    # Создаем директории если их нет
    Path('models/silero').mkdir(parents=True, exist_ok=True)
    Path('models/whisper').mkdir(parents=True, exist_ok=True)
    
    print("Starting model downloads...")
    
    # Скачиваем модели
    download_silero_model(Path('models/silero'))
    download_whisper_model('small', Path('models/whisper'))
    
    print("All models downloaded successfully!")