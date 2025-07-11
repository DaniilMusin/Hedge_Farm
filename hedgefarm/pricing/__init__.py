"""Модули расчета ценообразования для различных инструментов хеджирования."""

from .aggregator import calculate_all_prices

# Алиас для удобства внешних импортов
quote_all = calculate_all_prices

__all__ = ["quote_all", "calculate_all_prices"]