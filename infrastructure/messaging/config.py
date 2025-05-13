from pydantic_settings import BaseSettings
import os


class RabbitMQSettings(BaseSettings):
    """Настройки подключения к RabbitMQ."""
    HOST: str = os.getenv("RABBITMQ_HOST", "localhost")  # Хост RabbitMQ сервера
    PORT: int = int(os.getenv("RABBITMQ_PORT", "5672"))  # Порт для AMQP протокола
    USER: str = os.getenv("RABBITMQ_USER", "admin")  # Имя пользователя
    PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "admin")  # Пароль
    VHOST: str = os.getenv("RABBITMQ_VHOST", "/")  # Виртуальный хост
    
    # Очереди для различных типов запросов
    STT_QUEUE: str = "stt_requests"  # Очередь для запросов преобразования речи в текст
    TTS_QUEUE: str = "tts_requests"  # Очередь для запросов преобразования текста в речь
    LLM_QUEUE: str = "llm_requests"  # Очередь для запросов к языковой модели
    
    MAIN_EXCHANGE: str = "main_exchange"  # Основной обменник для маршрутизации сообщений
    
    class Config:
        env_prefix = "RABBITMQ_"

rabbitmq_settings = RabbitMQSettings() 