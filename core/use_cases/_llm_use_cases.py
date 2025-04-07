from core.entities.text import LLMInput, LLMResult
from typing import Optional

class LLMUseCase:
    def __init__(self, llm_model):
        self.llm_model = llm_model

    async def generate(
        self,
        input_data: LLMInput,
        max_length: Optional[int] = None,
        temperature: float = 0.7
    ) -> LLMResult:
        try:
            generated_text = await self.llm_model.generate(
                prompt=input_data.prompt,
                max_length=max_length,
                temperature=temperature
            )
            return LLMResult(
                text=generated_text,
                is_success=True
            )
        except Exception as e:
            return LLMResult(
                text="",
                is_success=False,
                error_message=str(e)
            )