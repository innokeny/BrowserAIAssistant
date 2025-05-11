from typing import Optional
from pydantic import BaseModel

class LLMInput:
    def __init__(self, prompt: str):
        self.prompt = prompt

class LLMResult(BaseModel):
    text: str
    is_success: bool
    error_message: Optional[str] = None

    @classmethod
    def error(cls, error_msg: str) -> "LLMResult":
        return cls(
            text="",
            is_success=False,
            error_message=error_msg
        )

class TranscriptionResult:
    def __init__(self, text: str, is_success: bool, error_message: str = ""):
        self.text = text
        self.is_success = is_success
        self.error_message = error_message
        
class TextInput:
    def __init__(self, text: str):
        self.text = text