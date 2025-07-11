FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY hedgefarm/ ./hedgefarm/
COPY config/ ./config/

# Создаем пользователя для безопасности
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порт
EXPOSE 8000

# Задаем переменные окружения
ENV PYTHONPATH=/app
ENV MOEX_TOKEN=""

# Команда запуска
CMD ["uvicorn", "hedgefarm.service:app", "--host", "0.0.0.0", "--port", "8000"]