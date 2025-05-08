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

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

# Add routes
app.include_router(credit_router, prefix="/api/v1", tags=["credits"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(user_router, prefix="/api/v1", tags=["users"])
app.include_router(qwen_router, prefix="/api/v1", tags=["qwen"])
app.include_router(stt_router, prefix="/api/v1", tags=["stt"])
app.include_router(tts_router, prefix="/api/v1", tags=["tts"]) 