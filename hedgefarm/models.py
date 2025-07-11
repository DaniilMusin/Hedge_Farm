"""Pydantic модели для hedgefarm-pricer API."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class QuoteRequest(BaseModel):
    """Запрос на получение котировки."""
    culture: Literal["wheat"] = Field(description="Культура для хеджирования")
    volume: int = Field(gt=0, description="Объем в тоннах")
    term_months: int = Field(default=6, ge=1, le=12, description="Срок в месяцах")


class QuoteOut(BaseModel):
    """Ответ с расчетом минимальной гарантированной цены."""
    culture: str = Field(description="Культура")
    volume_t: int = Field(description="Объем в тоннах")
    term_m: int = Field(description="Срок в месяцах")
    floor_futures_rubkg: float = Field(description="Цена пола при хедже фьючерсом, руб/кг")
    floor_put_rubkg: float = Field(description="Цена пола при хедже PUT опционом, руб/кг")
    floor_forward_rubkg: float = Field(description="Цена пола при форвардном хедже, руб/кг")
    recommended: Literal["futures", "put", "forward"] = Field(description="Рекомендуемый инструмент")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="Время расчета")


class FuturesQuote(BaseModel):
    """Котировка фьючерса."""
    symbol: str
    price: float = Field(description="Цена в руб/тонна")
    volume: int = Field(description="Объем торгов")
    updated_at: datetime


class OptionQuote(BaseModel):
    """Котировка опциона."""
    symbol: str
    strike: float = Field(description="Страйк цена")
    premium: float = Field(description="Премия опциона")
    option_type: Literal["P", "C"] = Field(description="Тип опциона: Put или Call")
    expiry: str = Field(description="Дата экспирации")
    implied_vol: Optional[float] = Field(default=None, description="Подразумеваемая волатильность")


class MarketData(BaseModel):
    """Рыночные данные для расчета."""
    futures_quote: FuturesQuote
    put_options: List[OptionQuote]
    usd_rate: float = Field(description="Курс USD/RUB")
    volatility: float = Field(description="Историческая волатильность")


class RiskMetrics(BaseModel):
    """Показатели риска."""
    var_99: float = Field(description="VaR 99%")
    capital_required: float = Field(description="Требуемый капитал")
    risk_surcharge: float = Field(default=0.0, description="Надбавка за риск")