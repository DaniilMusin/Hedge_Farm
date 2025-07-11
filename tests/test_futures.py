"""Тесты для модуля расчета цены при хедже фьючерсами."""

import pytest
import sys
import os

# Добавляем путь к модулю hedgefarm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hedgefarm.pricing.futures import floor_price, calculate_financing_cost, get_futures_metrics


class TestFuturesHedging:
    """Тесты для фьючерсного хеджирования."""
    
    def test_floor_price_basic(self):
        """Тест базового расчета цены пола для фьючерса."""
        futures_price = 16500.0  # руб/тонна
        term_months = 6
        volume = 1000
        
        mgp = floor_price(futures_price, term_months, volume)
        
        # Проверяем, что цена разумная (должна быть меньше исходной цены в кг)
        assert mgp > 0
        assert mgp < 16.5  # меньше исходной цены в руб/кг
        assert mgp > 14.0  # но не слишком низкая
    
    def test_financing_cost_calculation(self):
        """Тест расчета стоимости финансирования."""
        price = 16500.0
        leverage = 0.1
        go_rate = 0.1
        days = 180
        
        cost = calculate_financing_cost(price, leverage, go_rate, days)
        
        assert cost > 0
        assert cost < price * 0.1  # стоимость финансирования не должна превышать 10% от цены
    
    def test_futures_metrics(self):
        """Тест получения метрик фьючерсного хеджа."""
        futures_price = 16500.0
        term_months = 6
        volume = 1000
        
        metrics = get_futures_metrics(futures_price, term_months, volume)
        
        # Проверяем структуру результата
        assert "mgp_rub_kg" in metrics
        assert "margin_required" in metrics
        assert "leverage" in metrics
        assert "hedging_efficiency" in metrics
        assert "instrument" in metrics
        
        # Проверяем значения
        assert metrics["mgp_rub_kg"] > 0
        assert metrics["margin_required"] > 0
        assert metrics["leverage"] > 1
        assert metrics["instrument"] == "futures"
    
    def test_floor_price_different_volumes(self):
        """Тест расчета цены для разных объемов."""
        futures_price = 16500.0
        term_months = 6
        
        mgp_small = floor_price(futures_price, term_months, 100)
        mgp_large = floor_price(futures_price, term_months, 10000)
        
        # Цена должна быть одинаковой для разных объемов (в текущей реализации)
        assert abs(mgp_small - mgp_large) < 0.01
    
    def test_floor_price_different_terms(self):
        """Тест расчета цены для разных сроков."""
        futures_price = 16500.0
        volume = 1000
        
        mgp_short = floor_price(futures_price, 3, volume)
        mgp_long = floor_price(futures_price, 12, volume)
        
        # Для более длинного срока цена должна быть ниже из-за больших затрат на финансирование
        assert mgp_short > mgp_long


if __name__ == "__main__":
    pytest.main([__file__])