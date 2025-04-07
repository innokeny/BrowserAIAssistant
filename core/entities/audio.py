class AudioInput:
    def __init__(self, data, sample_rate: int):
        self.data = data
        self.sample_rate = sample_rate

class AudioResult:
    def __init__(self, data: bytes, sample_rate: int, is_success: bool, error_message: str = ""):
        self.data = data
        self.sample_rate = sample_rate
        self.is_success = is_success
        self.error_message = error_message