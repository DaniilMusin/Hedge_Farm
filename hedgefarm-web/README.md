# HedgeFarm Web

Полный веб-сайт для платформы хеджирования сельскохозяйственных рисков.

## Структура проекта

- `backend/` - FastAPI сервер
- `frontend/` - React + TypeScript + Tailwind CSS
- `nginx/` - Конфигурация reverse proxy
- `docker-compose.yml` - Оркестрация сервисов

## Запуск

```bash
git clone https://github.com/<user>/hedgefarm-web.git
cd hedgefarm-web
docker-compose up --build
```

## Доступные сервисы

- `http://localhost` — React SPA
- `http://localhost/api/docs` — Swagger FastAPI
- Здоровье: `curl http://localhost/health`

## Интеграция с алгоритмом

Проект использует алгоритм хеджирования из репозитория `Hedge_Farm` как зависимость через pip.
При каждом `docker-compose build` скачивается свежая версия алгоритма.

## Разработка

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```