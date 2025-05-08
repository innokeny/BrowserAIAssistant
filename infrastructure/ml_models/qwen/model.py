import logging
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import AsyncGenerator
import torch
import os

from config.qwen import QWEN_MODEL_DIR
from core.entities.text import LLMInput, LLMResult

logger = logging.getLogger(__name__)

class QwenModel:
    def __init__(self, model_name: str = None):
        # Use local model path if available, otherwise use default
        self.model_name = model_name or os.getenv("QWEN_MODEL_PATH", "models/qwen")
        logger.info(f"Loading Qwen model from: {self.model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            local_files_only=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            trust_remote_code=True,
            local_files_only=True
        )
        self.model.eval()

    def _format_prompt(self, prompt: str) -> str:
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
        
        return f"{system_prompt}\n\nЧеловек: {prompt}\n\nАссистент:"

    def _clean_response(self, response: str) -> str:
        # Очищаем ответ от возможных технических деталей
        response = response.replace("```", "").strip()
        response = response.replace("python", "").strip()
        response = response.replace("code:", "").strip()
        
        # Удаляем любые оставшиеся технические маркеры и нормализуем пробелы
        response = ' '.join(response.split())
        
        # Ограничиваем длину ответа
        if len(response) > 200:
            response = response[:200].rsplit(' ', 1)[0] + '...'
        
        return response

    async def generate(
        self,
        input_data: LLMInput,
        max_length: int = 100,
        temperature: float = 0.7
    ) -> LLMResult:
        """Generate text using Qwen model"""
        try:
            # Prepare input
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": input_data.prompt}
            ]
            
            # Tokenize input
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                return_tensors="pt"
            ).to(self.model.device)
            
            # Generate text
            with torch.no_grad():
                output_ids = self.model.generate(
                    input_ids,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            
            # Decode output
            output_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            
            return LLMResult(
                text=output_text,
                is_success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}", exc_info=True)
            return LLMResult(
                text="",
                is_success=False,
                error_message=str(e)
            )

    async def generate_stream(
        self,
        input_data: LLMInput,
        max_length: int = 100,
        temperature: float = 0.7
    ) -> AsyncGenerator[LLMResult, None]:
        """Generate text stream using Qwen model"""
        try:
            # Prepare input
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": input_data.prompt}
            ]
            
            # Tokenize input
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                return_tensors="pt"
            ).to(self.model.device)
            
            # Generate text stream
            with torch.no_grad():
                for output_ids in self.model.generate(
                    input_ids,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    stream=True
                ):
                    # Decode output
                    output_text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
                    
                    yield LLMResult(
                        text=output_text,
                        is_success=True,
                        error_message=None
                    )
                    
        except Exception as e:
            logger.error(f"Streaming generation error: {str(e)}", exc_info=True)
            yield LLMResult(
                text="",
                is_success=False,
                error_message=str(e)
            )


