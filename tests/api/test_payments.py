from http import HTTPStatus

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models.outbox import Outbox
from app.db.models.payment import Payment

SETTINGS = get_settings()


API_HEADERS = {
    "X-API-Key": SETTINGS.API_KEY,
    "Idempotency-Key": "test-idempotency-key-1",
}


def build_payload(webhook_url: str = "https://webhook.site/test") -> dict:
    return {
        "amount": "100.00",
        "currency": "rub",
        "description": "Test payment",
        "metadata": {"order_id": "123"},
        "webhook_url": webhook_url,
    }


async def test_create_payment_returns_403_for_invalid_api_key(client):
    headers = {
        "X-API-Key": "wrong-api-key",
        "Idempotency-Key": "invalid-api-key-test",
    }

    response = await client.post(
        "/api/v1/payments",
        json=build_payload(),
        headers=headers,
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Invalid API key"


async def test_get_payment_returns_403_for_invalid_api_key(client):
    response = await client.get(
        "/api/v1/payments/11111111-1111-1111-1111-111111111111",
        headers={"X-API-Key": "wrong-api-key"},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json()["detail"] == "Invalid API key"


async def test_create_payment_returns_422_without_idempotency_key(client):
    headers = {
        "X-API-Key": "super-secret-api-key",
    }

    response = await client.post(
        "/api/v1/payments",
        json=build_payload(),
        headers=headers,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_payment_returns_400_for_empty_idempotency_key(client):
    headers = {
        "X-API-Key": "super-secret-api-key",
        "Idempotency-Key": "   ",
    }

    response = await client.post(
        "/api/v1/payments",
        json=build_payload(),
        headers=headers,
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()["detail"] == "Idempotency-Key header must not be empty"


async def test_create_payment_returns_422_for_non_positive_amount(client):
    payload = build_payload()
    payload["amount"] = "0.00"

    await client.post(
        "/api/v1/payments",
        json=payload,
        headers={
            "X-API-Key": "super-secret-api-key",
            "Idempotency-Key": "non-positive-amount-test",
        },
    )


async def test_create_payment_success(client, db_session):
    response = await client.post(
        "/api/v1/payments",
        json=build_payload(),
        headers=API_HEADERS,
    )

    assert response.status_code == HTTPStatus.ACCEPTED

    data = response.json()
    assert data["status"] == "pending"

    payment_result = await db_session.execute(select(Payment))
    payments = list(payment_result.scalars().all())
    assert len(payments) == 1

    outbox_result = await db_session.execute(select(Outbox))
    outbox_events = list(outbox_result.scalars().all())
    assert len(outbox_events) == 1
    assert outbox_events[0].event_type == "payment.created"
    assert outbox_events[0].status == "new"


async def test_create_payment_is_idempotent(client, db_session):
    payload = build_payload()

    first_response = await client.post(
        "/api/v1/payments",
        json=payload,
        headers=API_HEADERS,
    )
    second_response = await client.post(
        "/api/v1/payments",
        json=payload,
        headers=API_HEADERS,
    )

    assert first_response.status_code == HTTPStatus.ACCEPTED
    assert second_response.status_code == HTTPStatus.ACCEPTED

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["id"] == second_data["id"]

    payment_result = await db_session.execute(select(Payment))
    payments = list(payment_result.scalars().all())
    assert len(payments) == 1

    outbox_result = await db_session.execute(select(Outbox))
    outbox_events = list(outbox_result.scalars().all())
    assert len(outbox_events) == 1


async def test_get_payment_by_id(client):
    create_response = await client.post(
        "/api/v1/payments",
        json=build_payload(),
        headers=API_HEADERS,
    )
    payment_id = create_response.json()["id"]

    get_response = await client.get(
        f"/api/v1/payments/{payment_id}",
        headers={"X-API-Key": "super-secret-api-key"},
    )

    assert get_response.status_code == HTTPStatus.OK

    data = get_response.json()
    assert data["id"] == payment_id
    assert data["status"] == "pending"
    assert data["currency"] == "RUB"


async def test_get_payment_returns_404_for_unknown_id(client):
    response = await client.get(
        "/api/v1/payments/11111111-1111-1111-1111-111111111111",
        headers={"X-API-Key": "super-secret-api-key"},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == "Payment not found"
