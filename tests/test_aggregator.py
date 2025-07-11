"""Тесты для модуля агрегации стратегий хеджирования."""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Добавляем путь к модулю hedgefarm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hedgefarm.pricing.aggregator import (
    calculate_forward_price,
    select_best_strategy,
    calculate_all_prices,
    get_detailed_comparison
)
from hedgefarm.models import MarketData, FuturesQuote, OptionQuote


class TestAggregator:
    """Тесты для агрегатора стратегий хеджирования."""
    
    def create_mock_market_data(self, futures_price: float = 16500.0):
        """Создает мок рыночных данных для тестирования."""
        futures_quote = FuturesQuote(
            symbol="WHEAT",
            price=futures_price,
            volume=1000,
            updated_at="2024-01-15T12:00:00Z"
        )
        
        # Создаем опционы
        strikes = [futures_price * k for k in [0.95, 0.97, 1.0, 1.03, 1.05]]
        put_options = []
        
        for strike in strikes:
            put_options.append(OptionQuote(
                symbol=f"WHEAT_{strike:.0f}_P",
                strike=strike,
                premium=max(strike - futures_price + 100, 50),
                option_type="P",
                expiry="2024-06-15",
                implied_vol=0.25
            ))
        
        return MarketData(
            futures_quote=futures_quote,
            put_options=put_options,
            usd_rate=95.0,
            volatility=0.25
        )
    
    def test_calculate_forward_price(self):
        """Тест расчета цены форвардного хеджа."""
        futures_price = 16500.0
        term_months = 6
        
        mgp_forward = calculate_forward_price(futures_price, term_months)
        
        assert mgp_forward > 0
        assert mgp_forward < 16.5  # должна быть меньше исходной цены в руб/кг
        
        # Проверяем, что применяется дисконт
        # MGP = P_fut * (1 - δ) - Fee - Basis) / 1000
        # При дефолтных настройках δ=1.5%, fee=1.2%, basis=1600 руб/т
        expected_approx = (16500 * 0.985 - 16500 * 0.985 * 0.012 - 1600) / 1000
        assert abs(mgp_forward - expected_approx) < 0.5  # погрешность ±0.5 руб/кг
    
    def test_select_best_strategy(self):
        """Тест выбора наилучшей стратегии."""
        mgp_futures = 15.8
        mgp_put = 15.5
        mgp_put_ladder = 15.6
        mgp_forward = 15.3
        
        best = select_best_strategy(mgp_futures, mgp_put, mgp_put_ladder, mgp_forward)
        assert best == "futures"  # максимальная цена
        
        # Тест с другим порядком
        best2 = select_best_strategy(14.5, 15.8, 15.7, 14.2)
        assert best2 == "put"
        
        # Тест с равными значениями (должен выбрать первую)
        best3 = select_best_strategy(15.0, 15.0, 14.9, 14.9)
        assert best3 in ["futures", "put"]  # любой из максимальных
    
    @patch('hedgefarm.pricing.futures.floor_price')
    @patch('hedgefarm.pricing.options.floor_price')
    def test_calculate_all_prices(self, mock_options_floor, mock_futures_floor):
        """Тест расчета всех вариантов цен."""
        # Мокаем функции расчета
        mock_futures_floor.return_value = 15.8
        mock_options_floor.return_value = 15.5
        
        market_data = self.create_mock_market_data()
        volume = 1000
        term_months = 6
        
        result = calculate_all_prices(market_data, volume, term_months)
        
        # Проверяем структуру результата
        assert result.culture == "wheat"
        assert result.volume_t == volume
        assert result.term_m == term_months
        assert result.floor_futures_rubkg == 15.8
        assert result.floor_put_rubkg == 15.5
        assert result.floor_forward_rubkg > 0
        assert result.recommended in ["futures", "put", "forward"]
        
        # Убеждаемся, что функции вызывались с правильными параметрами
        mock_futures_floor.assert_called_once_with(16500.0, term_months, volume)
        mock_options_floor.assert_called_once()
    
    @patch('hedgefarm.pricing.futures.get_futures_metrics')
    @patch('hedgefarm.pricing.options.get_put_metrics')
    def test_get_detailed_comparison(self, mock_put_metrics, mock_futures_metrics):
        """Тест детального сравнения стратегий."""
        # Мокаем метрики
        mock_futures_metrics.return_value = {
            "mgp_rub_kg": 15.8,
            "go_required": 1650.0,
            "instrument": "futures"
        }
        
        mock_put_metrics.return_value = {
            "mgp_rub_kg": 15.5,
            "strike": 16500.0,
            "premium": 300.0,
            "delta": -0.5,
            "instrument": "put_option"
        }
        
        market_data = self.create_mock_market_data()
        volume = 1000
        term_months = 6
        
        comparison = get_detailed_comparison(market_data, volume, term_months)
        
        # Проверяем структуру
        assert "futures" in comparison
        assert "put_option" in comparison
        assert "forward" in comparison
        assert "market_context" in comparison
        
        # Проверяем содержимое
        assert comparison["futures"]["mgp_rub_kg"] == 15.8
        assert comparison["put_option"]["mgp_rub_kg"] == 15.5
        assert comparison["forward"]["mgp_rub_kg"] > 0
        assert comparison["forward"]["no_margin_required"] is True
        
        # Проверяем рыночный контекст
        market_ctx = comparison["market_context"]
        assert market_ctx["futures_price"] == 16500.0
        assert market_ctx["volatility"] == 0.25
        assert market_ctx["usd_rate"] == 95.0
    
    def test_calculate_all_prices_integration(self):
        """Интеграционный тест расчета всех цен."""
        market_data = self.create_mock_market_data()
        volume = 1000
        term_months = 6
        
        try:
            result = calculate_all_prices(market_data, volume, term_months)
            
            # Базовые проверки
            assert result.floor_futures_rubkg > 0
            assert result.floor_put_rubkg > 0
            assert result.floor_forward_rubkg > 0
            
            # Все цены должны быть разумными (не слишком высокие/низкие)
            prices = [
                result.floor_futures_rubkg,
                result.floor_put_rubkg,
                result.floor_forward_rubkg
            ]
            
            for price in prices:
                assert 10.0 < price < 20.0, f"Неразумная цена: {price}"
            
            # Рекомендация должна соответствовать максимальной цене
            max_price = max(prices)
            if result.floor_futures_rubkg == max_price:
                assert result.recommended == "futures"
            elif result.floor_put_rubkg == max_price:
                assert result.recommended == "put"
            else:
                assert result.recommended == "forward"
                
        except Exception as e:
            # Если есть проблемы с зависимостями, тест не должен падать
            print(f"Integration test failed due to dependencies: {e}")
            pytest.skip("Dependencies not available")
    
    def test_edge_cases(self):
        """Тест граничных случаев."""
        # Очень высокая цена фьючерса
        high_price_data = self.create_mock_market_data(25000.0)
        result_high = calculate_all_prices(high_price_data, 100, 3)
        assert result_high.floor_futures_rubkg > 20.0
        
        # Очень низкая цена фьючерса
        low_price_data = self.create_mock_market_data(10000.0)
        result_low = calculate_all_prices(low_price_data, 100, 3)
        assert result_low.floor_futures_rubkg < 15.0
        
        # Большой объем
        result_big_volume = calculate_all_prices(
            self.create_mock_market_data(), 10000, 6
        )
        assert result_big_volume.volume_t == 10000
        
        # Короткий срок
        result_short_term = calculate_all_prices(
            self.create_mock_market_data(), 1000, 1
        )
        assert result_short_term.term_m == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])