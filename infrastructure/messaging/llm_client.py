from typing import Any, Callable
from .rabbitmq_client import RabbitMQClient
from .config import rabbitmq_settings

class LLMRabbitMQClient(RabbitMQClient):
    """RabbitMQ client for LLM operations."""
    
    async def publish_llm_request(self, prompt_data: Any) -> None:
        """Publish LLM request to queue."""
        await self.publish_message(
            rabbitmq_settings.LLM_QUEUE,
            {
                "type": "llm_request",
                "data": prompt_data
            }
        )
    
    async def consume_llm_requests(self, callback: Callable[[Any], None]) -> None:
        """Start consuming LLM requests."""
        await self.consume_messages(
            rabbitmq_settings.LLM_QUEUE,
            callback
        ) 