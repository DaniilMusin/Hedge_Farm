"""Расчет минимальной гарантированной цены при хедже PUT опционами."""

import math
import numpy as np
from scipy import stats
from typing import List
from ..models import OptionQuote
from ..utils import load_cfg, rub_per_kg


def black_scholes_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Вычисляет цену PUT опциона по модели Блэка-Шоулза.
    
    Args:
        S: Цена базового актива (фьючерс)
        K: Страйк цена
        T: Время до экспирации в годах
        r: Безрисковая ставка
        sigma: Волатильность
    
    Returns:
        Цена PUT опциона
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    put_price = K * math.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
    return max(put_price, 0)  # цена не может быть отрицательной


def select_optimal_strike(futures_price: float, put_options: List[OptionQuote]) -> OptionQuote:
    """Выбирает оптимальный страйк (ближайший к текущей цене)."""
    if not put_options:
        raise ValueError("No PUT options available")
    
    # Ищем страйк ближайший к текущей цене фьючерса
    best_option = min(put_options, key=lambda opt: abs(opt.strike - futures_price))
    return best_option


def floor_price(put_options: List[OptionQuote], futures_price: float, 
                term_months: int, volatility: float = 0.25) -> float:
    """
    Рассчитывает минимальную гарантированную цену при хедже PUT опционом.
    
    Формула: MGP = (Strike - Premium - Basis - Fee) / 1000
    """
    cfg = load_cfg()
    
    # Параметры из конфигурации
    fee_pct = cfg["fee_pct"]["put"]
    basis_discount = cfg["basis_discount"]
    
    # Выбираем оптимальный опцион
    optimal_put = select_optimal_strike(futures_price, put_options)
    
    # Если премия из рынка отсутствует, рассчитываем по Black-Scholes
    if optimal_put.premium <= 0 or optimal_put.implied_vol is None:
        T = term_months / 12.0  # время до экспирации в годах
        r = 0.15  # безрисковая ставка (ключевая ставка ЦБ)
        
        premium = black_scholes_put(
            S=futures_price,
            K=optimal_put.strike,
            T=T,
            r=r,
            sigma=volatility
        )
    else:
        premium = optimal_put.premium
    
    # Комиссия платформы
    platform_fee = optimal_put.strike * fee_pct
    
    # Цена пола в руб/тонна
    floor_price_ton = optimal_put.strike - premium - basis_discount - platform_fee
    
    # Конвертация в руб/кг
    return rub_per_kg(floor_price_ton)


def calculate_delta_hedge_cost(put_delta: float, futures_price: float, volume: int) -> float:
    """Рассчитывает стоимость дельта-хеджирования."""
    # Упрощенный расчет стоимости динамического хеджирования
    hedge_volume = abs(put_delta) * volume
    transaction_cost = hedge_volume * futures_price * 0.0001  # 0.01% на транзакции
    return transaction_cost


def get_put_metrics(put_options: List[OptionQuote], futures_price: float, 
                   term_months: int, volatility: float, volume: int) -> dict:
    """Возвращает детальные метрики по опционному хеджу."""
    cfg = load_cfg()
    
    optimal_put = select_optimal_strike(futures_price, put_options)
    mgp = floor_price(put_options, futures_price, term_months, volatility)
    
    # Расчет дельты для PUT (приблизительно)
    T = term_months / 12.0
    r = 0.15
    d1 = (math.log(futures_price / optimal_put.strike) + (r + 0.5 * volatility ** 2) * T) / (volatility * math.sqrt(T))
    put_delta = stats.norm.cdf(d1) - 1  # дельта PUT всегда отрицательная
    
    delta_hedge_cost = calculate_delta_hedge_cost(put_delta, futures_price, volume)
    
    return {
        "mgp_rub_kg": mgp,
        "strike": optimal_put.strike,
        "premium": optimal_put.premium,
        "delta": put_delta,
        "delta_hedge_cost": delta_hedge_cost,
        "instrument": "put_option"
    }