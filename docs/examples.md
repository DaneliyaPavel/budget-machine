# Примеры использования API

Ниже приведены примеры взаимодействия с сервером через `curl`.

## Запуск без Docker

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Переменные окружения:
- `DATABASE_URL` — строка подключения к PostgreSQL (по умолчанию SQLite);
- `SECRET_KEY` — ключ для подписи JWT;
- `TELEGRAM_TOKEN` и `TELEGRAM_CHAT_ID` — для уведомлений в Telegram.

## Создание пользователя и получение токена

```bash
curl -X POST "http://127.0.0.1:8000/пользователи/" \
     -H "Content-Type: application/json" \
     -d '{"email": "me@example.com", "password": "secret"}'

curl -X POST "http://127.0.0.1:8000/пользователи/token" \
     -d "username=me@example.com&password=secret" \
     -H "Content-Type: application/x-www-form-urlencoded"
```

## Создание категории с лимитом

```bash
curl -X POST "http://127.0.0.1:8000/категории/" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Продукты", "monthly_limit": 15000}'
```

## Импорт операций из CSV

CSV-файл должен содержать колонки `amount`, `currency`, `description`, `category_id` и опционально `created_at` в ISO-формате.

```bash
curl -X POST "http://127.0.0.1:8000/операции/импорт" \
     -H "Authorization: Bearer <token>" \
     -F "file=@transactions.csv"
```

## Получить операции за период

```bash
curl "http://127.0.0.1:8000/операции/?start=2025-06-01T00:00:00&end=2025-06-30T23:59:59" \
     -H "Authorization: Bearer <token>"
```
Можно указать `category_id`, чтобы вывести операции только по конкретной категории.

## Прогноз расходов на месяц

```bash
curl "http://127.0.0.1:8000/аналитика/прогноз?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

## Расходы по дням

```bash
curl "http://127.0.0.1:8000/аналитика/дни?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

## Баланс месяца

```bash
curl "http://127.0.0.1:8000/аналитика/баланс?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

## Прогресс по целям

```bash
curl "http://127.0.0.1:8000/аналитика/цели" \
     -H "Authorization: Bearer <token>"
```

## Импорт из Тинькофф по токену

```bash
curl -X POST "http://127.0.0.1:8000/тинькофф/импорт" \
     -H "Authorization: Bearer <token>" \
     -d "token=<tinkoff_token>&start=2025-06-01T00:00:00&end=2025-06-30T23:59:59"
```

## Импорт операций из другого банка

```bash
curl -X POST "http://127.0.0.1:8000/банки/импорт" \
     -H "Authorization: Bearer <token>" \
     -d "bank=sber&token=<access_token>&start=2025-06-01T00:00:00&end=2025-06-30T23:59:59"
```

## Присоединиться к счёту

```bash
curl -X POST "http://127.0.0.1:8000/пользователи/join" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"account_id": 1}'
```

