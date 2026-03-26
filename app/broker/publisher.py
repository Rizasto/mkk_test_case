from app.broker.rabbit import PAYMENTS_DLQ, PAYMENTS_NEW_QUEUE, broker
from app.broker.schemas import PaymentCreatedEvent, PaymentDlqEvent


class RabbitPublisher:
    async def publish_payment_created(self, event: PaymentCreatedEvent) -> None:
        await broker.publish(
            event,
            queue=PAYMENTS_NEW_QUEUE,
            persist=True,
        )

    async def publish_payment_dlq(self, event: PaymentDlqEvent) -> None:
        await broker.publish(
            event,
            queue=PAYMENTS_DLQ,
            persist=True,
        )
