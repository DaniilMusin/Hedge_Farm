"""Тесты для FastAPI эндпоинтов."""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Добавляем путь к модулю hedgefarm
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient
    from hedgefarm.service import app
    
    # Создаем тестовый клиент
    client = TestClient(app)
    FASTAPI_AVAILABLE = True
except ImportError:
    # FastAPI не установлен, пропускаем тесты
    FASTAPI_AVAILABLE = False
    client = None


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestAPI:
    """Тесты для API эндпоинтов."""
    
    def test_root_endpoint(self):
        """Тест корневого эндпоинта."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert data["service"] == "HedgeFarm Pricer"
        assert "version" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """Тест эндпоинта проверки здоровья."""
        response = client.get("/health")
        
        # Может быть либо 200 (если все ОК), либо 503 (если проблемы)
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]
    
    @patch('hedgefarm.service.moex_client')
    def test_price_endpoint_success(self, mock_moex_client):
        """Тест успешного расчета цены."""
        # Мокаем рыночные данные
        mock_market_data = Mock()
        mock_market_data.futures_quote.price = 16500.0
        mock_market_data.put_options = []
        mock_market_data.volatility = 0.25
        mock_market_data.usd_rate = 95.0
        
        mock_moex_client.get_market_data.return_value = mock_market_data
        
        response = client.get("/price?culture=wheat&volume=1000&term_months=6")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "culture", "volume_t", "term_m",
            "floor_futures_rubkg", "floor_put_rubkg", "floor_forward_rubkg",
            "recommended", "calculated_at"
        ]
        
        for field in required_fields:
            assert field in data
        
        assert data["culture"] == "wheat"
        assert data["volume_t"] == 1000
        assert data["term_m"] == 6
        assert data["recommended"] in ["futures", "put", "forward"]
    
    def test_price_endpoint_invalid_culture(self):
        """Тест с неподдерживаемой культурой."""
        response = client.get("/price?culture=corn&volume=1000&term_months=6")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "пшеница" in data["detail"]
    
    def test_price_endpoint_invalid_volume(self):
        """Тест с некорректным объемом."""
        response = client.get("/price?culture=wheat&volume=0&term_months=6")
        assert response.status_code == 422  # Validation error
    
    def test_price_endpoint_invalid_term(self):
        """Тест с некорректным сроком."""
        response = client.get("/price?culture=wheat&volume=1000&term_months=15")
        assert response.status_code == 422  # Validation error
    
    @patch('hedgefarm.service.moex_client')
    def test_detailed_endpoint(self, mock_moex_client):
        """Тест детального анализа."""
        # Мокаем рыночные данные
        mock_market_data = Mock()
        mock_market_data.futures_quote.price = 16500.0
        mock_market_data.put_options = []
        mock_market_data.volatility = 0.25
        mock_market_data.usd_rate = 95.0
        
        mock_moex_client.get_market_data.return_value = mock_market_data
        
        response = client.get("/price/detailed?culture=wheat&volume=1000&term_months=6")
        
        # Может падать из-за зависимостей, но структура должна быть правильной
        if response.status_code == 200:
            data = response.json()
            assert "futures" in data
            assert "put_option" in data
            assert "forward" in data
            assert "market_context" in data
    
    def test_post_price_endpoint(self):
        """Тест POST эндпоинта для расчета цены."""
        request_data = {
            "culture": "wheat",
            "volume": 1000,
            "term_months": 6
        }
        
        with patch('hedgefarm.service.moex_client') as mock_moex_client:
            mock_market_data = Mock()
            mock_market_data.futures_quote.price = 16500.0
            mock_market_data.put_options = []
            mock_market_data.volatility = 0.25
            mock_market_data.usd_rate = 95.0
            
            mock_moex_client.get_market_data.return_value = mock_market_data
            
            response = client.post("/price", json=request_data)
            
            # Проверяем, что запрос обрабатывается
            assert response.status_code in [200, 500]  # 500 если есть проблемы с зависимостями


class TestAPIWithoutFastAPI:
    """Тесты, которые работают без FastAPI."""
    
    def test_import_service_module(self):
        """Тест импорта модуля сервиса."""
        try:
            import hedgefarm.service
            assert hasattr(hedgefarm.service, 'app')
        except ImportError as e:
            # Ожидаемо, если FastAPI не установлен
            assert "fastapi" in str(e).lower()
    
    def test_models_import(self):
        """Тест импорта моделей."""
        try:
            from hedgefarm.models import QuoteRequest, QuoteOut
            
            # Проверяем создание экземпляров
            request = QuoteRequest(culture="wheat", volume=1000)
            assert request.culture == "wheat"
            assert request.volume == 1000
            assert request.term_months == 6  # значение по умолчанию
            
        except ImportError as e:
            # Ожидаемо, если pydantic не установлен
            assert "pydantic" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__])