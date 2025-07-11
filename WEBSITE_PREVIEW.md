# 🌐 Hedge Farm - Веб-интерфейс

## 📱 Что вы увидите в браузере

### 🏠 Главная страница: `http://localhost:8000/`

```json
{
    "service": "HedgeFarm Pricer",
    "version": "0.1.0", 
    "description": "API для расчета минимальной гарантированной цены",
    "endpoints": {
        "price": "/price - Основной расчет цены",
        "health": "/health - Проверка состояния сервиса",
        "detailed": "/price/detailed - Детальный анализ"
    }
}
```

### 📚 Swagger UI документация: `http://localhost:8000/docs`

**Красивый интерактивный интерфейс с:**

```
🎯 HedgeFarm Pricer API
API для расчета минимальной гарантированной цены при хеджировании сельхозпродуктов

📋 Эндпоинты:

1. GET / - Корневой эндпоинт  
   └─ Информация о сервисе

2. GET /health - Проверка здоровья сервиса
   └─ Статус подключения к MOEX

3. GET /price - Расчет минимальной гарантированной цены
   📋 Параметры:
   ├─ culture: wheat | corn | barley
   ├─ volume: объем в тоннах  
   └─ term_months: срок в месяцах
   
   📊 Ответ:
   ├─ floor_futures_rubkg: цена фьючерсов
   ├─ floor_put_rubkg: цена PUT опционов  
   ├─ floor_forward_rubkg: цена форвардов
   └─ recommended: рекомендация

4. GET /price/detailed - Детальный анализ
   📊 Расширенная информация по каждому инструменту

5. POST /price - Расчет с JSON параметрами
   📝 Тело запроса: PriceRequest
```

### 🎯 Пример ответа API

**Базовый расчет цены:**
```json
{
    "culture": "wheat",
    "volume_t": 1000,
    "term_m": 6,
    "floor_futures_rubkg": 14.64,
    "floor_put_rubkg": 14.69,
    "floor_forward_rubkg": 14.46,
    "recommended": "put",
    "calculated_at": "2025-07-11T15:02:08.778727"
}
```

**Детальный анализ:**
```json
{
    "futures": {
        "mgp_rub_kg": 14.58,
        "margin_required": 3300000.0,
        "leverage": 10.0,
        "hedging_efficiency": 0.88
    },
    "put_option": {
        "mgp_rub_kg": 14.69,
        "strike": 16500.0,
        "premium": 50.0,
        "delta": -0.24,
        "ladder_strikes": [[15675.0, 0.25], [16005.0, 0.25]]
    },
    "forward": {
        "mgp_rub_kg": 14.46,
        "discount_applied": 0.015,
        "no_margin_required": true
    },
    "market_context": {
        "futures_price": 16500.0,
        "volatility": 0.22,
        "usd_rate": 95.0
    }
}
```

### 🔧 Health Check: `http://localhost:8000/health`

```json
{
    "status": "healthy",
    "moex_connection": "ok", 
    "test_wheat_price": 16500.0,
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🎨 Визуальное описание

### Swagger UI выглядит как:

```
╔════════════════════════════════════════════════════════════╗
║  🎯 HedgeFarm Pricer API                                   ║
║  API для расчета минимальной гарантированной цены          ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  📂 default                                                ║
║                                                            ║
║  ▼ GET /        Корневой эндпоинт                         ║
║     └─ [Try it out] [Execute]                             ║
║                                                            ║
║  ▼ GET /health  Проверка здоровья сервиса                ║
║     └─ [Try it out] [Execute]                             ║
║                                                            ║
║  ▼ GET /price   Расчет минимальной гарантированной цены   ║
║     📋 Parameters:                                         ║
║     ├─ culture*    [wheat ▼]                              ║
║     ├─ volume*     [1000     ]                            ║
║     └─ term_months* [6       ]                            ║
║     └─ [Try it out] [Execute]                             ║
║                                                            ║
║  ▼ GET /price/detailed  Детальный анализ                 ║
║     └─ [Try it out] [Execute]                             ║
║                                                            ║
║  ▼ POST /price  Расчет с JSON параметрами                ║
║     📝 Request body:                                       ║
║     {                                                      ║
║       "culture": "wheat",                                  ║
║       "volume": 1000,                                      ║
║       "term_months": 6                                     ║
║     }                                                      ║
║     └─ [Try it out] [Execute]                             ║
╚════════════════════════════════════════════════════════════╝
```

### 🌟 Интерактивные возможности:

1. **"Try it out"** - позволяет редактировать параметры
2. **"Execute"** - выполняет запрос прямо в браузере  
3. **Response body** - показывает результат в JSON
4. **Response headers** - показывает HTTP заголовки
5. **Curl command** - генерирует готовую команду curl

### 🎯 Примеры curl команд:

```bash
# Базовый расчет
curl -X GET "http://localhost:8000/price?culture=wheat&volume=1000&term_months=6"

# Детальный анализ  
curl -X GET "http://localhost:8000/price/detailed?culture=wheat&volume=2000&term_months=9"

# POST запрос
curl -X POST "http://localhost:8000/price" \
     -H "Content-Type: application/json" \
     -d '{"culture":"wheat","volume":1000,"term_months":6}'

# Проверка здоровья
curl -X GET "http://localhost:8000/health"
```

## 🚀 Запуск для просмотра

```bash
# 1. Активировать окружение
source venv/bin/activate

# 2. Запустить сервер
uvicorn hedgefarm.service:app --reload --host 0.0.0.0 --port 8000

# 3. Открыть в браузере:
# http://localhost:8000/docs - Swagger UI
# http://localhost:8000/ - JSON API info  
# http://localhost:8000/health - Health check
```

---

**💡 Tip:** Swagger UI полностью интерактивен - можно тестировать все эндпоинты прямо в браузере без необходимости писать код или использовать curl!