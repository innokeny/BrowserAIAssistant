from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.web.controllers.credit_controller import router as credit_router
from infrastructure.web.controllers.analytics_controller import router as analytics_router

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add credit routes
app.include_router(credit_router, prefix="/api/v1", tags=["credits"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"]) 