"""Модуль для получения данных с Московской биржи (MOEX)."""

import requests
import numpy as np
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from .models import FuturesQuote, OptionQuote, MarketData
from .utils import get_moex_token, load_cfg

logger = logging.getLogger(__name__)


class MOEXClient:
    """Клиент для работы с API Московской биржи."""

    BASE_URL = "https://iss.moex.com/iss"

    def __init__(self):
        self.session = requests.Session()

        # Загружаем конфигурацию
        self.config = load_cfg()

        # Маппинг полей MOEX API из конфигурации
        self.MARKETDATA_FIELDS = self.config.get("moex_fields", {
            "LAST": 12,  # Fallback values
            "BID": 7,
            "OFFER": 8,
        })

        # Добавляем токен для аутентификации если доступен
        try:
            token = get_moex_token()
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            logger.info("MOEX client initialized with authentication token")
        except ValueError:
            # Работаем без токена для публичных данных
            logger.info("MOEX client initialized without authentication token")

    def _extract_price_from_marketdata(self, marketdata: List, field_name: str = "LAST") -> Optional[float]:
        """
        Извлекает цену из marketdata с использованием маппинга полей.

        Args:
            marketdata: Массив данных из MOEX API
            field_name: Имя поля (LAST, BID, OFFER)

        Returns:
            Цена или None
        """
        try:
            field_index = self.MARKETDATA_FIELDS.get(field_name, 12)
            if len(marketdata) > field_index:
                price = marketdata[field_index]
                # Проверяем что цена не None и не 0 (используем is not None вместо truthy check)
                if price is not None and price != 0:
                    return float(price)
        except (IndexError, ValueError, TypeError) as e:
            logger.warning(f"Failed to extract {field_name} from marketdata: {e}")
        return None
        
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
                logger.debug(f"Fetching price for {symbol} from MOEX")
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if "marketdata" in data and data["marketdata"]["data"]:
                    marketdata = data["marketdata"]["data"][0]
                    # Используем новый метод вместо hardcoded index
                    last_price = self._extract_price_from_marketdata(marketdata, "LAST")

                    if last_price:
                        logger.info(f"Successfully fetched {symbol} price: {last_price}")
                        return last_price

                # Fallback если не удалось получить реальные данные
                logger.warning(f"Could not fetch real data for {symbol}, using fallback price 16500.0")
                return 16500.0  # Fallback цена

            except requests.Timeout:
                logger.error(f"Timeout fetching {symbol} price after 10s, using fallback")
                return 16500.0
            except requests.RequestException as e:
                logger.error(f"Network error fetching {symbol} price: {e}, using fallback")
                return 16500.0
            except (ValueError, KeyError, IndexError) as e:
                logger.error(f"Data parsing error for {symbol}: {e}, using fallback")
                return 16500.0
                
        elif symbol == "USD000UTSTOM" or symbol == "USD/RUB_TOM":
            # Реальный запрос для курса USD/RUB
            url = f"{self.BASE_URL}/engines/currency/markets/selt/securities/USD000UTSTOM.json"
            params = {
                "iss.only": "marketdata",
                "iss.meta": "off"
            }

            try:
                logger.debug(f"Fetching USD/RUB rate from MOEX")
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if "marketdata" in data and data["marketdata"]["data"]:
                    marketdata = data["marketdata"]["data"][0]
                    # Используем новый метод
                    last_price = self._extract_price_from_marketdata(marketdata, "LAST")

                    if last_price:
                        logger.info(f"Successfully fetched USD/RUB rate: {last_price}")
                        return last_price

                # Fallback
                logger.warning(f"Could not fetch real USD/RUB rate, using fallback 95.0")
                return 95.0

            except requests.Timeout:
                logger.error(f"Timeout fetching USD/RUB rate after 10s, using fallback")
                return 95.0
            except requests.RequestException as e:
                logger.error(f"Network error fetching USD/RUB rate: {e}, using fallback")
                return 95.0
            except (ValueError, KeyError, IndexError) as e:
                logger.error(f"Data parsing error for USD/RUB: {e}, using fallback")
                return 95.0
        else:
            logger.error(f"Unknown symbol: {symbol}")
            raise ValueError(f"Unknown symbol: {symbol}")
    
    def get_futures_quote(self, symbol: str = "WHEAT") -> FuturesQuote:
        """Получает котировку фьючерса."""
        price = self.get_last_price(symbol)

        return FuturesQuote(
            symbol=symbol,
            price=price,
            volume=1000,
            updated_at=datetime.now(timezone.utc)
        )
    
    def get_option_chain(self, underlying: str, option_type: str = "P") -> List[OptionQuote]:
        """
        Получает цепочку опционов.

        Note: Это упрощенная реализация для демо.
        В production должна использовать реальные данные из MOEX options API.
        """
        fut_price = self.get_last_price(underlying)
        strikes = [fut_price * k for k in [0.95, 0.97, 1.0, 1.03, 1.05]]

        # Рассчитываем дату экспирации (3-й четверг через 3 месяца)
        today = datetime.now(timezone.utc)
        expiry_date = today + timedelta(days=90)  # ~3 месяца
        expiry_str = expiry_date.strftime("%Y-%m-%d")

        options = []
        for strike in strikes:
            # Упрощенный расчет премии на основе moneyness
            # В реальности берется из биржевого стакана
            moneyness = abs(fut_price - strike)
            # Премия зависит от moneyness: чем дальше от денег, тем меньше
            time_value = max(50, moneyness * 0.15 + 100)

            options.append(OptionQuote(
                symbol=f"{underlying}_{strike:.0f}_{option_type}",
                strike=strike,
                premium=time_value,
                option_type=option_type,
                expiry=expiry_str,
                implied_vol=0.25
            ))

        logger.debug(f"Generated {len(options)} {option_type} options for {underlying}")
        return options
    
    def get_historical_volatility(self, symbol: str, days: int = 30) -> float:
        """
        Вычисляет историческую волатильность.

        Note: Это упрощенная реализация. В production должна:
        1. Загружать реальные исторические цены из MOEX
        2. Рассчитывать волатильность на основе log returns
        3. Использовать методы EWMA или GARCH для более точной оценки

        Args:
            symbol: Символ инструмента
            days: Количество дней для расчета (по умолчанию 30)

        Returns:
            Годовая волатильность (annualized volatility)
        """
        # TODO: В будущем заменить на реальные данные через MOEX history API
        # url = f"{self.BASE_URL}/history/engines/futures/markets/forts/securities/{symbol}.json"

        # Для демо используем типичные значения волатильности из конфигурации
        # Пшеница обычно имеет волатильность 20-35% годовых
        volatility_estimates = self.config.get("volatility_estimates", {
            "WHEAT": 0.28,
            "CORN": 0.30,
            "SOYBEANS": 0.25,
            "default": 0.25
        })

        estimated_vol = volatility_estimates.get(symbol, volatility_estimates.get("default", 0.25))
        logger.info(f"Using estimated volatility for {symbol}: {estimated_vol:.2%}")
        return estimated_vol
    
    def get_market_data(self, symbol: str = "WHEAT") -> MarketData:
        """Получает полный набор рыночных данных."""
        return MarketData(
            futures_quote=self.get_futures_quote(symbol),
            put_options=self.get_option_chain(symbol, "P"),
            usd_rate=self.get_last_price("USD000UTSTOM"),
            volatility=self.get_historical_volatility(symbol)
        )