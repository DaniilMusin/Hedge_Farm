from fastapi import APIRouter
from ..schemas.price import PriceRequest, PriceResponse
from hedgefarm.pricing import quote_all   # ← импорт из вашего репо

router = APIRouter(prefix="/api", tags=["Price"])

@router.post("/price", response_model=PriceResponse)
def get_price(payload: PriceRequest):
    q = quote_all(payload.term_m)
    return PriceResponse(**q,
                         culture=payload.culture,
                         volume_t=payload.volume_t,
                         term_m=payload.term_m)