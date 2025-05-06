from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Импорт middleware CORS
from infrastructure.web.controllers.user_controller import router as user_router
from infrastructure.web.controllers.stt_controller import router as stt_router
from infrastructure.web.controllers.tts_controller import router as tts_router
# from infrastructure.web.controllers.gemini_controller import router as gemini_router
from infrastructure.web.controllers.qwen_controller import router as qwen_router

import logging
import os
import sys
from infrastructure.db.init_db import init_db, wait_for_db


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Разрешить все расширения Chrome
        "moz-extension://*",     # Разрешить все расширения Firefox
        "http://localhost",      # Для локальной разработки
        "http://127.0.0.1"       # Альтернативный localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],         # Разрешить все методы (GET, POST и т.д.)
    allow_headers=["*"],         # Разрешить все заголовки
    expose_headers=["*"]         # Показывать все заголовки в ответе
)

# Подключение роутеров
app.include_router(user_router)
app.include_router(stt_router)
app.include_router(tts_router)
# app.include_router(gemini_router)
app.include_router(qwen_router)

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """
    Initialize the database when the application starts.
    """
    logger.info("Waiting for database to be ready...")
    if wait_for_db():
        logger.info("Database is ready. Initializing...")
        init_db()
        logger.info("Database initialization complete.")
    else:
        logger.error("Failed to connect to the database. Application may not function correctly.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)