from core.entities.audio import AudioInput
from core.entities.text import TranscriptionResult
from typing import Optional

class SpeechToTextUseCase:
    def __init__(self, stt_model):
        self.stt_model = stt_model

    async def transcribe(self, audio_input: AudioInput, language: Optional[str] = None) -> TranscriptionResult:
        try:
            text = await self.stt_model.transcribe(
                audio_data=audio_input.data,
                sample_rate=audio_input.sample_rate,
                language=language
            )
            return TranscriptionResult(text=text, is_success=True)
        except Exception as e:
            return TranscriptionResult(
                text="",
                is_success=False,
                error_message=f"Transcription failed: {str(e)}"
            )