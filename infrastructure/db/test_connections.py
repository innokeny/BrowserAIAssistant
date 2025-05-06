import asyncio
import aio_pika
import redis
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.messaging.config import rabbitmq_settings

async def test_rabbitmq():
    """Test RabbitMQ connection and basic operations."""
    print("Testing RabbitMQ connection...")
    try:
        # Connect to RabbitMQ
        connection = await aio_pika.connect_robust(
            host=rabbitmq_settings.HOST,
            port=rabbitmq_settings.PORT,
            login=rabbitmq_settings.USER,
            password=rabbitmq_settings.PASSWORD,
            virtualhost=rabbitmq_settings.VHOST
        )
        
        # Create channel
        channel = await connection.channel()
        
        # Declare queue
        queue = await channel.declare_queue("test_queue", durable=True)
        
        # Send test message
        await channel.default_exchange.publish(
            aio_pika.Message(
                body="Test message".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="test_queue"
        )
        
        # Receive message
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print(f"Received message: {message.body.decode()}")
                    break
        
        # Clean up
        await connection.close()
        print("✅ RabbitMQ test passed!")
        
    except Exception as e:
        print(f"❌ RabbitMQ test failed: {str(e)}")

def test_redis():
    """Test Redis connection and basic operations."""
    print("\nTesting Redis connection...")
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test set and get
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        
        if value.decode() == 'test_value':
            print("✅ Redis test passed!")
        else:
            print("❌ Redis test failed: Value mismatch")
            
    except Exception as e:
        print(f"❌ Redis test failed: {str(e)}")

async def main():
    await test_rabbitmq()
    test_redis()

if __name__ == "__main__":
    asyncio.run(main()) 