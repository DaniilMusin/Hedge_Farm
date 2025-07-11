
# Репозиторий `hedgefarm-pricer` — структура и логика

## 1 / Идея

*Сервису нужен «одночисловой» индикатор — **Минимальная гарантированная цена (MGP)**,* которую мы обещаем фермеру после хеджа.
Алгоритм берёт **live‑котировки пшеницы** на Московской бирже (фьючерс WHEAT и опционы на него), накладывает:

* издержки биржи (комиссии, ГО‑финансирование);
* величину премии PUT или спреда «фьючерс‑форвард»;
* наш риск‑маржин и комиссию 0,8 – 1,2 %;
* базисный дисконт (Новороссийск → «с поля»).

Результат — значение «≥ Х руб./кг», которое прямо выводится на лендинге калькулятора.

---

## 2 / Архитектура репозитория

```
hedgefarm-pricer/
├── README.md          ← этот файл
├── requirements.txt   ← pandas, numpy, requests, pydantic, scipy, fastapi
├── config/
│   └── settings.yaml  ← ключи API, коэффициенты (комиссия, ГО, дисконты)
├── hedgefarm/
│   ├── __init__.py
│   ├── models.py      ← Pydantic‑схемы котировок и выдачи
│   ├── datasources.py ← обёртка над REST/FIX MOEX
│   ├── pricing/
│   │   ├── futures.py ← расчёт эффективной цены при хедже фьючерсом
│   │   ├── options.py ← блэк‑шолз + дискретная волатильность MOEX
│   │   └── aggregator.py  ← выбирает "оптимум / гибкость / без‑маржи"
│   ├── risk.py        ← stress‑VAR + потребность в собственном капитале
│   ├── service.py     ← FastAPI‑эндпоинт /price?culture=wheat&volume=...
│   └── utils.py
└── tests/
    ├── test_futures.py
    ├── test_options.py
    └── test_api.py
```

---

## 3 / Алгоритм расчёта MGP (упрощённая математика)

### 3.1 Получение рынка

```python
quote_fut  = moex.get_last_price('WHEAT')          # ₽/т
quote_puts = moex.get_option_chain('WHEAT', 'P')   # страйки, вола, премия
usd_rate   = moex.get_last_price('USD/RUB_TOM')
```

### 3.2 Фьючерс‑хедж («Оптимум»)

```
Цена фиксации = P_fut
Мин. цена (рубы/кг) = (P_fut – комисс – базис – ф/дисконт) / 1000
```

*Комиссии* = 0,013 % × 2 стороны + стоимость финансирования ГО:

$$
Fin = P_{fut}\times L \times \frac{GO}{365}\times D
$$

где **L** — леверидж (10 %), **D** — дней до экспирации.

### 3.3 Опцион‑PUT («Гибкость»)

*Страйк* выбираем равным ближайшей рыночной цене.
Цена «пола»:

$$
MGP = \frac{K - Premium - Basis - Fee}{1000}
$$

*Premium* берётся из биржевого стакана; если ликвидность низка, внутренняя Black‑Scholes:

$$
C_{put} = K e^{-rT}\Phi(-d_2) - S e^{-qT}\Phi(-d_1)
$$

где $S=P_{fut}$, $T$ — время до экспирации, $\sigma$ — годовая волатильность (скользящее sd 10‑дн.).

### 3.4 Форвард‑хедж («Без‑маржи»)

$$
MGP = \frac{P_{fut} (1-\delta) - Fee - Basis}{1000}
$$

$\delta$ — дисконт 1–2 % за отсутствие маржи; задаётся в `settings.yaml`.

### 3.5 Агрегация

```python
mgp_fut = futures.floor_price(quote_fut, term)
mgp_put = options.floor_price(quote_puts, quote_fut, term)
mgp_for = forward.floor_price(quote_fut, term)

best   = max(mgp_fut, mgp_put, mgp_for)  # "гарантия выше"
output = {
    "futures": mgp_fut,
    "put":     mgp_put,
    "forward": mgp_for,
    "recommended": best
}
```

### 3.6 Stress‑Risk и лимит «от платформы»

Алгоритм просчитывает VAR(99 %) на горизонте T:

* импортирует 10‑летнюю историю WHEAT;
* клёвый метод Cornish‑Fisher для «толстых хвостов»;
* добавляет базисное смещение (γ = 250 руб./т).

Если потребность в капитале > резерв 50 млн ₽, цена автоматически занижается на величину *Surcharge*
(см. рисковый коэффициент `alpha_capital` в настройках).

---

## 4 / Энд‑поинт FastAPI

```python
@app.get("/price", response_model=QuoteOut)
async def get_price(culture: str, volume: int, term_months: int = 6):
    data = pricer.calculate(culture, volume, term_months)
    return data
```

Возвращает JSON:

```json
{
  "culture": "wheat",
  "volume_t": 1000,
  "term_m": 6,
  "floor_futures_rubkg": 15.98,
  "floor_put_rubkg": 15.45,
  "floor_forward_rubkg": 15.31,
  "recommended": "futures"
}
```

---

## 5 / Параметры, настраиваемые в `settings.yaml`

```yaml
# комиссия платформы
fee_pct:
  futures: 0.008          # 0,8 %
  put:     0.010
  forward: 0.012
# базисный дисконт РО -> CPT Новороссийск, руб/т
basis_discount: 1600
# дисконт форварда
forward_delta_pct: 0.015
# гарант. обеспечение
go_pct: 0.10
risk:
  capital_reserve: 50000000   # 50 млн
  alpha_capital: 0.1
```

---

## 6 / Тест‑каверидж

* Юнит‑тесты каждой формулы (pytest).
* Интеграционный тест обращается к **sandbox MOEX** и проверяет:

  * латентность ответа < 500 мс;
  * через faker () имитируется рост цены ↑30 % → check risk‑surcharge.

---

## 7 / Как запустить локально

```bash
git clone https://github.com/your-org/hedgefarm-pricer.git
cd hedgefarm-pricer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export MOEX_TOKEN="…"
uvicorn hedgefarm.service:app --reload
# открыть http://127.0.0.1:8000/docs
```

---

## 8 / Дальнейшие улучшения (issues ‑ backlog)

* **CVaR‑оптимизация**: вместо VAR взять Conditional VAR для хвостовых рисков.
* **Delta‑hedge for PUT**: динамически корректировать фьючерс‑позицию против проданных опционов.
* **Machine‑learning**: LSTM‑модель короткосрочного базиса.
* **Caching layer** через Redis для котировок (TTL 2 сек).

---

### Как использовать в GitHub‑пиче

* Копируете README + структуру, публикуете (можно пустые `.py` с docstring‑ами).
* Добавляете 2‑3 unit‑test и workflow *pytest + black* — выглядит «живым» проектом.
* В pitch‑deck вставляете диаграмму архитектуры из раздела 2.

Готово — у вас «обширный и сложный» алгоритм, который демонстрирует и цену‑для‑фермера, и серьёзный risk‑engine.
