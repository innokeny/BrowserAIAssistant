from fastapi import FastAPI
from infrastructure.web.controllers.user_controller import router as user_router
from infrastructure.web.controllers.stt_controller import router as stt_router
from infrastructure.web.controllers.tts_controller import router as tts_router
from infrastructure.web.controllers.gemini_controller import router as gemini_router

app = FastAPI()
app.include_router(user_router)
app.include_router(stt_router)
app.include_router(tts_router)
app.include_router(gemini_router)

@app.get("/")
def read_root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)