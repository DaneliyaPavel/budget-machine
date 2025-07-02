# Учет бюджета

[![CI](https://github.com/DaneliyaPavel/budget-machine/actions/workflows/ci.yml/badge.svg)](https://github.com/DaneliyaPavel/budget-machine/actions/workflows/ci.yml)

Небольшой FastAPI-бекенд для учёта доходов, расходов и целей накоплений. Все примеры и интерфейс на русском языке.

## Быстрый старт

```bash
make dev  # запускает docker-compose и открывает http://localhost:8000/docs
make ci   # локальный запуск ruff, black, mypy и pytest
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

## Вклад

Правила участия описаны в [CONTRIBUTING.md](CONTRIBUTING.md).
