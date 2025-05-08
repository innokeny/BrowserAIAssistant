from core.entities.text import LLMInput, LLMResult
from infrastructure.ml_models.qwen.model import QwenModel
from typing import Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class QwenUseCase:
    def __init__(self):
        logger.info("Initializing Qwen model")
        self.model = QwenModel()
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
            
            response = await self.model.generate(
                input_data=input_data,
                max_length=max_length or 512,
                temperature=temperature
            )
            
            logger.debug(f"Received response: {response.text[:100]}...")
            return response
            
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
        max_length: Optional[int] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[LLMResult, None]:
        try:
            logger.debug(
                f"Starting streaming generation: {input_data.prompt[:50]}..."
                f" | max_length={max_length}, temp={temperature}"
            )
            
            async for chunk in self.model.generate_stream(
                input_data=input_data,
                max_length=max_length or 512,
                temperature=temperature
            ):
                yield chunk
            
        except Exception as e:
            logger.error(f"Streaming generation error: {str(e)}", exc_info=True)
            yield LLMResult(
                text="",
                is_success=False,
                error_message=str(e)
            ) 