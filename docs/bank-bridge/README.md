# Сервис Bank Bridge

Bank Bridge отвечает за обмен данными с внешними банковскими API и нормализацию полученных операций. Он работает отдельно от основного приложения, взаимодействуя с Kafka и системой мониторинга.

## Потоки данных

1. Bank Bridge получает операции из банков (по вебхуку и при полной синхронизации) и помещает их в топик `bank.raw`.
2. Отдельный consumer считывает сообщения из `bank.raw`, вызывает `normalizer.process` и публикует результат в `bank.norm` либо `bank.err`.
3. Нормализованные данные далее обрабатываются ядром системы.

Пример схемы потоков данных приведён в файле `dataflow.puml`.

## Схемы сообщений

В каталоге `schemas/bank-bridge` описаны JSON‑схемы для трёх типов сообщений:

- **bank.raw** – исходные параметры запроса к банку. Сообщение содержит
  обязательные поля `user_id`, `bank_txn_id`, `bank_id` и `payload`.
- **bank.norm** – нормализованная операция после успешной обработки.
- **bank.err** – информация об ошибке с исходным сообщением.

Каждая схема версионируется и проверяется в тестах `tests/bank_bridge/test_contracts.py`.
Схемы располагаются в каталогах `<topic>/<version>`. При изменении
спецификации создаётся новый каталог версии, а изменения вносятся через
pull request. На старте сервиса все схемы автоматически регистрируются в
Apicurio Schema Registry, что позволяет воспроизвести состояние схем в
любом окружении.

## Переменные окружения

Для работы сервиса требуются следующие переменные:

- `KAFKA_BROKER_URL` – адрес брокера Kafka (по умолчанию `localhost:9092`);
- `BANK_RAW_TOPIC` – топик, куда приложение помещает исходные запросы;
- `BANK_BRIDGE_SYNC_DAYS` – число дней истории при полной синхронизации (по умолчанию `30`);
- `SCHEMA_REGISTRY_URL` – адрес Schema Registry;
- `BANK_BRIDGE_VAULT_URL` – URL Vault, например `https://vault.example.com`;
- `BANK_BRIDGE_VAULT_TOKEN` – токен доступа к Vault.
- `BANK_BRIDGE_<BANK>_RATE` – максимальная частота запросов к API банка;
- `BANK_BRIDGE_<BANK>_CAPACITY` – ёмкость окна для лимитера.

Токены банков хранятся в Vault по пути `bank_tokens/<bank>/<user_id>`.
Пример полного пути: `bank_tokens/tinkoff/42`.

## Ротация токенов

При запуске Bank Bridge стартует фоновая задача, которая раз в сутки
обновляет токены всех пользователей. Список `user_id` определяется через
Vault запросом `list` к каталогу `bank_tokens/<bank>/`. Если Vault не
вернул результат, список загружается из Core API, адрес которого задаётся
переменной `BANK_BRIDGE_CORE_URL`.

## Лимиты

Для контейнера сервиса в `docker-compose.yml` задано ограничение ресурсов: не более 1 CPU и 512 MB памяти.
При обращении к внешним API учитываются ответы 429, их количество фиксируется отдельной метрикой.

## Метрики

Сервис экспортирует метрики Prometheus на эндпойнте `/metrics`.
Все метрики имеют метку `bank` с названием коннектора.
Счётчик `bankbridge_error_total` также содержит метку `stage`:

- `bankbridge_fetch_latency_ms` – гистограмма времени вызова внешних API;
- `bankbridge_txn_count` – число обработанных банковских операций;
- `bankbridge_error_total` – количество ошибок при запросах к банкам (метки `bank` и `stage`);
- `bankbridge_rate_limited` – счётчик ответов с кодом 429.
- `bankbridge_circuit_open` – состояние circuit breaker (1 — открыт, 0 — закрыт).

## Проверка состояния

Эндпойнт `/healthz` проверяет возможность отправки сообщений в Kafka и доступ к
Vault. Отдельная база данных в Bank Bridge не используется, поэтому её
доступность не проверяется.

