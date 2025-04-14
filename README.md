# Voice Assistant Extention

Расширяемый голосовой ассистент с поддержкой современных ML-моделей (Whisper, Silero, Gemini)

```
.
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
│       ├── popup.css
│       ├── popup.html
│       └── popup.js
├── config
│   ├── _tinyllama.py
│   ├── gemini.py
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
│       ├── _llm_use_cases.py
│       ├── gemini_use_cases.py
│       ├── stt_use_cases.py
│       ├── tts_use_cases.py
│       └── user_use_cases.py
├── infrastructure
│   ├── db
│   │   └── user_repository_impl.py
│   ├── ml_models
│   │   ├── _tinyllama
│   │   │   └── model.py
│   │   ├── silero
│   │   │   └── model.py
│   │   └── whisper
│   │       └── model.py
│   └── web
│       └── controllers
│           ├── _llm_controller.py
│           ├── gemini_controller.py
│           ├── stt_controller.py
│           ├── tts_controller.py
│           └── user_controller.py
├── main.py
├── models
│   ├── silero
│   │   └── v3_1_ru.pt
│   └── whisper
│       ├── base.pt
│       └── small.pt
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
  - Gemini – интеграция с LLM
  - User – управление пользователями
- **Repositories**: Абстракции для работы с хранилищами

### Infrastructure (Инфраструктура)
- **ML Models**: Реализации ML-моделей:
  - Whisper – speech-to-text
  - Silero – text-to-speech 
- **Web**: FastAPI-контроллеры для:
  - Речевых операций (STT/TTS)
  - Работы с Gemini
  - Пользовательского API
- **DB**: Реализация хранилища данных

### Конфигурация
- Централизованное управление параметрами:
  - Пути к моделям
  - Настройки API-ключей
  - Параметры генерации

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
- TS: Silero v3 (русский язык)
- LLM: Google Gemini
- Web: FastAPI, Uvicorn