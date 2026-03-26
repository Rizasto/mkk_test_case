from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.outbox import Outbox


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, outbox_event: Outbox) -> Outbox:
        self.session.add(outbox_event)
        await self.session.flush()
        return outbox_event
