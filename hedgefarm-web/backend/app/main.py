from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import price
from .config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HedgeFarm API",
    description="API for calculating minimum guaranteed prices for agricultural hedging",
    version="0.1.0"
)

# Улучшенные CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_methods=["GET", "POST"],  # Только необходимые методы
    allow_headers=["Content-Type", "Authorization"],  # Только необходимые headers
    allow_credentials=False,
    max_age=3600,  # Cache preflight requests for 1 hour
)

app.include_router(price.router)

@app.get("/health", status_code=200)
async def health():
    """Health check endpoint."""
    try:
        # Можно добавить проверку подключения к внешним сервисам
        return {
            "status": "healthy",
            "version": "0.1.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }