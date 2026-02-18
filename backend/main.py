import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, DEBUG
from database import init_db
from routers import dashboard, chat, career, vacancies


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте приложения."""
    print("[START] EnbekAI starting...")
    await init_db()
    print("[OK] Database ready")
    yield
    print("[STOP] EnbekAI shutting down")


app = FastAPI(
    title="EnbekAI API",
    description="AI-аналитик рынка труда Казахстана",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/api", tags=["AI Chat"])
app.include_router(career.router, prefix="/api", tags=["Career Plan"])
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["Vacancies"])


@app.get("/")
async def root():
    return {
        "service": "EnbekAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=DEBUG)
