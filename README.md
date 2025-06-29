# Учет бюджета

Простой FastAPI-бекенд для учета доходов, расходов и целей накоплений.

Все тексты интерфейса и комментарии написаны на русском языке.

Поддерживаются базовые CRUD-операции для категорий, операций и целей.

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
