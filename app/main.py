from fastapi import FastAPI
from app.api.routes import battles

app = FastAPI(
    title="LLM Colosseum API",
    description="Multi-agent LLM debates platform",
    version="0.1.0"
)

app.include_router(battles.router)

@app.get("/")
async def root():
    """Корневой эндпоинт для проверки, что сервер жив."""
    return {"message": "Welcome to LLM Colosseum! The arena is open."}

@app.get("/health")
async def health_check():
    """Стандартный эндпоинт для проверки работоспособности (Healthcheck)."""
    return {"status": "ok"}