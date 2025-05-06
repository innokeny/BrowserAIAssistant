from pydantic_settings import BaseSettings

class RabbitMQSettings(BaseSettings):
    """RabbitMQ connection settings."""
    HOST: str = "localhost"
    PORT: int = 5672
    USER: str = "admin"
    PASSWORD: str = "admin"
    VHOST: str = "/"
    
    # Queue names
    STT_QUEUE: str = "stt_requests"
    TTS_QUEUE: str = "tts_requests"
    LLM_QUEUE: str = "llm_requests"
    
    # Exchange names
    MAIN_EXCHANGE: str = "main_exchange"
    
    class Config:
        env_prefix = "RABBITMQ_"

rabbitmq_settings = RabbitMQSettings() 