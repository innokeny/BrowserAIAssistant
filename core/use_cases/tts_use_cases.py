from core.entities.text import TextInput
from core.entities.audio import AudioResult
from typing import Optional

class TextToSpeechUseCase:
    def __init__(self, tts_model):
        self.tts_model = tts_model

    async def synthesize(
        self,
        text_input: TextInput,
        speaker: Optional[str] = None,
        sample_rate: int = 24000
    ) -> AudioResult:
        try:
            audio_data = await self.tts_model.synthesize(
                text=text_input.text,
                speaker=speaker,
                sample_rate=sample_rate
            )
            return AudioResult(
                data=audio_data,
                sample_rate=sample_rate,
                is_success=True
            )
        except Exception as e:
            return AudioResult(
                data=b'',
                sample_rate=0,
                is_success=False,
                error_message=str(e)
            )