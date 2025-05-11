from typing import Any, Callable
from .rabbitmq_client import RabbitMQClient
from .config import rabbitmq_settings


class STTRabbitMQClient(RabbitMQClient):
    """RabbitMQ client for STT operations."""
    
    async def publish_stt_request(self, audio_data: Any) -> None:
        """Publish STT request to queue."""
        await self.publish_message(
            rabbitmq_settings.STT_QUEUE,
            {
                "type": "stt_request",
                "data": audio_data
            }
        )
    
    async def consume_stt_requests(self, callback: Callable[[Any], None]) -> None:
        """Start consuming STT requests."""
        await self.consume_messages(
            rabbitmq_settings.STT_QUEUE,
            callback
        ) 