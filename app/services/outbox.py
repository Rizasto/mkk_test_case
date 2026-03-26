from sqlalchemy.ext.asyncio import AsyncSession

from app.broker.publisher import RabbitPublisher
from app.broker.schemas import PaymentCreatedEvent
from app.repositories.outbox import OutboxRepository


class OutboxService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.outbox_repository = OutboxRepository(session)
        self.publisher = RabbitPublisher()

    async def publish_new_events(self, batch_size: int = 100) -> int:
        events = await self.outbox_repository.get_unpublished_batch(limit=batch_size)
        published_count = 0

        for outbox_event in events:
            try:
                payload = PaymentCreatedEvent(**outbox_event.payload)
                await self.publisher.publish_payment_created(payload)
                await self.outbox_repository.mark_as_published(outbox_event)
                await self.session.commit()
                published_count += 1
            except Exception as exc:
                await self.outbox_repository.mark_as_failed(
                    outbox_event=outbox_event,
                    error_message=str(exc),
                )
                await self.session.commit()

        return published_count
