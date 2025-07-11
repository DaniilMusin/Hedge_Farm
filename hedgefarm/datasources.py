"""Модуль для получения данных с Московской биржи (MOEX)."""

import requests
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import FuturesQuote, OptionQuote, MarketData
from .utils import get_moex_token


class MOEXClient:
    """Клиент для работы с API Московской биржи."""
    
    BASE_URL = "https://iss.moex.com/iss"
    
    def __init__(self):
        self.session = requests.Session()
        # Добавляем токен для аутентификации если доступен
        try:
            token = get_moex_token()
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        except ValueError:
            # Работаем без токена для публичных данных
            pass
        
    def get_last_price(self, symbol: str) -> float:
        """Получает последнюю цену по символу через MOEX ISS API."""
        if symbol == "WHEAT":
            # Реальный запрос к MOEX ISS API для фьючерса WHEAT
            url = f"{self.BASE_URL}/engines/futures/markets/forts/securities/{symbol}.json"
            params = {
                "iss.only": "marketdata",
                "iss.meta": "off"
            }
            
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "marketdata" in data and data["marketdata"]["data"]:
                    # Извлекаем последнюю цену из ответа MOEX
                    marketdata = data["marketdata"]["data"][0]
                    # Индекс для LAST (последняя цена) обычно 12 в MOEX API
                    last_price = marketdata[12] if len(marketdata) > 12 and marketdata[12] else None
                    
                    if last_price:
                        return float(last_price)
                
                # Fallback если не удалось получить реальные данные
                print(f"Warning: Could not fetch real data for {symbol}, using fallback")
                return 16500.0  # Fallback цена
                
            except (requests.RequestException, ValueError, KeyError, IndexError) as e:
                print(f"Error fetching {symbol} price: {e}, using fallback")
                return 16500.0  # Fallback цена
                
        elif symbol == "USD000UTSTOM" or symbol == "USD/RUB_TOM":
            # Реальный запрос для курса USD/RUB
            url = f"{self.BASE_URL}/engines/currency/markets/selt/securities/USD000UTSTOM.json"
            params = {
                "iss.only": "marketdata",
                "iss.meta": "off"
            }
            
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if "marketdata" in data and data["marketdata"]["data"]:
                    marketdata = data["marketdata"]["data"][0]
                    last_price = marketdata[12] if len(marketdata) > 12 and marketdata[12] else None
                    
                    if last_price:
                        return float(last_price)
                
                # Fallback
                print(f"Warning: Could not fetch real USD/RUB rate, using fallback")
                return 95.0
                
            except (requests.RequestException, ValueError, KeyError, IndexError) as e:
                print(f"Error fetching USD/RUB rate: {e}, using fallback")
                return 95.0
        else:
            raise ValueError(f"Unknown symbol: {symbol}")
    
    def get_futures_quote(self, symbol: str = "WHEAT") -> FuturesQuote:
        """Получает котировку фьючерса."""
        price = self.get_last_price(symbol)
        
        return FuturesQuote(
            symbol=symbol,
            price=price,
            volume=1000,
            updated_at=datetime.utcnow()
        )
    
    def get_option_chain(self, underlying: str, option_type: str = "P") -> List[OptionQuote]:
        """Получает цепочку опционов."""
        # Упрощенная реализация для демо
        fut_price = self.get_last_price(underlying)
        strikes = [fut_price * k for k in [0.95, 0.97, 1.0, 1.03, 1.05]]
        
        options = []
        for strike in strikes:
            # Упрощенный расчет премии (в реальности брался бы из стакана)
            time_value = abs(fut_price - strike) * 0.1 + 50  # базовая премия
            
            options.append(OptionQuote(
                symbol=f"{underlying}_{strike:.0f}_{option_type}",
                strike=strike,
                premium=time_value,
                option_type=option_type,
                expiry="2024-06-15",  # фиксированная дата для демо
                implied_vol=0.25
            ))
        
        return options
    
    def get_historical_volatility(self, symbol: str, days: int = 10) -> float:
        """Вычисляет историческую волатильность."""
        # В реальной реализации здесь загружалась бы история цен
        # и рассчитывалась волатильность
        np.random.seed(42)  # для воспроизводимости в демо
        daily_returns = np.random.normal(0, 0.02, days)  # 2% дневная волатильность
        return np.std(daily_returns) * np.sqrt(252)  # годовая волатильность
    
    def get_market_data(self, symbol: str = "WHEAT") -> MarketData:
        """Получает полный набор рыночных данных."""
        return MarketData(
            futures_quote=self.get_futures_quote(symbol),
            put_options=self.get_option_chain(symbol, "P"),
            usd_rate=self.get_last_price("USD000UTSTOM"),
            volatility=self.get_historical_volatility(symbol)
        )