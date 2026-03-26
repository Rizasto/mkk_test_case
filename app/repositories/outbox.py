from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import OutboxStatus
from app.db.models.outbox import Outbox


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, outbox_event: Outbox) -> Outbox:
        self.session.add(outbox_event)
        await self.session.flush()
        return outbox_event

    async def get_unpublished_batch(self, limit: int = 100) -> list[Outbox]:
        stmt = (
            select(Outbox)
            .where(Outbox.status == OutboxStatus.NEW)
            .order_by(Outbox.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_published(self, outbox_event: Outbox) -> None:
        outbox_event.status = OutboxStatus.PUBLISHED
        outbox_event.published_at = datetime.now(UTC)
        outbox_event.last_error = None
        await self.session.flush()

    async def mark_as_failed(self, outbox_event: Outbox, error_message: str) -> None:
        outbox_event.attempts += 1
        outbox_event.last_error = error_message
        await self.session.flush()
