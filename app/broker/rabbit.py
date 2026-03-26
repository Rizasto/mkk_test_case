from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitQueue

from app.core.config import get_settings

settings = get_settings()

PAYMENTS_NEW_QUEUE = RabbitQueue(
    "payments.new",
    durable=True,
)

PAYMENTS_DLQ = RabbitQueue(
    "payments.dlq",
    durable=True,
)

broker = RabbitBroker(settings.rabbitmq_url)
stream_app = FastStream(broker)
