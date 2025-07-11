
# HedgeFarm Pricer

FastAPI micro‑service that publishes *Minimum Guaranteed Price (MGP)* for a farmer.
The service pulls live futures & options quotes from Moscow Exchange (MOEX WHEAT),
adds platform fees, basis adjustments and risk add‑ons, then returns:

```json
{
  "culture": "wheat",
  "volume_t": 1000,
  "term_m": 6,
  "floor_futures": 15.98,
  "floor_put": 15.45,
  "floor_forward": 15.31,
  "recommended": "put"
}
```

## Key features

* **Options‑first**: PUT pricing with Black‑Scholes fallback.
* Futures engine with funding/commission model.
* Stress‑VaR & capital reserve check.
* Config‑driven parameters (`config/settings.yaml`).
* REST API generated from Pydantic models (`/docs`).

## Usage (local)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export MOEX_TOKEN="..."
uvicorn hedgefarm.service:app --reload
```

Open <http://127.0.0.1:8000/docs> for Swagger UI.

## Folder layout
```
hedgefarm-pricer/
├─ config/
│  └─ settings.yaml
├─ hedgefarm/
│  ├─ datasources.py
│  ├─ models.py
│  ├─ risk.py
│  ├─ service.py
│  └─ pricing/
│     ├─ futures.py
│     ├─ options.py
│     └─ aggregator.py
└─ tests/
```
