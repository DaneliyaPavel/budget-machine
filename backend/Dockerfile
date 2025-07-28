FROM python:3.12-slim
WORKDIR /app

# Добавьте эту строку для установки системных библиотек
RUN apt-get install -y --no-install-recommends libpq-dev=15.5-0ubuntu0.24.04.1 gcc=4:11.3.0-1ubuntu1~24.04.1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
