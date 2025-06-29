# Учет бюджета

Простой FastAPI-бекенд для учета доходов, расходов и целей накоплений.

Все тексты интерфейса и комментарии написаны на русском языке.

Поддерживаются базовые CRUD-операции для категорий, операций и целей.


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
