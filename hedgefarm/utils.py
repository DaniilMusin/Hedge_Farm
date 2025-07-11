"""Утилитарные функции для hedgefarm-pricer."""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
    """Возвращает конфигурацию по умолчанию."""
    return {
        "fee_pct": {
            "futures": 0.008,
            "put": 0.010,
            "forward": 0.012
        },
        "basis_discount": 1600,
        "forward_delta_pct": 0.015,
        "go_pct": 0.10,
        "risk": {
            "capital_reserve": 50000000,
            "alpha_capital": 0.1
        }
    }


def load_cfg() -> Dict[str, Any]:
    """Загружает конфигурацию из settings.yaml с fallback на default."""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    
    try:
        if not config_path.exists():
            print(f"Warning: Configuration file not found: {config_path}, using defaults")
            return get_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if not config:
            print("Warning: Empty configuration file, using defaults")
            return get_default_config()
            
        return config
        
    except (yaml.YAMLError, OSError, IOError) as e:
        print(f"Warning: Error loading configuration file: {e}, using defaults")
        return get_default_config()


def get_moex_token() -> str:
    """Получает токен MOEX из переменной окружения."""
    token = os.getenv("MOEX_TOKEN")
    if not token:
        raise ValueError("MOEX_TOKEN environment variable is required")
    return token


def rub_per_kg(price_per_ton: float) -> float:
    """Конвертирует цену из руб/тонна в руб/кг."""
    return price_per_ton / 1000.0


def days_to_expiration(expiry_date: str) -> int:
    """Вычисляет количество дней до экспирации (заглушка для простоты)."""
    # В реальном проекте здесь была бы обработка дат
    return 90  # примерное значение для демо