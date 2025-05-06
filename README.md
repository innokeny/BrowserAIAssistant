# Voice Assistant Extention

Расширяемый голосовой ассистент с поддержкой современных ML-моделей (Whisper, Silero, Gemini, Qwen)

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
│   ├── gemini.py
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
│   │   └── user_repository.py
│   └── use_cases
│       ├── gemini_use_cases.py
│       ├── qwen_use_cases.py
│       ├── stt_use_cases.py
│       ├── tts_use_cases.py
│       └── user_use_cases.py
├── docker-compose.yml
├── infrastructure
│   ├── db
│   │   ├── db_connection.py
│   │   ├── init_db.py
│   │   ├── models.py
│   │   ├── quota_repository_impl.py
│   │   ├── request_history_repository_impl.py
│   │   ├── resource_manager.py
│   │   ├── test_connections.py
│   │   └── user_repository_impl.py
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
│       ├── fastapi_app.py
│       └── controllers
│           ├── gemini_controller.py
│           ├── qwen_controller.py
│           ├── stt_controller.py
│           ├── tts_controller.py
│           └── user_controller.py
├── requirements.txt
└── scripts
    └── download_models.py
```

## Описание архитектуры

### Core (Ядро)
- **Entities**: Базовые DTO-объекты:
  - `Audio` – аудиоданные и метаинформация
  - `Text` – результаты обработки текста
  - `User` – данные пользователя
- **Use Cases**: Бизнес-логика:
  - STT/TTS – преобразование речи в текст и обратно
  - Gemini/Qwen – интеграция с LLM
  - User – управление пользователями
- **Repositories**: Абстракции для работы с хранилищами

### Infrastructure (Инфраструктура)
- **ML Models**: Реализации ML-моделей:
  - Whisper – speech-to-text
  - Silero – text-to-speech
  - Qwen – large language model
- **Web**: FastAPI-контроллеры для:
  - Речевых операций (STT/TTS)
  - Работы с LLM (Gemini/Qwen)
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
1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Загрузите модели:
```bash
python scripts/download_models.py
```

3. Запустите приложение:
```bash
python main.py
```

API будет доступно на http://localhost:8000/docs

### Поддерживаемые технологии
- STT: OpenAI Whisper (base/small)
- TTS: Silero v3 (русский язык)
- LLM: Google Gemini, Qwen
- Web: FastAPI, Uvicorn
- Messaging: RabbitMQ
- DB: PostgreSQL, Redis