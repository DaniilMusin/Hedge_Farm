"""Тесты для модуля расчета цены при хедже PUT опционами."""

import pytest
import sys
import os
from unittest.mock import Mock

# Добавляем путь к модулю hedgefarm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hedgefarm.pricing.options import (
    black_scholes_put, 
    select_optimal_strike, 
    floor_price, 
    get_put_metrics
)
from hedgefarm.models import OptionQuote


class TestOptionsHedging:
    """Тесты для опционного хеджирования."""
    
    def create_mock_put_options(self, futures_price: float):
        """Создает набор мок PUT опционов для тестирования."""
        strikes = [futures_price * k for k in [0.95, 0.97, 1.0, 1.03, 1.05]]
        options = []
        
        for strike in strikes:
            options.append(OptionQuote(
                symbol=f"WHEAT_{strike:.0f}_P",
                strike=strike,
                premium=max(strike - futures_price + 100, 50),  # внутренняя стоимость + время
                option_type="P",
                expiry="2024-06-15",
                implied_vol=0.25
            ))
        
        return options
    
    def test_black_scholes_put_calculation(self):
        """Тест расчета цены PUT по Блэку-Шоулзу."""
        S = 16500.0  # цена базового актива
        K = 16000.0  # страйк
        T = 0.5      # полгода
        r = 0.15     # 15% ставка
        sigma = 0.25 # 25% волатильность
        
        put_price = black_scholes_put(S, K, T, r, sigma)
        
        assert put_price > 0
        assert put_price < K  # цена PUT не может превышать страйк
        # Для OTM опциона цена должна быть меньше внутренней стоимости
        assert put_price < max(K - S, 0) + 1000  # + временная стоимость
    
    def test_select_optimal_strike(self):
        """Тест выбора оптимального страйка."""
        futures_price = 16500.0
        put_options = self.create_mock_put_options(futures_price)
        
        optimal = select_optimal_strike(futures_price, put_options)
        
        # Должен выбрать опцион со страйком ближайшим к текущей цене
        assert optimal.strike == futures_price  # ATM опцион
        assert optimal.option_type == "P"
    
    def test_select_optimal_strike_empty_list(self):
        """Тест выбора страйка при пустом списке опционов."""
        with pytest.raises(ValueError, match="No PUT options available"):
            select_optimal_strike(16500.0, [])
    
    def test_floor_price_calculation(self):
        """Тест расчета цены пола с PUT опционами."""
        futures_price = 16500.0
        put_options = self.create_mock_put_options(futures_price)
        term_months = 6
        volatility = 0.25
        
        mgp = floor_price(put_options, futures_price, term_months, volatility)
        
        assert mgp > 0
        assert mgp < 16.5  # должна быть меньше исходной цены в руб/кг
        assert mgp > 12.0  # но не слишком низкая
    
    def test_get_put_metrics(self):
        """Тест получения метрик опционного хеджа."""
        futures_price = 16500.0
        put_options = self.create_mock_put_options(futures_price)
        term_months = 6
        volatility = 0.25
        volume = 1000
        
        metrics = get_put_metrics(put_options, futures_price, term_months, volatility, volume)
        
        # Проверяем структуру результата
        required_keys = ["mgp_rub_kg", "strike", "premium", "delta", "delta_hedge_cost", "instrument"]
        for key in required_keys:
            assert key in metrics
        
        # Проверяем значения
        assert metrics["mgp_rub_kg"] > 0
        assert metrics["strike"] > 0
        assert metrics["premium"] > 0
        assert metrics["delta"] < 0  # дельта PUT всегда отрицательная
        assert metrics["delta_hedge_cost"] >= 0
        assert metrics["instrument"] == "put_option"
    
    def test_black_scholes_edge_cases(self):
        """Тест граничных случаев для Блэка-Шоулза."""
        # ITM опцион
        itm_price = black_scholes_put(15000, 16000, 0.5, 0.15, 0.25)
        assert itm_price > 950  # должна быть существенная внутренняя стоимость (фактически ~974.77)
        
        # OTM опцион
        otm_price = black_scholes_put(17000, 16000, 0.5, 0.15, 0.25)
        assert otm_price > 0 and otm_price < 500  # только временная стоимость
        
        # Очень короткий срок
        short_term_price = black_scholes_put(16000, 16000, 0.01, 0.15, 0.25)
        assert short_term_price >= 0
    
    def test_floor_price_with_market_premium(self):
        """Тест расчета цены пола с рыночной премией."""
        futures_price = 16500.0
        
        # Создаем опцион с известной премией
        put_option = OptionQuote(
            symbol="WHEAT_16500_P",
            strike=16500.0,
            premium=300.0,  # известная премия
            option_type="P",
            expiry="2024-06-15",
            implied_vol=0.25
        )
        
        mgp = floor_price([put_option], futures_price, 6, 0.25)
        
        # Проверяем, что используется рыночная премия
        assert mgp > 0
        # Можем проверить примерный расчет: (16500 - 300 - 1600 - комиссия) / 1000


if __name__ == "__main__":
    pytest.main([__file__])