"""Расчет минимальной гарантированной цены при хедже PUT опционами."""

import math
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple
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


def create_ladder_strikes(futures_price: float, put_options: List[OptionQuote]) -> List[Tuple[OptionQuote, float]]:
    """
    Создает 5-шаговую лестницу страйков с распределением 25-25-20-20-10%.
    
    Args:
        futures_price: Текущая цена фьючерса
        put_options: Доступные опционы
    
    Returns:
        Список кортежей (опцион, вес в портфеле)
    """
    if not put_options:
        raise ValueError("No PUT options available for ladder hedge")
    
    # Сортируем опционы по страйку
    sorted_options = sorted(put_options, key=lambda opt: opt.strike)
    
    # Если опционов меньше 5, используем все доступные
    if len(sorted_options) < 5:
        # Равномерное распределение между доступными опционами
        weight = 1.0 / len(sorted_options)
        return [(opt, weight) for opt in sorted_options]
    
    # Выбираем 5 страйков: 2 выше спота, 1 около спота, 2 ниже спота
    spot_option = min(sorted_options, key=lambda opt: abs(opt.strike - futures_price))
    spot_idx = sorted_options.index(spot_option)
    
    # Определяем индексы для лестницы
    ladder_indices = []
    
    # 2 страйка ниже спота
    for i in range(max(0, spot_idx - 2), spot_idx):
        if i >= 0:
            ladder_indices.append(i)
    
    # Сам спот
    ladder_indices.append(spot_idx)
    
    # 2 страйка выше спота
    for i in range(spot_idx + 1, min(len(sorted_options), spot_idx + 3)):
        ladder_indices.append(i)
    
    # Если у нас недостаточно опционов, добавляем крайние
    while len(ladder_indices) < 5 and len(ladder_indices) < len(sorted_options):
        if ladder_indices[0] > 0:
            ladder_indices.insert(0, ladder_indices[0] - 1)
        elif ladder_indices[-1] < len(sorted_options) - 1:
            ladder_indices.append(ladder_indices[-1] + 1)
        else:
            break
    
    # Берем до 5 опционов
    ladder_indices = ladder_indices[:5]
    
    # Веса для распределения 25-25-20-20-10%
    if len(ladder_indices) == 5:
        weights = [0.25, 0.25, 0.20, 0.20, 0.10]
    elif len(ladder_indices) == 4:
        weights = [0.30, 0.30, 0.25, 0.15]
    elif len(ladder_indices) == 3:
        weights = [0.40, 0.35, 0.25]
    elif len(ladder_indices) == 2:
        weights = [0.60, 0.40]
    else:
        weights = [1.0]
    
    # Создаем результат
    ladder = []
    for i, idx in enumerate(ladder_indices):
        if i < len(weights):
            ladder.append((sorted_options[idx], weights[i]))
    
    return ladder


def ladder_floor_price(put_options: List[OptionQuote], futures_price: float, 
                      term_months: int, volatility: float = 0.25) -> float:
    """
    Рассчитывает минимальную гарантированную цену при лестничном хедже PUT опционами.
    """
    cfg = load_cfg()
    
    # Параметры из конфигурации
    fee_pct = cfg["fee_pct"]["put"]
    basis_discount = cfg["basis_discount"]
    
    # Создаем лестницу страйков
    ladder = create_ladder_strikes(futures_price, put_options)
    
    total_mgp = 0.0
    T = term_months / 12.0  # время до экспирации в годах
    r = 0.15  # безрисковая ставка
    
    for option, weight in ladder:
        # Если премия из рынка отсутствует, рассчитываем по Black-Scholes
        if option.premium <= 0 or option.implied_vol is None:
            premium = black_scholes_put(
                S=futures_price,
                K=option.strike,
                T=T,
                r=r,
                sigma=volatility
            )
        else:
            premium = option.premium
        
        # Комиссия платформы для этого опциона
        platform_fee = option.strike * fee_pct
        
        # Цена пола в руб/тонна для этого опциона
        option_floor_price_ton = option.strike - premium - basis_discount - platform_fee
        
        # Добавляем взвешенный вклад в общую MGP
        total_mgp += weight * rub_per_kg(option_floor_price_ton)
    
    return total_mgp


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
    mgp_single = floor_price(put_options, futures_price, term_months, volatility)
    mgp_ladder = ladder_floor_price(put_options, futures_price, term_months, volatility)
    
    # Расчет дельты для PUT (приблизительно)
    T = term_months / 12.0
    r = 0.15
    d1 = (math.log(futures_price / optimal_put.strike) + (r + 0.5 * volatility ** 2) * T) / (volatility * math.sqrt(T))
    put_delta = stats.norm.cdf(d1) - 1  # дельта PUT всегда отрицательная
    
    delta_hedge_cost = calculate_delta_hedge_cost(put_delta, futures_price, volume)
    
    return {
        "mgp_rub_kg": mgp_single,
        "mgp_ladder_rub_kg": mgp_ladder,
        "strike": optimal_put.strike,
        "premium": optimal_put.premium,
        "delta": put_delta,
        "delta_hedge_cost": delta_hedge_cost,
        "ladder_strikes": [(opt.strike, weight) for opt, weight in create_ladder_strikes(futures_price, put_options)],
        "instrument": "put_option"
    }