
## Содержание

- [Реализовано](#Реализовано)
- [Что именно закрывает ТЗ](#что-именно-закрывает-тз)
- [Стек](#стек)
- [Архитектура](#архитектура)
- [Поток обработки](#поток-обработки)
- [Статусы](#статусы)
- [Бытрый запуск](Run.md)


## Реализовано

### API
- `POST /api/v1/payments` — создание платежа
- `GET /api/v1/payments/{payment_id}` — получение платежа по ID

### Безопасность и валидация
- аутентификация через `X-API-Key`
- идемпотентность через `Idempotency-Key`
- валидация входного payload
- нормализация валюты в uppercase

### Persistence layer
- таблица `payments`
- таблица `outbox`
- Alembic migrations
- запись `payment` и `outbox` в **одной транзакции**

### Очередь и сообщения
- публикация событий в очередь `payments.new`
- один consumer, который:
  - получает сообщение из очереди
  - эмулирует обработку платежа (`2–5 сек`)
  - выставляет итоговый статус (`90% success`, `10% failed`)
  - обновляет запись в БД
  - отправляет webhook
  - делает retry с backoff при ошибках отправки webhook
  - отправляет сообщение в `payments.dlq` после исчерпания попыток

### Infra
- Docker / Docker Compose
- RabbitMQ
- PostgreSQL
- GitHub Actions CI
- pytest + Ruff

---

## Что именно закрывает ТЗ

- при создании платежа событие публикуется в очередь `payments.new`
- есть один consumer, выполняющий всю бизнес-обработку
- есть PostgreSQL с таблицами `payments` и `outbox`
- применён **Outbox pattern**
- реализованы повторные попытки при ошибках отправки webhook
- реализован DLQ
- приложение запускается через Docker

---

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- RabbitMQ
- FastStream
- httpx
- pytest / pytest-asyncio
- Ruff

---

## Архитектура

Сервис состоит из двух основных процессов:

### `app`
HTTP API, которое:
- принимает запросы на создание платежей
- проверяет `X-API-Key`
- проверяет `Idempotency-Key`
- создаёт запись в `payments`
- создаёт запись в `outbox`

### `worker`
Фоновый процесс, который:
- публикует события из `outbox` в RabbitMQ
- слушает очередь `payments.new`
- обрабатывает платёж
- обновляет БД
- отправляет webhook
- делает retry/backoff при ошибке webhook
- отправляет сообщение в DLQ

А также:

### `rabbitmq`
Брокер сообщений:
- хранит сообщения
- отдаёт их consumer-у
- содержит основную очередь и DLQ

### `db`
Источник истины:
- хранит `payments`
- хранит `outbox`

---

## Поток обработки

1. Клиент вызывает `POST /api/v1/payments`
2. API проверяет `X-API-Key` и `Idempotency-Key`
3. В БД создаются:
   - запись в `payments`
   - запись в `outbox`
4. Worker публикует событие из `outbox` в очередь `payments.new`
5. Consumer получает сообщение из `payments.new`
6. Consumer эмулирует обработку платежа
7. Consumer обновляет статус платежа в БД
8. Consumer отправляет webhook
9. Если webhook не доставлен:
   - выполняются повторные попытки с backoff
   - после исчерпания попыток сообщение отправляется в `payments.dlq`

---

## Статусы

### Payment status
- `pending` - в ожидании
- `succeeded` - успешно
- `failed` - не успешно

### Outbox status
- `new` - новый
- `published` - опубликованный
- `failed` - неуспешный