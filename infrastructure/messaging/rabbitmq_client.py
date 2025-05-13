import json
import aio_pika
from typing import Any, Callable, Optional
from .config import rabbitmq_settings


class RabbitMQClient:
    """Базовый класс для операций с RabbitMQ."""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None  # Соединение с RabbitMQ
        self.channel: Optional[aio_pika.Channel] = None  # Канал для обмена сообщениями
        self.exchange: Optional[aio_pika.Exchange] = None  # Обменник для маршрутизации
        
    async def connect(self) -> None:
        """Установка соединения с сервером RabbitMQ."""
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
        """Закрытие соединения с RabbitMQ."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None
            self.exchange = None
    
    async def publish_message(self, queue_name: str, message: Any) -> None:
        """Публикация сообщения в указанную очередь."""
        if not self.connection:
            await self.connect()
            
        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(self.exchange, queue_name)
        
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
        """Начало потребления сообщений из указанной очереди."""
        if not self.connection:
            await self.connect()
            
        await self.channel.set_qos(prefetch_count=prefetch_count)
        
        queue = await self.channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(self.exchange, queue_name)
        
        await queue.consume(
            lambda message: self._process_message(message, callback)
        )
    
    async def _process_message(
        self,
        message: aio_pika.IncomingMessage,
        callback: Callable[[Any], None]
    ) -> None:
        """Обработка входящего сообщения."""
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                await callback(data)
            except Exception as e:
                print(f"Ошибка обработки сообщения: {e}")
                await message.reject(requeue=True) 