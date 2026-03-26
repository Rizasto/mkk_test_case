import asyncio
from typing import Any

import httpx

from app.core.config import get_settings
from app.db.models.payment import Payment

settings = get_settings()


class WebhookDeliveryError(Exception):
    pass


class WebhookService:
    @staticmethod
    def _get_backoff_delay(attempt: int) -> int:
        return settings.BACKOFF_BASE_SECONDS**attempt

    async def send_payment_result(self, payment: Payment) -> None:
        payload: dict[str, Any] = {
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "description": payment.description,
            "metadata": payment.metadata_json,
            "processed_at": (
                payment.processed_at.isoformat() if payment.processed_at is not None else None
            ),
        }

        last_error_message = ""

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=float(settings.WEBHOOK_TIMEOUT),
                ) as client:
                    response = await client.post(payment.webhook_url, json=payload)
                    response.raise_for_status()
                    return
            except Exception as exc:
                print(exc)
                last_error_message = str(exc)

                if attempt == settings.MAX_RETRIES:
                    break

                await asyncio.sleep(self._get_backoff_delay(attempt))

        raise WebhookDeliveryError(last_error_message)
