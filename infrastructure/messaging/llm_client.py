from typing import Any, Callable
from .rabbitmq_client import RabbitMQClient
from .config import rabbitmq_settings


class LLMRabbitMQClient(RabbitMQClient):
    """Клиент RabbitMQ для операций с языковой моделью (LLM)."""
    
    async def publish_llm_request(self, prompt_data: Any) -> None:
        """Публикация запроса к языковой модели в очередь LLM."""
        await self.publish_message(
            rabbitmq_settings.LLM_QUEUE,
            {
                "type": "llm_request",
                "data": prompt_data
            }
        )
    
    async def consume_llm_requests(self, callback: Callable[[Any], None]) -> None:
        """Начало потребления запросов к языковой модели."""
        await self.consume_messages(
            rabbitmq_settings.LLM_QUEUE,
            callback
        ) 