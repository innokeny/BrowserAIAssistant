import logging
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

from config.qwen import QWEN_MODEL_DIR

logger = logging.getLogger(__name__)

class QwenModel:
    def __init__(self, model_dir: Path = QWEN_MODEL_DIR):
        self.model_dir = model_dir
        self.model = None
        self.tokenizer = None
        self._load_model(model_dir)

    def _load_model(self, model_dir: Path):
        try:
            logger.info(f"Loading Qwen model from {model_dir}")
            
            if not model_dir.exists():
                raise FileNotFoundError(f"Model directory not found: {model_dir}")
                
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_dir,
                trust_remote_code=True,
                padding_side="left"
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info("Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_dir,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype="auto"
            )
            
            if self.model is None:
                raise RuntimeError("Model failed to load")
                
            logger.info("Qwen model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Qwen model: {str(e)}", exc_info=True)
            raise

    def generate(self, prompt: str, max_length: int = 128, temperature: float = 0.7) -> str:
        try:
            if self.model is None or self.tokenizer is None:
                raise RuntimeError("Model not initialized")
                
            logger.info(f"Generating response for prompt: {prompt[:50]}...")
            
            system_prompt = """Ты - дружелюбный ассистент. Правила общения:
            1. Отвечай кратко (max_length: 256), 1 предложение, будто ведешь диалог с человеком
            2. Используй простой разговорный язык
            3. Не используй технические термины
            4. Не генерируй код
            5. Отвечай на русском языке
            6. Не задавай уточняющих вопросов
            7. Не используй формальные обороты
            8. Не повторяйся
            9. Не используй эмодзи"""
            
            formatted_prompt = f"{system_prompt}\n\nЧеловек: {prompt}\n\nАссистент:"
            
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
            input_length = len(inputs.input_ids[0])
            
            logger.debug(f"Input length: {input_length} tokens")
            
            # Генерируем ответ
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.2,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=3
            )
            
            # Декодируем ответ
            response = self.tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
            
            # Очищаем ответ от возможных технических деталей
            response = response.replace("```", "").strip()
            response = response.replace("python", "").strip()
            response = response.replace("code:", "").strip()
            
            # Удаляем любые оставшиеся технические маркеры и нормализуем пробелы
            response = ' '.join(response.split())
            
            # Ограничиваем длину ответа
            if len(response) > 200:
                response = response[:200].rsplit(' ', 1)[0] + '...'
            
            logger.info(f"Generated response: {response[:50]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}", exc_info=True)
            raise


