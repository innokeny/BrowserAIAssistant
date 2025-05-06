from pydantic_settings import BaseSettings
import os

class RabbitMQSettings(BaseSettings):
    """RabbitMQ connection settings."""
    HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    USER: str = os.getenv("RABBITMQ_USER", "admin")
    PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "admin")
    VHOST: str = os.getenv("RABBITMQ_VHOST", "/")
    
    # Queue names
    STT_QUEUE: str = "stt_requests"
    TTS_QUEUE: str = "tts_requests"
    LLM_QUEUE: str = "llm_requests"
    
    # Exchange names
    MAIN_EXCHANGE: str = "main_exchange"
    
    class Config:
        env_prefix = "RABBITMQ_"

rabbitmq_settings = RabbitMQSettings() 