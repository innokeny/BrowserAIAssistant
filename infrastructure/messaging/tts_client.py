from typing import Any, Callable
from .rabbitmq_client import RabbitMQClient
from .config import rabbitmq_settings


class TTSRabbitMQClient(RabbitMQClient):
    """Клиент RabbitMQ для операций преобразования текста в речь (TTS)."""
    
    async def publish_tts_request(self, text_data: Any) -> None:
        """Публикация запроса на преобразование текста в речь в очередь TTS."""
        await self.publish_message(
            rabbitmq_settings.TTS_QUEUE,
            {
                "type": "tts_request",
                "data": text_data
            }
        )
    
    async def consume_tts_requests(self, callback: Callable[[Any], None]) -> None:
        """Начало потребления запросов на преобразование текста в речь."""
        await self.consume_messages(
            rabbitmq_settings.TTS_QUEUE,
            callback
        ) 