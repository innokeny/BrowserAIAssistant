# Voice Assistant Extention

Расширяемый голосовой ассистент с поддержкой современных ML-моделей (Whisper, Silero, Qwen)

```
.
├── Dockerfile
├── README.md
├── app.log
├── browser-extension
│   ├── background
│   │   └── background.js
│   ├── content
│   │   └── content.js
│   ├── icons
│   │   ├── icon-128.png
│   │   ├── icon-48.png
│   │   └── mic-icon.png
│   ├── manifest.json
│   └── popup
│       ├── core
│       │   ├── command-router.js
│       │   ├── scenarios
│       │   │   ├── base-scenario.js
│       │   │   ├── llm-chat.js
│       │   │   ├── new-tab-scenario.js
│       │   │   ├── scroll.js
│       │   │   ├── search-panel.css
│       │   │   └── search.js
│       │   └── services
│       │       ├── llm-service.js
│       │       ├── recorder.js
│       │       ├── stt-service.js
│       │       └── tts-service.js
│       ├── popup.css
│       ├── popup.html
│       └── popup.js
├── config
│   ├── qwen.py
│   ├── settings.py
│   ├── silero.py
│   └── whisper.py
├── core
│   ├── entities
│   │   ├── audio.py
│   │   ├── text.py
│   │   └── user.py
│   ├── repositories
│   │   ├── credit_repository_impl.py
│   │   ├── qwen_repository_impl.py
│   │   ├── request_history_repository_impl.py
│   │   ├── user_repository.py
│   │   └── user_repository_impl.py
│   └── use_cases
│       ├── qwen_use_cases.py
│       ├── stt_use_cases.py
│       ├── tts_use_cases.py
│       └── user_use_cases.py
├── docker-compose.yml
├── infrastructure
│   ├── db
│   │   ├── db_connection.py
│   │   ├── init_db.py
│   │   ├── models
│   │   │   ├── silero
│   │   │   └── whisper
│   │   └── models.py
│   ├── messaging
│   │   ├── config.py
│   │   ├── llm_client.py
│   │   ├── rabbitmq_client.py
│   │   ├── stt_client.py
│   │   └── tts_client.py
│   ├── ml_models
│   │   ├── qwen
│   │   │   └── model.py
│   │   ├── silero
│   │   │   └── model.py
│   │   └── whisper
│   │       └── model.py
│   └── web
│       ├── app.py
│       ├── auth_service.py
│       ├── controllers
│       │   ├── analytics_controller.py
│       │   ├── credit_controller.py
│       │   ├── qwen_controller.py
│       │   ├── stt_controller.py
│       │   ├── tts_controller.py
│       │   └── user_controller.py
│       └── schemas
│           ├── __init__.py
│           ├── credit_schema.py
│           ├── qwen_schema.py
│           └── user_schema.py
├── requirements.txt
├── scripts
│   └── download_models.py
└── tests
    └── unit
        ├── test_analytics_controller.py
        ├── test_auth_service.py
        ├── test_credit_controller.py
        ├── test_credit_repository.py
        ├── test_qwen_controller.py
        ├── test_resource_manager.py
        └── test_user_controller.py
```
## Описание архитектуры

### Core (Ядро)
- **Entities**: Базовые DTO-объекты:
  - `Audio` – аудиоданные и метаинформация
  - `Text` – результаты обработки текста
  - `User` – данные пользователя
- **Use Cases**: Бизнес-логика:
  - STT/TTS – преобразование речи в текст и обратно
  - Qwen – интеграция с LLM
  - User – управление пользователями
- **Repositories**: Абстракции для работы с хранилищами

### Infrastructure (Инфраструктура)
- **ML Models**: Реализации ML-моделей:
  - Whisper – speech-to-text
  - Silero – text-to-speech
  - Qwen – large language model
- **Web**: FastAPI-контроллеры для:
  - Речевых операций (STT/TTS)
  - Работы с LLM 
  - Пользовательского API
- **DB**: Реализация хранилища данных
- **Messaging**: Асинхронная коммуникация через RabbitMQ

### Browser Extension
- **Core**: Основная логика расширения
  - Command Router – маршрутизация команд
  - Scenarios – сценарии взаимодействия
  - Services – сервисы для работы с API
- **UI**: Пользовательский интерфейс
  - Popup – всплывающее окно
  - Search Panel – панель поиска

### Конфигурация
- Централизованное управление параметрами:
  - Пути к моделям
  - Настройки API-ключей
  - Параметры генерации
  - Конфигурация RabbitMQ

## Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Git

### Запуск приложения
1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd BrowserAIAssistant
```

2. Запустите приложение через Docker Compose:
```bash
docker-compose up -d
```

Это запустит:
- FastAPI приложение на порту 8000
- PostgreSQL на порту 5433
- Redis на порту 6379
- RabbitMQ на порту 5672
- pgAdmin на порту 8080

3. Проверьте статус контейнеров:
```bash
docker-compose ps
```

4. API будет доступно на http://localhost:8000/docs

### Остановка приложения
```bash
docker-compose down
```

### Просмотр логов
```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f redis
docker-compose logs -f rabbitmq
```

### Переменные окружения
Все необходимые переменные окружения уже настроены в `docker-compose.yml`. При необходимости их можно изменить в этом файле.

### Поддерживаемые технологии
- STT: OpenAI Whisper (base/small)
- TTS: Silero v3 (русский язык)
- LLM: Qwen
- Web: FastAPI, Uvicorn
- Messaging: RabbitMQ
- DB: PostgreSQL, Redis
