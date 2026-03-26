import asyncio
import random
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PaymentStatus
from app.repositories.payment import PaymentRepository


class PaymentProcessingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payment_repository = PaymentRepository(session)

    async def process_payment(self, payment_id: str):
        payment = await self.payment_repository.get_by_id(uuid.UUID(payment_id))
        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        await asyncio.sleep(random.randint(2, 5))

        new_status = PaymentStatus.SUCCEEDED if random.random() < 0.9 else PaymentStatus.FAILED

        await self.payment_repository.update_status(payment, new_status)
        await self.session.commit()
        await self.session.refresh(payment)
        return payment
