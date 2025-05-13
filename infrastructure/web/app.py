from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from infrastructure.web.controllers.credit_controller import router as credit_router
from infrastructure.web.controllers.analytics_controller import router as analytics_router
from infrastructure.web.controllers.user_controller import router as user_router
from infrastructure.web.controllers.qwen_controller import router as qwen_router
from infrastructure.web.controllers.stt_controller import router as stt_router
from infrastructure.web.controllers.tts_controller import router as tts_router
from infrastructure.db.init_db import init_db, wait_for_db
from infrastructure.messaging.message_service import MessageService
from infrastructure.messaging.queue_processor import QueueProcessor
import asyncio
import logging

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    expose_headers=["*"],
    allow_headers=["*", "Authorization"] 
)

app.include_router(credit_router)
app.include_router(analytics_router)
app.include_router(user_router)
app.include_router(stt_router)
app.include_router(tts_router)
app.include_router(qwen_router)

@app.on_event("startup")
async def startup_event():
    """
    Initialize the database and message service when the application starts.
    """
    logger.info("Waiting for database to be ready...")
    if wait_for_db():
        logger.info("Database is ready. Initializing...")
        init_db()
        logger.info("Database initialization complete.")
    else:
        logger.error("Failed to connect to the database. Application may not function correctly.")

    # Инициализация сервиса сообщений
    try:
        message_service = MessageService()
        await message_service.initialize()
        logger.info("Message service initialized successfully")

        # Запуск обработчика очередей
        queue_processor = QueueProcessor()
        asyncio.create_task(queue_processor.start_processing())
        logger.info("Queue processor started")
    except Exception as e:
        logger.error(f"Failed to initialize message service: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup when the application shuts down.
    """
    try:
        message_service = MessageService()
        await message_service.close()
        logger.info("Message service connections closed")
    except Exception as e:
        logger.error(f"Error closing message service connections: {e}")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.get("/")
def read_root():
    return {"status": "ok"}
