"""Агрегатор для выбора оптимального инструмента хеджирования."""

from typing import Dict, List
from ..models import MarketData, QuoteOut
from ..utils import load_cfg, rub_per_kg
from . import futures, options


def calculate_forward_price(futures_price: float, term_months: int) -> float:
    """
    Рассчитывает минимальную гарантированную цену при форвардном хедже.
    
    Формула: MGP = P_fut * (1 - δ) - Fee - Basis
    где δ - дисконт за отсутствие маржи
    """
    cfg = load_cfg()
    
    # Параметры из конфигурации
    fee_pct = cfg["fee_pct"]["forward"]
    basis_discount = cfg["basis_discount"]
    forward_delta_pct = cfg["forward_delta_pct"]
    
    # Дисконт за отсутствие маржи
    discounted_price = futures_price * (1 - forward_delta_pct)
    
    # Комиссия платформы
    platform_fee = discounted_price * fee_pct
    
    # Цена пола в руб/тонна
    floor_price_ton = discounted_price - platform_fee - basis_discount
    
    # Конвертация в руб/кг
    return rub_per_kg(floor_price_ton)


def select_best_strategy(mgp_futures: float, mgp_put: float, mgp_forward: float) -> str:
    """Выбирает наилучшую стратегию на основе максимального MGP."""
    strategies = {
        "futures": mgp_futures,
        "put": mgp_put,
        "forward": mgp_forward
    }
    
    # Возвращаем стратегию с максимальной гарантированной ценой
    return max(strategies.keys(), key=lambda k: strategies[k])


def apply_risk_surcharge(mgp: float, risk_surcharge: float) -> float:
    """Применяет надбавку за риск к цене."""
    return mgp * (1 - risk_surcharge)


def calculate_all_prices(market_data: MarketData, volume: int, term_months: int) -> QuoteOut:
    """
    Рассчитывает все варианты хеджирования и возвращает результат.
    
    Args:
        market_data: Рыночные данные
        volume: Объем в тоннах
        term_months: Срок в месяцах
    
    Returns:
        Результат расчета со всеми вариантами
    """
    futures_price = market_data.futures_quote.price
    
    # Расчет MGP для каждого инструмента
    mgp_futures = futures.floor_price(futures_price, term_months, volume)
    mgp_put = options.floor_price(
        market_data.put_options, 
        futures_price, 
        term_months, 
        market_data.volatility
    )
    mgp_forward = calculate_forward_price(futures_price, term_months)
    
    # Выбор рекомендуемой стратегии
    recommended = select_best_strategy(mgp_futures, mgp_put, mgp_forward)
    
    # Создание результата
    result = QuoteOut(
        culture="wheat",
        volume_t=volume,
        term_m=term_months,
        floor_futures_rubkg=mgp_futures,
        floor_put_rubkg=mgp_put,
        floor_forward_rubkg=mgp_forward,
        recommended=recommended
    )
    
    return result


def get_detailed_comparison(market_data: MarketData, volume: int, term_months: int) -> Dict:
    """Возвращает детальное сравнение всех стратегий хеджирования."""
    futures_price = market_data.futures_quote.price
    
    # Получаем детальные метрики по каждому инструменту
    futures_metrics = futures.get_futures_metrics(futures_price, term_months, volume)
    put_metrics = options.get_put_metrics(
        market_data.put_options, 
        futures_price, 
        term_months, 
        market_data.volatility, 
        volume
    )
    
    # Метрики форварда
    forward_mgp = calculate_forward_price(futures_price, term_months)
    forward_metrics = {
        "mgp_rub_kg": forward_mgp,
        "discount_applied": load_cfg()["forward_delta_pct"],
        "no_margin_required": True,
        "instrument": "forward"
    }
    
    return {
        "futures": futures_metrics,
        "put_option": put_metrics,
        "forward": forward_metrics,
        "market_context": {
            "futures_price": futures_price,
            "volatility": market_data.volatility,
            "usd_rate": market_data.usd_rate
        }
    }