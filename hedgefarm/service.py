"""FastAPI сервис для расчета минимальной гарантированной цены."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import logging
import os

from .models import QuoteOut, QuoteRequest
from .datasources import MOEXClient
from .pricing.aggregator import calculate_all_prices, get_detailed_comparison
from .risk import check as risk_check

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="HedgeFarm Pricer API",
    description="API для расчета минимальной гарантированной цены при хеджировании сельхозпродуктов",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить конкретными доменами
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Клиент для получения данных с MOEX
moex_client = MOEXClient()


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Возврат иконки сайта."""
    favicon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/", summary="Корневой эндпоинт")
async def root():
    """Корневой эндпоинт с информацией о сервисе."""
    return {
        "service": "HedgeFarm Pricer",
        "version": "0.1.0",
        "description": "API для расчета минимальной гарантированной цены",
        "endpoints": {
            "price": "/price - Основной расчет цены",
            "health": "/health - Проверка состояния сервиса",
            "detailed": "/price/detailed - Детальный анализ"
        }
    }


@app.get("/health", summary="Проверка здоровья сервиса")
async def health_check():
    """Проверка состояния сервиса и подключения к источникам данных."""
    try:
        # Проверяем подключение к MOEX
        test_price = moex_client.get_last_price("WHEAT")
        
        return {
            "status": "healthy",
            "moex_connection": "ok",
            "test_wheat_price": test_price,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@app.get("/price", response_model=QuoteOut, summary="Расчет минимальной гарантированной цены")
async def get_price(
    culture: str = Query(default="wheat", description="Культура для хеджирования"),
    volume: int = Query(gt=0, description="Объем в тоннах"),
    term_months: int = Query(default=6, ge=1, le=12, description="Срок в месяцах")
):
    """
    Основной эндпоинт для расчета минимальной гарантированной цены.
    
    Возвращает цены для всех доступных инструментов хеджирования:
    - Фьючерсы
    - PUT опционы  
    - Форвардные контракты
    
    И рекомендацию по оптимальному инструменту.
    """
    try:
        # Валидация входных параметров
        if culture.lower() != "wheat":
            raise HTTPException(
                status_code=400, 
                detail="В настоящий момент поддерживается только пшеница (wheat)"
            )
        
        if volume <= 0:
            raise HTTPException(
                status_code=400,
                detail="Объем должен быть положительным числом"
            )
        
        # Получение рыночных данных
        logger.info(f"Fetching market data for {culture}, volume: {volume}t, term: {term_months}m")
        market_data = moex_client.get_market_data(culture.upper())
        
        # Расчет цен для всех инструментов
        result = calculate_all_prices(market_data, volume, term_months)
        
        logger.info(f"Price calculation completed. Recommended: {result.recommended}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Price calculation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при расчете цены: {str(e)}"
        )


@app.get("/price/detailed", summary="Детальный анализ стратегий хеджирования")
async def get_detailed_price(
    culture: str = Query(default="wheat", description="Культура для хеджирования"),
    volume: int = Query(gt=0, description="Объем в тоннах"),
    term_months: int = Query(default=6, ge=1, le=12, description="Срок в месяцах")
):
    """
    Детальный анализ всех стратегий хеджирования с метриками по каждому инструменту.
    
    Включает:
    - Требования по марже
    - Дельта-хедж для опционов
    - Стоимость финансирования
    - Риск-метрики
    """
    try:
        if culture.lower() != "wheat":
            raise HTTPException(
                status_code=400,
                detail="В настоящий момент поддерживается только пшеница (wheat)"
            )
        
        # Получение рыночных данных
        market_data = moex_client.get_market_data(culture.upper())
        
        # Детальный анализ
        detailed_result = get_detailed_comparison(market_data, volume, term_months)
        
        return detailed_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detailed analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при детальном анализе: {str(e)}"
        )


@app.post("/price", response_model=QuoteOut, summary="Расчет цены (POST)")
async def post_price(request: QuoteRequest):
    """
    POST версия эндпоинта для расчета цены.
    Принимает параметры в теле запроса.
    """
    return await get_price(
        culture=request.culture,
        volume=request.volume,
        term_months=request.term_months
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)