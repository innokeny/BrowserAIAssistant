from core.entities.text import LLMInput, LLMResult
import google.generativeai as genai
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GeminiUseCase:
    def __init__(self, model_name: str):
        logger.info(f"Initializing Gemini model: {model_name}")
        self.model = genai.GenerativeModel(model_name)
        logger.debug("Model initialized successfully")
    
    async def generate(
        self,
        input_data: LLMInput,
        max_length: Optional[int] = None,
        temperature: float = 0.7
    ) -> LLMResult:
        try:
            logger.debug(
                f"Starting generation: {input_data.prompt[:50]}..."
                f" | max_length={max_length}, temp={temperature}"
            )
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_length
            }

            response = await self.model.generate_content_async(
                input_data.prompt,
                generation_config=generation_config
            )
            
            logger.debug(f"Received response: {response.text[:100]}...")
            return LLMResult(
                text=response.text,
                is_success=True
            )
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}", exc_info=True)
            return LLMResult(
                text="",
                is_success=False,
                error_message=str(e)
            )