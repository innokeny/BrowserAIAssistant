from pydantic import BaseModel, ConfigDict
import numpy as np

class AudioInput(BaseModel):
    data: np.ndarray
    sample_rate: int
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            np.ndarray: lambda v: v.tolist()
        }

class AudioResult:
    def __init__(self, data: bytes, sample_rate: int, is_success: bool, error_message: str = ""):
        self.data = data
        self.sample_rate = sample_rate
        self.is_success = is_success
        self.error_message = error_message