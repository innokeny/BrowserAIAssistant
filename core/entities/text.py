class LLMInput:
    def __init__(self, prompt: str):
        self.prompt = prompt

class LLMResult:
    def __init__(self, text: str, is_success: bool, error_message: str = ""):
        self.text = text
        self.is_success = is_success
        self.error_message = error_message

class TranscriptionResult:
    def __init__(self, text: str, is_success: bool, error_message: str = ""):
        self.text = text
        self.is_success = is_success
        self.error_message = error_message

class TextInput:
    def __init__(self, text: str):
        self.text = text