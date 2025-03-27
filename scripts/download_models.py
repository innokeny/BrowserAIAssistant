from pathlib import Path
import torch
import os
import whisper
import warnings

# Отключаем предупреждения torch.hub
warnings.filterwarnings("ignore", category=UserWarning)

def download_silero_model(save_dir: Path):
    """Загрузка модели Silero TTS с использованием официального API"""
    if not save_dir.exists():
        save_dir.mkdir(parents=True)
    
    torch.hub.set_dir(str(save_dir))
    
    # Используем правильное имя спикера для русской модели
    model, example_text = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_tts',
        language='ru',
        speaker='v3_1_ru',  # Исправленное имя спикера
        trust_repo=True  # Добавляем подтверждение доверия
    )
    print(f"Silero model downloaded to {save_dir}")
    return model

def download_whisper_model(model_name: str, save_dir: Path):
    """Загрузка модели Whisper"""
    if not save_dir.exists():
        save_dir.mkdir(parents=True)
    
    os.environ["WHISPER_MODEL_DIR"] = str(save_dir)
    model = whisper.load_model(model_name, download_root=save_dir)
    print(f"Whisper model {model_name} is ready in {save_dir}")
    return model

def download_all_models():
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    try:
        print("Downloading Silero TTS model...")
        silero_dir = models_dir / "silero"
        download_silero_model(silero_dir)
    except Exception as e:
        print(f"Error downloading Silero: {e}")
        print("Trying alternative Silero installation...")
        try:
            from silero import silero_tts
            silero_tts.download_model('ru', 'v3_1_ru', device='cpu', dst_dir=str(silero_dir))
            print(f"Silero model downloaded via alternative method to {silero_dir}")
        except Exception as alt_e:
            print(f"Failed to download Silero: {alt_e}")
    
    print("\nDownloading Whisper model...")
    whisper_dir = models_dir / "whisper"
    download_whisper_model("base", whisper_dir)
    
    print("\nДля TinyLlama выполните вручную:")
    print("git lfs install")
    print("git clone https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0 models/tinyllama")

if __name__ == "__main__":
    download_all_models()