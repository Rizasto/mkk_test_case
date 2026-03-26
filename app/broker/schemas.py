from pydantic import BaseModel


class PaymentCreatedEvent(BaseModel):
    payment_id: str
    idempotency_key: str
    amount: str
    currency: str
    webhook_url: str


class PaymentDlqEvent(BaseModel):
    payment_id: str
    idempotency_key: str
    webhook_url: str
    reason: str
