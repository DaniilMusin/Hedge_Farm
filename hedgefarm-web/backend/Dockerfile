FROM python:3.12-slim

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
ENV PYTHONPATH=/code
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]