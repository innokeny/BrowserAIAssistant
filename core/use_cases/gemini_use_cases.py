from core.entities.text import LLMInput, LLMResult
import google.generativeai as genai
from typing import Optional

class GeminiUseCase:
    def __init__(self, model_name: str):
        self.model = genai.GenerativeModel(model_name)
    
    async def generate(
        self,
        input_data: LLMInput,
        max_length: Optional[int] = None,
        temperature: float = 0.7
    ) -> LLMResult:
        try:
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_length
            }

            response = await self.model.generate_content_async(
                input_data.prompt,
                generation_config=generation_config
            )
            
            return LLMResult(
                text=response.text,
                is_success=True
            )
        except Exception as e:
            return LLMResult(
                text="",
                is_success=False,
                error_message=str(e)
            )