from fastapi import APIRouter, HTTPException
from ..schemas.price import PriceRequest, PriceResponse
from hedgefarm.pricing.aggregator import calculate_all_prices
from hedgefarm.datasources import MOEXClient
import logging

router = APIRouter(prefix="/api", tags=["Price"])
logger = logging.getLogger(__name__)

# Инициализация клиента MOEX
moex_client = MOEXClient()

@router.post("/price", response_model=PriceResponse, status_code=201)
async def get_price(payload: PriceRequest):
    """Расчет минимальной гарантированной цены для хеджирования."""
    try:
        # Валидация входных данных
        if payload.culture.lower() != "wheat":
            raise HTTPException(
                status_code=400,
                detail="Currently only wheat is supported"
            )

        if payload.volume_t <= 0:
            raise HTTPException(
                status_code=400,
                detail="Volume must be positive"
            )

        # Получение рыночных данных
        logger.info(f"Fetching market data for {payload.culture}, volume: {payload.volume_t}t, term: {payload.term_m}m")
        market_data = moex_client.get_market_data(payload.culture.upper())

        # Расчет цен для всех инструментов
        result = calculate_all_prices(market_data, payload.volume_t, payload.term_m)

        # Формирование ответа
        return PriceResponse(
            culture=result.culture,
            volume_t=result.volume_t,
            term_m=result.term_m,
            floor_futures_rubkg=result.floor_futures_rubkg,
            floor_put_rubkg=result.floor_put_rubkg,
            floor_forward_rubkg=result.floor_forward_rubkg,
            recommended=result.recommended,
            calculated_at=result.calculated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Price calculation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during price calculation"
        )