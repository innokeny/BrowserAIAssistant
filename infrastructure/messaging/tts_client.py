from typing import Any, Callable
from .rabbitmq_client import RabbitMQClient
from .config import rabbitmq_settings


class TTSRabbitMQClient(RabbitMQClient):
    """RabbitMQ client for TTS operations."""
    
    async def publish_tts_request(self, text_data: Any) -> None:
        """Publish TTS request to queue."""
        await self.publish_message(
            rabbitmq_settings.TTS_QUEUE,
            {
                "type": "tts_request",
                "data": text_data
            }
        )
    
    async def consume_tts_requests(self, callback: Callable[[Any], None]) -> None:
        """Start consuming TTS requests."""
        await self.consume_messages(
            rabbitmq_settings.TTS_QUEUE,
            callback
        ) 