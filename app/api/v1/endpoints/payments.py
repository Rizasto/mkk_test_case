import uuid

from fastapi import APIRouter

from app.api.deps import ApiKeyDep, DbSessionDep, IdempotencyKeyDep
from app.db.models.payment import Payment
from app.schemas.payment import PaymentCreateRequest, PaymentFullResponse, PaymentResponse
from app.services.payment import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


def build_payment_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(id=payment.id, status=payment.status, created_at=payment.created_at)


def build_payment_full_response(payment: Payment) -> PaymentFullResponse:
    return PaymentFullResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata_json,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
        processed_at=payment.processed_at,
    )


@router.post("", response_model=PaymentResponse, status_code=202)
async def create_payment(
    payload: PaymentCreateRequest,
    session: DbSessionDep,
    _: ApiKeyDep,
    idempotency_key: IdempotencyKeyDep,
) -> PaymentResponse:
    service = PaymentService(session=session)
    payment = await service.create_payment(
        payload=payload,
        idempotency_key=idempotency_key,
    )
    return build_payment_response(payment)


@router.get("/{payment_id}", response_model=PaymentFullResponse, status_code=200)
async def get_payment(
    payment_id: uuid.UUID,
    session: DbSessionDep,
    _: ApiKeyDep,
) -> PaymentFullResponse:
    service = PaymentService(session=session)
    payment = await service.get_payment(payment_id=payment_id)
    return build_payment_full_response(payment)
