"""Расчет минимальной гарантированной цены при хедже фьючерсом."""

import math
from ..utils import load_cfg, rub_per_kg, days_to_expiration


def calculate_financing_cost(price: float, leverage: float, go_rate: float, days: int) -> float:
    """Вычисляет стоимость финансирования гарантийного обеспечения."""
    financing_rate = 0.15  # 15% годовых в рублях
    go_amount = price * leverage
    return go_amount * financing_rate * days / 365


def floor_price(futures_price: float, term_months: int, volume: int = 1000) -> float:
    """
    Рассчитывает минимальную гарантированную цену при хедже фьючерсом.
    
    Формула: MGP = (P_fut - комиссии - базис - финансирование) / 1000
    """
    cfg = load_cfg()
    
    # Параметры из конфигурации
    fee_pct = cfg["fee_pct"]["futures"]
    basis_discount = cfg["basis_discount"]
    go_pct = cfg["go_pct"]
    
    # Расчет дней до экспирации (приблизительно)
    days = term_months * 30
    
    # Комиссия платформы
    platform_fee = futures_price * fee_pct
    
    # Биржевые комиссии (упрощенно)
    exchange_fee = futures_price * 0.00013 * 2  # 0.013% с каждой стороны
    
    # Стоимость финансирования ГО
    financing_cost = calculate_financing_cost(futures_price, go_pct, go_pct, days)
    
    # Общие издержки
    total_costs = platform_fee + exchange_fee + financing_cost + basis_discount
    
    # Цена пола в руб/тонна
    floor_price_ton = futures_price - total_costs
    
    # Конвертация в руб/кг
    return rub_per_kg(floor_price_ton)


def calculate_margin_requirement(price: float, volume: int) -> float:
    """Рассчитывает требования по марже."""
    cfg = load_cfg()
    go_pct = cfg["go_pct"]
    
    total_value = price * volume
    return total_value * go_pct


def get_futures_metrics(futures_price: float, term_months: int, volume: int) -> dict:
    """Возвращает детальные метрики по фьючерсному хеджу."""
    cfg = load_cfg()
    
    mgp = floor_price(futures_price, term_months, volume)
    margin = calculate_margin_requirement(futures_price, volume)
    
    return {
        "mgp_rub_kg": mgp,
        "margin_required": margin,
        "leverage": 1 / cfg["go_pct"],
        "hedging_efficiency": mgp / rub_per_kg(futures_price),
        "instrument": "futures"
    }