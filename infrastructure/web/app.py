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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"] 
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
    Initialize the database when the application starts.
    """
    logger.info("Waiting for database to be ready...")
    if wait_for_db():
        logger.info("Database is ready. Initializing...")
        init_db()
        logger.info("Database initialization complete.")
    else:
        logger.error("Failed to connect to the database. Application may not function correctly.")

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

# Add routes
# app.include_router(credit_router, prefix="/api", tags=["credits"])
# app.include_router(analytics_router, prefix="/api", tags=["analytics"])
# app.include_router(user_router, prefix="/api", tags=["users"])
# app.include_router(qwen_router, prefix="/api", tags=["qwen"])
# app.include_router(stt_router, prefix="/api", tags=["stt"])
# app.include_router(tts_router, prefix="/api", tags=["tts"]) 