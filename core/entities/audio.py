from pydantic import BaseModel, ConfigDict
import numpy as np

class AudioInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)  
    data: np.ndarray
    sample_rate: int

class AudioResult:
    def __init__(self, data: bytes, sample_rate: int, is_success: bool, error_message: str = ""):
        self.data = data
        self.sample_rate = sample_rate
        self.is_success = is_success
        self.error_message = error_message