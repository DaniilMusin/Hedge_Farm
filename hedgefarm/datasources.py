"""Модуль для получения данных с Московской биржи (MOEX)."""

import requests
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from .models import FuturesQuote, OptionQuote, MarketData
from .utils import get_moex_token


class MOEXClient:
    """Клиент для работы с API Московской биржи."""
    
    BASE_URL = "https://iss.moex.com/iss"
    
    def __init__(self):
        self.session = requests.Session()
        # В продакшене здесь была бы аутентификация с токеном
        
    def get_last_price(self, symbol: str) -> float:
        """Получает последнюю цену по символу."""
        # Упрощенная реализация для демо
        if symbol == "WHEAT":
            # Имитация цены фьючерса на пшеницу
            return 16500.0  # руб/тонна
        elif symbol == "USD/RUB_TOM":
            return 95.0  # курс USD/RUB
        else:
            raise ValueError(f"Unknown symbol: {symbol}")
    
    def get_futures_quote(self, symbol: str = "WHEAT") -> FuturesQuote:
        """Получает котировку фьючерса."""
        # В реальной реализации здесь был бы запрос к MOEX API
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
            usd_rate=self.get_last_price("USD/RUB_TOM"),
            volatility=self.get_historical_volatility(symbol)
        )