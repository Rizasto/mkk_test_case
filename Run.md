# Run app

## Быстрый запуск
Для запуская потребуется docker и docker-compose
```bash
docker compose up --build
```

После запуска доступны:

- API: `http://localhost:8001`
- Swagger: `http://localhost:8001/docs`
- RabbitMQ UI: `http://localhost:15672`

## Основные заголовки

Для всех запросов к API нужны заголовки(Headers):

```http
X-API-Key: *Уникальный ключ*
```

Для создания платежа также нужен:

```http
Idempotency-Key: *Другой уникальный ключ*
```

## Проверка API

## 1. Создание платежа

**POST** `/api/v1/payments`

Пример body:

```json
{
  "amount": "100.00",
  "currency": "rub",
  "description": "Test payment",
  "metadata": {
    "order_id": "123"
  },
  "webhook_url": "https://webhook.site/your-unique-url"
}
```

Ожидаемый результат:
- HTTP `202`
- `status = pending`
- `currency = RUB`
- в БД появляется запись в `payments`
- в БД появляется запись в `outbox`

В качестве ответа отдается:
- `id`
- `status`
- `created_at`

## 2. Получение платежа по ID

**GET** `/api/v1/payments/{payment_id}`

Ожидаемый результат:
- HTTP `200`
- возвращается созданный платёж

## 3. Идемпотентность

Повторно отправить **тот же POST** с тем же `Idempotency-Key`.

Ожидаемый результат:
- новый платёж не создаётся
- возвращается уже существующий платёж
- в таблице `payments` остаётся одна запись

## Happy Path

### Через Swagger

1. Открыть `http://localhost:8001/docs`
2. Вызвать `POST /api/v1/payments`
3. Использовать валидный `webhook_url`, например `webhook.site`
4. После создания платежа подождать несколько секунд
5. Вызвать `GET /api/v1/payments/{payment_id}`

Ожидаемый результат:
- статус меняется с `pending` на `succeeded` или `failed`
- в `webhook.site` появляется POST-запрос
- в таблице `outbox` событие имеет статус `published`

## Проверка webhook

Самый удобный способ — использовать `https://webhook.site/`.

1. Открыть `webhook.site`
2. Получить уникальный URL
3. Подставить его в `webhook_url`
4. Создать платёж

Ожидаемый результат:
- webhook приходит в `webhook.site`
- в body есть `payment_id`, `status`, `amount`, `currency`, `metadata`, `processed_at`

## Проверка DLQ

Использовать заведомо невалидный webhook URL, например:

```text
http://host.docker.internal:9999/webhook
```

Шаги:
1. Создать платёж через `POST /api/v1/payments`
2. Дождаться обработки consumer-ом
3. Проверить RabbitMQ UI по адресу: `localhost:15672`

Ожидаемый результат:
- платёж обработан
- webhook несколько раз переотправлялся
- после исчерпания retry сообщение попадает в очередь `payments.dlq`

## Что смотреть в RabbitMQ

В UI RabbitMQ полезно проверять:

- очередь `payments.new`
- очередь `payments.dlq`
- наличие сообщений в DLQ при сломанном webhook

## Что смотреть в БД

### Таблица `payments`
Проверять:
- `status`
- `processed_at`
- `idempotency_key`

### Таблица `outbox`
Проверять:
- `event_type`
- `status`
- `attempts`
- `last_error`

## Проверка ошибок API

### Неверный API key
Ожидается:
- `403 Forbidden`

### Пустой `Idempotency-Key`
Ожидается:
- `400 Bad Request`

### Отсутствующий `Idempotency-Key`
Ожидается:
- `422 Unprocessable Entity`

### Неизвестный `payment_id`
Ожидается:
- `404 Not Found`

## Локальный запуск тестов
