import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PaymentStatus
from app.db.models.outbox import Outbox
from app.db.models.payment import Payment
from app.repositories.outbox import OutboxRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentCreateRequest


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payment_repository = PaymentRepository(session)
        self.outbox_repository = OutboxRepository(session)

    async def create_payment(
            self,
            payload: PaymentCreateRequest,
            idempotency_key: str,
    ) -> Payment:
        existing_payment = await self.payment_repository.get_by_idempotency_key(
            idempotency_key=idempotency_key,
        )
        if existing_payment is not None:
            return existing_payment

        payment = Payment(
            amount=payload.amount,
            currency=payload.currency.upper(),
            description=payload.description,
            metadata_json=payload.metadata,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=str(payload.webhook_url),
        )

        await self.payment_repository.add(payment)

        outbox_event = Outbox(
            event_type="payment.created",
            payload={
                "payment_id": str(payment.id),
                "idempotency_key": idempotency_key,
                "amount": str(payload.amount),
                "currency": payload.currency.upper(),
                "webhook_url": str(payload.webhook_url),
            },
        )
        await self.outbox_repository.add(outbox_event)

        await self.session.commit()
        await self.session.refresh(payment)
        return payment

    async def get_payment(self, payment_id: uuid.UUID) -> Payment:
        payment = await self.payment_repository.get_by_id(payment_id=payment_id)
        if payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )
        return payment
