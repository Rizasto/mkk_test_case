from app.broker.publisher import RabbitPublisher
from app.broker.rabbit import PAYMENTS_NEW_QUEUE, broker
from app.broker.schemas import PaymentCreatedEvent, PaymentDlqEvent
from app.db.session import AsyncSessionLocal
from app.services.processing import PaymentProcessingService
from app.services.webhook import WebhookDeliveryError, WebhookService


@broker.subscriber(PAYMENTS_NEW_QUEUE)
async def handle_payment_created(event: PaymentCreatedEvent) -> None:
    async with AsyncSessionLocal() as session:
        processing_service = PaymentProcessingService(session=session)
        webhook_service = WebhookService()
        publisher = RabbitPublisher()

        payment = await processing_service.process_payment(event.payment_id)

        try:
            await webhook_service.send_payment_result(payment)
        except WebhookDeliveryError as exc:
            dlq_event = PaymentDlqEvent(
                payment_id=str(payment.id),
                idempotency_key=payment.idempotency_key,
                webhook_url=payment.webhook_url,
                reason=str(exc),
            )
            await publisher.publish_payment_dlq(dlq_event)
            print(
                f"Webhook delivery failed permanently for payment_id={payment.id}. "
                "Message sent to DLQ."
            )