## REST‑эндпоинты

Ниже перечислены основные HTTP‑эндпоинты сервиса.

| Метод | Путь | Назначение | Параметры |
| ----- | ---- | ---------- | --------- |
| `POST` | `/connect/{bank}` | Получить ссылку для авторизации пользователя в выбранном банке | `user_id` (query), `bank` (path) |
| `GET` | `/status/{bank}` | Проверить состояние подключения к банку | `user_id` (query), `bank` (path) |
| `POST` | `/sync/{bank}` | Запланировать полную синхронизацию операций | `user_id` (query), `bank` (path) |
| `POST` | `/webhook/tinkoff/{user_id}` | Обработать webhook Тинькофф | `user_id` (path) |
| `GET` | `/metrics` | Метрики Prometheus | – |
| `GET` | `/healthz` | Проверка состояния сервиса | – |

Допустимые значения параметра `bank`: `tinkoff`, `sber`, `gazprom`, `alfa`, `vtb`.

Примеры:

```bash
curl -X POST "http://localhost:8080/connect/tinkoff?user_id=<uuid>"
curl -X POST "http://localhost:8080/sync/tinkoff?user_id=<uuid>"
```

## Политики надёжности

При работе с внешними API сервис применяет несколько механизмов надёжности:

- **Leaky Bucket** ограничивает частоту запросов до одного в секунду с запасом в
  пять запросов;
- при ошибках выполняется повтор с экспоненциальной задержкой, не более пяти
  попыток;
- **Circuit Breaker** открывается после трёх подряд неудачных запросов и
  блокирует дальнейшие обращения на 30 секунд.


## Логи

Сервис пишет структурированные логи в stdout в формате JSON. Пример
минимальной конфигурации Promtail для передачи логов в Loki:

```yaml
serverPort: 9080

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: bank-bridge
    static_configs:
      - targets: [localhost]
        labels:
          job: bank-bridge
          __path__: /var/log/containers/*bank-bridge*.log
```
Полный пример доступен в файле `promtail-example.yml`.

## Тестовый контур

Для локального тестирования используется `tests/bank_bridge/docker-compose.yml`. Он поднимает Kafka и несколько заглушек. Запуск:

```bash
docker compose -f tests/bank_bridge/docker-compose.yml up -d
```

После старта доступны следующие сервисы:
- Kafka на порту 9092;
- mock bank-api на порту 8081;
- mock Core API на порту 8200.

Интеграционные тесты запускаются командой:

```bash
pytest tests/bank_bridge
```

или через `make bankbridge-tests`.

### Проверка авторизации в песочнице

Для тестирования OAuth‑процесса с песочницей Тинькофф используется
скрипт `tests/bank_bridge/tinkoff_sandbox.py` на базе Playwright. Он
выполняет вход под тестовой учётной записью и ожидает редирект на
указанный в переменных окружения URL.

Перед запуском необходимо установить Playwright и загрузить браузер:

```bash
pip install playwright
playwright install chromium
```

После этого скрипт запускается командой:

```bash
python tests/bank_bridge/tinkoff_sandbox.py
```

Требуются переменные `TINKOFF_SANDBOX_LOGIN` и
`TINKOFF_SANDBOX_PASSWORD`.

## Локальное развёртывание

1. Скопируйте `env/.env.example` в `.env` и заполните переменные для доступа к банкам.
2. Соберите Docker‑образ и запустите контейнер API:

```bash
docker build -t bank-bridge -f services/bank_bridge/Dockerfile .
docker run --env-file .env -p 8080:8080 bank-bridge
```

3. В отдельном контейнере запустите consumer Kafka:

```bash
docker build -t bank-bridge-consumer -f services/bank_bridge/consumer.Dockerfile .
docker run --env-file .env bank-bridge-consumer
```

Сервис будет доступен на `http://localhost:8080`. Для разработки можно запустить его напрямую:

```bash
uvicorn services.bank_bridge.app:app --reload --port 8080
```
