import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.core.enums import PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12)
    currency: str = Field(..., min_length=3, max_length=3)
    description: str | None = None
    metadata: dict[str, Any] | None = None
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: PaymentStatus
    created_at: datetime


class PaymentFullResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount: Decimal
    currency: str
    description: str | None
    metadata: dict[str, Any] | None
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
