#!/usr/bin/env python3
"""
Пример использования HedgeFarm Pricer API.

Демонстрирует:
1. Прямой вызов модулей для расчета
2. HTTP API через requests
"""

import os
import sys
import requests
import json

# Добавляем путь к модулю
sys.path.append('.')

def example_direct_usage():
    """Пример прямого использования модулей."""
    print("=== Прямое использование модулей ===")
    
    try:
        from hedgefarm.datasources import MOEXClient
        from hedgefarm.pricing.aggregator import calculate_all_prices
        
        # Создаем клиент MOEX
        moex_client = MOEXClient()
        
        # Получаем рыночные данные
        market_data = moex_client.get_market_data("WHEAT")
        
        # Рассчитываем цены
        result = calculate_all_prices(market_data, volume=1000, term_months=6)
        
        print(f"Фьючерс: {result.floor_futures_rubkg:.2f} руб/кг")
        print(f"PUT опцион: {result.floor_put_rubkg:.2f} руб/кг")
        print(f"Форвард: {result.floor_forward_rubkg:.2f} руб/кг")
        print(f"Рекомендация: {result.recommended}")
        
    except Exception as e:
        print(f"Ошибка при прямом использовании: {e}")


def example_api_usage():
    """Пример использования через HTTP API."""
    print("\n=== Использование HTTP API ===")
    
    base_url = "http://127.0.0.1:8000"
    
    # Проверка здоровья сервиса
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Сервис работает")
        else:
            print("⚠ Проблемы с сервисом")
            return
    except requests.exceptions.RequestException:
        print("❌ Сервис недоступен. Запустите: uvicorn hedgefarm.service:app")
        return
    
    # Основной запрос расчета цены
    try:
        params = {
            "culture": "wheat",
            "volume": 1000,
            "term_months": 6
        }
        
        response = requests.get(f"{base_url}/price", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Результат расчета:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Ошибка API: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")


def example_post_request():
    """Пример POST запроса."""
    print("\n=== POST запрос ===")
    
    base_url = "http://127.0.0.1:8000"
    
    request_data = {
        "culture": "wheat",
        "volume": 5000,
        "term_months": 12
    }
    
    try:
        response = requests.post(
            f"{base_url}/price", 
            json=request_data, 
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Результат для {data['volume_t']} тонн на {data['term_m']} месяцев:")
            print(f"  Фьючерс: {data['floor_futures_rubkg']:.2f} руб/кг")
            print(f"  Опцион:  {data['floor_put_rubkg']:.2f} руб/кг")
            print(f"  Форвард: {data['floor_forward_rubkg']:.2f} руб/кг")
            print(f"  🎯 Рекомендация: {data['recommended']}")
        else:
            print(f"Ошибка: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")


def example_detailed_analysis():
    """Пример получения детального анализа."""
    print("\n=== Детальный анализ ===")
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        params = {
            "culture": "wheat",
            "volume": 2000,
            "term_months": 9
        }
        
        response = requests.get(f"{base_url}/price/detailed", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("📈 Фьючерсы:")
            futures = data.get("futures", {})
            print(f"  MGP: {futures.get('mgp_rub_kg', 0):.2f} руб/кг")
            print(f"  Маржа: {futures.get('margin_required', 0):,.0f} руб")
            print(f"  Плечо: {futures.get('leverage', 0):.1f}x")
            
            print("\n📊 PUT опционы:")
            puts = data.get("put_option", {})
            print(f"  MGP: {puts.get('mgp_rub_kg', 0):.2f} руб/кг")
            print(f"  Страйк: {puts.get('strike', 0):,.0f} руб/т")
            print(f"  Премия: {puts.get('premium', 0):.0f} руб/т")
            print(f"  Дельта: {puts.get('delta', 0):.3f}")
            
            print("\n🔄 Форвард:")
            forward = data.get("forward", {})
            print(f"  MGP: {forward.get('mgp_rub_kg', 0):.2f} руб/кг")
            print(f"  Дисконт: {forward.get('discount_applied', 0)*100:.1f}%")
            print(f"  Без маржи: {forward.get('no_margin_required', False)}")
            
        else:
            print(f"Ошибка: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")


if __name__ == "__main__":
    print("🌾 HedgeFarm Pricer - Примеры использования")
    print("=" * 50)
    
    # Прямое использование модулей
    example_direct_usage()
    
    # API примеры (работают только если сервис запущен)
    example_api_usage()
    example_post_request()
    example_detailed_analysis()
    
    print("\n" + "=" * 50)
    print("💡 Для запуска API сервера:")
    print("   uvicorn hedgefarm.service:app --reload")
    print("   Документация: http://127.0.0.1:8000/docs")