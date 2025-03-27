Voice Assistant Extention

```
│
├── core/
│   ├── entities/
│   │   ├── audio.py          # Аудио сущности
│   │   └── text.py           # Текстовые сущности
│   ├── use_cases/
│   │   ├── stt_use_cases.py  # Сценарии для распознавания речи
│   │   ├── tts_use_cases.py  # Сценарии для синтеза речи
│   │   └── llm_use_cases.py  # Сценарии для языковой модели
│   └── repositories/
│       ├── audio_repository.py
│       └── text_repository.py
│
├── infrastructure/
│   ├── ml_models/            # Модели ML
│   │   ├── tinyllama/        # TinyLlama
│   │   │   ├── model.py      # Обертка для модели
│   │   │   └── utils.py      # Вспомогательные функции
│   │   ├── silero/           # Silero TTS
│   │   │   ├── model.py
│   │   │   └── utils.py
│   │   └── whisper/          # Whisper STT
│   │       ├── model.py
│   │       └── utils.py
│   ├── db/
│   └── web/
│       ├── controllers/
│       │   ├── stt_controller.py  # API для распознавания речи
│       │   ├── tts_controller.py  # API для синтеза речи
│       │   └── llm_controller.py  # API для языковой модели
│       └── middlewares/      # Промежуточное ПО
│
├── config/
│   ├── settings.py           # Основные настройки
│   ├── tinyllama.py          # Конфиг TinyLlama
│   ├── silero.py             # Конфиг Silero
│   └── whisper.py            # Конфиг Whisper
│
├── static/                   # Статические файлы (аудио и т.д.)
│
├── requirements/
│   ├── base.txt              # Базовые зависимости
│   ├── ml.txt                # ML зависимости
│   └── dev.txt               # Для разработки
│
├── scripts/                  # Скрипты для загрузки моделей
│   ├── download_models.py
│   └── prepare_environment.py
│
└── main.py                   # Точка входа

```


Описание слоев

Core (Ядро):
- entities: Содержит бизнес-сущности (например, User), которые представляют основные объекты предметной области.
- use_cases: Содержит сценарии использования (бизнес-логику), которые описывают, как приложение должно работать.
- repositories: Определяет интерфейсы для работы с данными (например, UserRepository). Это абстракции, которые не зависят от конкретной реализации.


Infrastructure (Инфраструктура):
- db: Реализация репозиториев (например, UserRepositoryImpl), которая работает с базой данных.
- web: Веб-слой, который обрабатывает HTTP-запросы и взаимодействует с ядром через контроллеры.

Config (Конфигурация):
- main.py:  Точка входа в приложение, где инициализируются зависимости и запускается приложение.
