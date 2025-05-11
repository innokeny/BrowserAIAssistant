from pydantic import BaseModel
# from typing import Optional
# from datetime import datetime

# class QwenRequest(BaseModel):
#     prompt: str
#     max_tokens: Optional[int] = Field(default=1000, ge=1, le=4000)
#     temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)

# class QwenResponse(BaseModel):
#     response: str
#     tokens_used: int
#     created_at: str

class QwenHistory(BaseModel):
    id: int
    prompt: str
    response: str
    tokens_used: int
    created_at: str 