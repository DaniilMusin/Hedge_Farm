"""Расчет минимальной гарантированной цены при хедже фьючерсом."""

import math
from ..utils import load_cfg, rub_per_kg, days_to_expiration


def calculate_financing_cost(price: float, leverage: float, go_rate: float, days: int) -> float:
    """
    Вычисляет стоимость финансирования гарантийного обеспечения.

    Args:
        price: Цена фьючерса
        leverage: Кредитное плечо
        go_rate: Процент гарантийного обеспечения
        days: Количество дней

    Returns:
        Стоимость финансирования

    Raises:
        ValueError: Если параметры некорректны
    """
    # Валидация входных параметров
    if price <= 0:
        raise ValueError(f"Price must be positive, got {price}")
    if leverage < 0:
        raise ValueError(f"Leverage must be non-negative, got {leverage}")
    if days < 0:
        raise ValueError(f"Days must be non-negative, got {days}")

    financing_rate = 0.15  # 15% годовых в рублях
    go_amount = price * leverage
    return go_amount * financing_rate * days / 365


def floor_price(futures_price: float, term_months: int, volume: int = 1000) -> float:
    """
    Рассчитывает минимальную гарантированную цену при хедже фьючерсом.

    Формула: MGP = (P_fut - комиссии - базис - финансирование) / 1000

    Args:
        futures_price: Цена фьючерса в руб/тонна
        term_months: Срок в месяцах
        volume: Объем в тоннах

    Returns:
        Минимальная гарантированная цена в руб/кг

    Raises:
        ValueError: Если параметры некорректны
    """
    # Валидация входных параметров
    if futures_price <= 0:
        raise ValueError(f"Futures price must be positive, got {futures_price}")
    if term_months <= 0:
        raise ValueError(f"Term months must be positive, got {term_months}")
    if term_months > 24:
        raise ValueError(f"Term months seems too large, got {term_months}")
    if volume <= 0:
        raise ValueError(f"Volume must be positive, got {volume}")

    cfg = load_cfg()

    # Параметры из конфигурации
    fee_pct = cfg["fee_pct"]["futures"]
    basis_discount = cfg["basis_discount"]
    go_pct = cfg["go_pct"]

    # Расчет дней до экспирации (приблизительно)
    days = term_months * 30

    # Комиссия платформы
    platform_fee = futures_price * fee_pct

    # Биржевые комиссии
    exchange_fee_rate = cfg.get("exchange_fee_rate", 0.00013)  # Из конфига или default
    exchange_fee = futures_price * exchange_fee_rate * 2  # обе стороны

    # Стоимость финансирования ГО
    financing_cost = calculate_financing_cost(futures_price, go_pct, go_pct, days)

    # Общие издержки
    total_costs = platform_fee + exchange_fee + financing_cost + basis_discount

    # Цена пола в руб/тонна
    floor_price_ton = futures_price - total_costs

    # Проверка что цена пола не отрицательная
    if floor_price_ton < 0:
        raise ValueError(
            f"Floor price is negative ({floor_price_ton:.2f}). "
            f"Total costs ({total_costs:.2f}) exceed futures price ({futures_price:.2f})"
        )

    # Конвертация в руб/кг
    return rub_per_kg(floor_price_ton)


def calculate_margin_requirement(price: float, volume: int) -> float:
    """Рассчитывает требования по марже."""
    cfg = load_cfg()
    go_pct = cfg["go_pct"]
    
    total_value = price * volume
    return total_value * go_pct


def get_futures_metrics(futures_price: float, term_months: int, volume: int) -> dict:
    """
    Возвращает детальные метрики по фьючерсному хеджу.

    Args:
        futures_price: Цена фьючерса
        term_months: Срок в месяцах
        volume: Объем в тоннах

    Returns:
        Словарь с метриками

    Raises:
        ValueError: Если параметры некорректны
    """
    # Валидация
    if futures_price <= 0:
        raise ValueError(f"Futures price must be positive, got {futures_price}")

    cfg = load_cfg()

    # Проверка деления на ноль
    go_pct = cfg["go_pct"]
    if go_pct <= 0:
        raise ValueError(f"GO percentage must be positive, got {go_pct}")

    mgp = floor_price(futures_price, term_months, volume)
    margin = calculate_margin_requirement(futures_price, volume)

    # Безопасное деление
    futures_price_kg = rub_per_kg(futures_price)
    hedging_efficiency = mgp / futures_price_kg if futures_price_kg > 0 else 0

    return {
        "mgp_rub_kg": mgp,
        "margin_required": margin,
        "leverage": 1 / go_pct,
        "hedging_efficiency": hedging_efficiency,
        "instrument": "futures"
    }