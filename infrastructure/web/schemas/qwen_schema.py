from pydantic import BaseModel

class QwenHistory(BaseModel):
    id: int
    prompt: str
    response: str
    tokens_used: int
    created_at: str 