# Учет бюджета

[![CI](https://github.com/DaneliyaPavel/budget-machine/actions/workflows/ci.yml/badge.svg)](https://github.com/DaneliyaPavel/budget-machine/actions/workflows/ci.yml)

Небольшой FastAPI-бекенд для учёта доходов, расходов и целей накоплений. Все примеры и интерфейс на русском языке.

### Требования к базе данных

Приложение использует PostgreSQL 16 с расширениями TimescaleDB и PostGIS. В локальной разработке
достаточно Docker-образа `timescale/timescaledb:2-postgis-16`.

## Установка зависимостей

```bash
pip install -r requirements.txt
pip install -r backend/requirements-dev.txt  # для разработки
```

## Быстрый старт

```bash
make dev  # запускает docker-compose и открывает http://localhost:8000/docs
make ci   # локальный запуск ruff, black, mypy и pytest
```

Для работы в [devcontainer](https://containers.dev/) предусмотрена команда

```bash
make devcontainer
```

### Миграции и документация

Перед первым запуском выполните миграции базы данных:

```bash
alembic upgrade head
```

Файл OpenAPI можно сгенерировать командой:

```bash
make openapi
```

gRPC-сервисы генерируются аналогично:

```bash
make proto
```

Для создания демонстрационного пользователя выполните:

```bash
make demo_user
```

Полные примеры запросов смотрите в [docs/examples.md](docs/examples.md). Инструкции по развёртыванию доступны в [docs/deployment.md](docs/deployment.md).

## Структура проекта

- `backend/app` — исходный код FastAPI
- `backend/tests` — тесты backend
- `infra/terraform` — инфраструктура в Terraform
- `infra/helm` и `infra/argocd` — файлы развёртывания в Kubernetes
- `frontend/pwa` — PWA на React
- `frontend/web` — веб-клиент на Next.js
- `services/` — дополнительные сервисы
- `docs/` — документация

## gRPC

Сервис LedgerService можно запустить командой:

```bash
python -m backend.app.grpc.server
```

Пример запроса с использованием `grpcurl`:

```bash
grpcurl -plaintext -d '{"account_id":"<uuid>"}' localhost:50051 ledger.LedgerService.GetBalance
```

## Дополнительные зависимости

Для проверки кода в репозитории настроены [pre-commit](https://pre-commit.com/)
хуки. Установите их командой `pre-commit install`, а затем используйте
`pre-commit run --all-files` перед созданием pull request. Эта команда запускает все проверки из конфигурации.

В CI выполняется анализ безопасности исходного кода с помощью [CodeQL и других job'ов](https://github.com/DaneliyaPavel/budget-machine/security/code-scanning).

## Инструменты безопасности

- Hadolint
- Gitleaks
- tfsec
- Terrascan
- Semgrep

## Вклад

Правила участия описаны в [CONTRIBUTING.md](CONTRIBUTING.md).
