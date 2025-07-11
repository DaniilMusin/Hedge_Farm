"""Утилитарные функции для hedgefarm-pricer."""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


def load_cfg() -> Dict[str, Any]:
    """Загружает конфигурацию из settings.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


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