import json
import aio_pika
from typing import Any, Callable, Optional
from .config import rabbitmq_settings

class RabbitMQClient:
    """Base class for RabbitMQ operations."""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        
    async def connect(self) -> None:
        """Establish connection to RabbitMQ server."""
        if not self.connection:
            self.connection = await aio_pika.connect_robust(
                host=rabbitmq_settings.HOST,
                port=rabbitmq_settings.PORT,
                login=rabbitmq_settings.USER,
                password=rabbitmq_settings.PASSWORD,
                virtualhost=rabbitmq_settings.VHOST
            )
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                rabbitmq_settings.MAIN_EXCHANGE,
                aio_pika.ExchangeType.DIRECT
            )
    
    async def close(self) -> None:
        """Close RabbitMQ connection."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None
    
    async def publish_message(self, queue_name: str, message: Any) -> None:
        """Publish message to specified queue."""
        if not self.connection:
            await self.connect()
            
        # Declare queue
        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        # Bind queue to exchange
        await queue.bind(self.exchange, queue_name)
        
        # Publish message
        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )
    
    async def consume_messages(
        self,
        queue_name: str,
        callback: Callable[[Any], None],
        prefetch_count: int = 1
    ) -> None:
        """Start consuming messages from specified queue."""
        if not self.connection:
            await self.connect()
            
        # Set prefetch count
        await self.channel.set_qos(prefetch_count=prefetch_count)
        
        # Declare queue
        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        # Bind queue to exchange
        await queue.bind(self.exchange, queue_name)
        
        # Start consuming
        await queue.consume(
            lambda message: self._process_message(message, callback)
        )
    
    async def _process_message(
        self,
        message: aio_pika.IncomingMessage,
        callback: Callable[[Any], None]
    ) -> None:
        """Process incoming message."""
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                await callback(data)
            except Exception as e:
                # Log error and reject message
                print(f"Error processing message: {e}")
                await message.reject(requeue=True) 