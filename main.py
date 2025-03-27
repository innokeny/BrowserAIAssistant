from fastapi import FastAPI
from infrastructure.web.controllers.user_controller import (
    router as user_router,
    stt_controller,
    tts_controller,
    llm_controller
)

app = FastAPI()
app.include_router(user_router)
app.include_router(stt_controller.router)
app.include_router(tts_controller.router)
app.include_router(llm_controller.router)

@app.get("/")
def read_root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
