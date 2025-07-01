# Учет бюджета

[![CI](https://github.com/DaneliyaPavel/budget-machine/actions/workflows/ci.yml/badge.svg)](https://github.com/DaneliyaPavel/budget-machine/actions/workflows/ci.yml)

Простой FastAPI-бекенд для учета доходов, расходов и целей накоплений.

Все тексты интерфейса и комментарии написаны на русском языке.

Поддерживаются базовые CRUD-операции для категорий, операций и целей.

Все данные привязаны к аккаунту пользователя.
Несколько пользователей могут работать с одним счётом. Чтобы присоединиться к существующему счёту, используйте эндпоинт `/пользователи/join`.

Есть простой эндпоинт аналитики с суммой расходов по категориям за месяц.
Поддерживается мультивалютность: суммы автоматически переводятся в рубли по курсу ЦБ РФ.
Для категорий можно задавать месячный лимит расходов и получать отчёт о превышениях.

Пример запроса:

```bash
curl "http://127.0.0.1:8000/аналитика/категории?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

Отчёт о категориях, где превышен лимит:

```bash
curl "http://127.0.0.1:8000/аналитика/лимиты?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

При необходимости можно указать параметр `notify=true`, чтобы получить уведомление
в Telegram (нужны переменные окружения `TELEGRAM_TOKEN` и `TELEGRAM_CHAT_ID`).


## Быстрый старт

Установите зависимости:

```bash
pip install -r requirements.txt
```

Запустите сервер:

```bash
uvicorn app.main:app --reload
```

По умолчанию используется SQLite. Для PostgreSQL задайте переменную окружения `DATABASE_URL`.
Секретный ключ JWT задаётся через переменную окружения `SECRET_KEY`.
Для отправки уведомлений в Telegram установите `TELEGRAM_TOKEN` и `TELEGRAM_CHAT_ID`.

Создание пользователя:

```bash
curl -X POST "http://127.0.0.1:8000/пользователи/" \
     -H "Content-Type: application/json" \
     -d '{"email": "me@example.com", "password": "secret"}'
```

Получение токена:

```bash
curl -X POST "http://127.0.0.1:8000/пользователи/token" \
     -d "username=me@example.com&password=secret" \
     -H "Content-Type: application/x-www-form-urlencoded"
```

### Создание категории с лимитом

```bash
curl -X POST "http://127.0.0.1:8000/категории/" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Продукты", "monthly_limit": 15000}'
```

### Импорт операций из CSV

CSV-файл должен содержать колонки `amount`, `currency`, `description`, `category_id` и опционально `created_at` в ISO-формате.

Пример запроса:

```bash
curl -X POST "http://127.0.0.1:8000/операции/импорт" \
     -H "Authorization: Bearer <token>" \
     -F "file=@transactions.csv"
```

### Получить операции за период

```bash
curl "http://127.0.0.1:8000/операции/?start=2025-06-01T00:00:00&end=2025-06-30T23:59:59" \
     -H "Authorization: Bearer <token>"
```
При необходимости можно указать `category_id`, чтобы вывести операции только по конкретной категории.


### Прогноз расходов на месяц

```bash
curl "http://127.0.0.1:8000/аналитика/прогноз?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

### Расходы по дням

```bash
curl "http://127.0.0.1:8000/аналитика/дни?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

### Баланс месяца

```bash
curl "http://127.0.0.1:8000/аналитика/баланс?year=2025&month=6" \
     -H "Authorization: Bearer <token>"
```

### Прогресс по целям

```bash
curl "http://127.0.0.1:8000/аналитика/цели" \
     -H "Authorization: Bearer <token>"
```

### Импорт из Тинькофф по токену

```bash
curl -X POST "http://127.0.0.1:8000/тинькофф/импорт" \
     -H "Authorization: Bearer <token>" \
     -d "token=<tinkoff_token>&start=2025-06-01T00:00:00&end=2025-06-30T23:59:59"
```

### Импорт операций из другого банка

```bash
curl -X POST "http://127.0.0.1:8000/банки/импорт" \
     -H "Authorization: Bearer <token>" \
     -d "bank=sber&token=<access_token>&start=2025-06-01T00:00:00&end=2025-06-30T23:59:59"
```

### Присоединиться к счёту

```bash
curl -X POST "http://127.0.0.1:8000/пользователи/join" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"account_id": 1}'
```
## Проверка качества кода

Перед коммитом выполните `pre-commit run --all-files`.
Все тесты запускаются командой `pytest`.


## Запуск в Docker

Для удобного запуска окружения используйте `docker-compose`. Оно поднимает PostgreSQL, Redis и приложение вместе с Celery-воркером.

```bash
docker-compose up --build
```

Docker build configuration resides in `backend/Dockerfile`.

API будет доступно по адресу `http://localhost:8000`.

## Миграции

Для управления схемой БД используется Alembic. URL базы берётся из
переменной окружения `DATABASE_URL`.

Применить все миграции:

```bash
alembic upgrade head
```

Создать новую миграцию после изменения моделей:

```bash
alembic revision --autogenerate -m "comment"
```

## Telegram-бот

Для уведомлений и получения кратких отчётов можно запустить простого Telegram-бота.
Нужен токен бота в переменной `TELEGRAM_TOKEN` и идентификатор пользователя
в `BOT_USER_ID` (по умолчанию `1`).

```bash
export TELEGRAM_TOKEN=<token>
export BOT_USER_ID=1
python -m app.telegram_bot
```

Доступны команды `/summary` для отчёта по категориям и `/limits` для проверки
превышения лимитов.

## Веб-клиент

В каталоге `frontend` находится минимальное приложение на React + TypeScript.
Для разработки необходим Node.js. После установки зависимостей запустите:

```bash
cd frontend
npm install
npm run dev
```

Для сборки PWA выполните:

```bash
npm run build
```

Готовая сборка появится в каталоге `frontend/dist`.

Приложение откроется на `http://localhost:3000` и будет проксировать запросы к API.

## Мониторинг

После запуска приложения метрики Prometheus доступны по пути `/metrics`.
Библиотека `prometheus-fastapi-instrumentator` подключается при старте сервера.

В каталоге `monitoring` находится пример дашборда Grafana
`grafana_dashboard.json`.
Создайте источник данных Prometheus в Grafana и импортируйте этот файл,
чтобы наблюдать статистику запросов.

## Deployment

Инструкции по развёртыванию инфраструктуры Terraform и деплою Helm/Argo CD описаны в [docs/deployment.md](docs/deployment.md).
