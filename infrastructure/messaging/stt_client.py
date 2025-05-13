from typing import Any, Callable
from .rabbitmq_client import RabbitMQClient
from .config import rabbitmq_settings


class STTRabbitMQClient(RabbitMQClient):
    """Клиент RabbitMQ для операций преобразования речи в текст (STT)."""
    
    async def publish_stt_request(self, audio_data: Any) -> None:
        """Публикация запроса на преобразование речи в текст в очередь STT."""
        await self.publish_message(
            rabbitmq_settings.STT_QUEUE,
            {
                "type": "stt_request",
                "data": audio_data
            }
        )
    
    async def consume_stt_requests(self, callback: Callable[[Any], None]) -> None:
        """Начало потребления запросов на преобразование речи в текст."""
        await self.consume_messages(
            rabbitmq_settings.STT_QUEUE,
            callback
        ) 