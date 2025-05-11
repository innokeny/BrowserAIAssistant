import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
from core.entities.text import LLMInput, LLMResult


logger = logging.getLogger(__name__)

class QwenModel:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("QWEN_MODEL_PATH", "models/qwen")
        logger.info(f"Loading Qwen model from: {self.model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            local_files_only=True,
            pad_token="<|endoftext|>",  
            padding_side="left"
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype=torch.bfloat16
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
        9. Не используй эмодзи
        10. Цифры пиши словами"""
        
        return f"<|im_start|>user\n{system_prompt}\n\nЧеловек: {prompt}\n<|im_end|>\n<|im_start|>assistant\n"

    def _clean_response(self, response: str) -> str:
        response = response.replace("```", "").strip()
        response = response.replace("python", "").strip()
        response = response.replace("code:", "").strip()
        
        response = ' '.join(response.split())
        
        if len(response) > 256:
            response = response[:256].rsplit(' ', 1)[0] + '...'
        
        return response

    async def generate(
        self,
        input_data: LLMInput,
        max_length: int = 256,
        temperature: float = 0.7
    ) -> LLMResult:
        try:
            formatted_prompt = self._format_prompt(input_data.prompt)
            
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                return_attention_mask=True
            ).to(self.model.device)

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
                do_sample=True
            )
            
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            if "</think>" in full_response:
                response = full_response.split("</think>")[-1].strip()
            elif "<|im_start|>assistant\n" in full_response:
                response = full_response.split("<|im_start|>assistant\n")[-1].split("<|im_end|>")[0].strip()
            else:
                logger.warning("Response does not contain expected markers. Returning full response.")
                response = full_response.strip()

            response = self._clean_response(response)

            logger.info(f"Generated response: {response}")
            
            return LLMResult(
                text=response,
                is_success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}", exc_info=True)
            return LLMResult.error(str(e))
    
   