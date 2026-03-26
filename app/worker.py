import asyncio

import aio_pika

import app.broker.consumer  # noqa: F401
from app.broker.rabbit import PAYMENTS_DLQ, broker
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.outbox import OutboxService

settings = get_settings()


async def declare_dlq() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    try:
        channel = await connection.channel()
        await channel.declare_queue(
            PAYMENTS_DLQ.name,
            durable=True,
        )
    finally:
        await connection.close()


async def run_outbox_publisher() -> None:
    while True:
        async with AsyncSessionLocal() as session:
            service = OutboxService(session=session)
            published_count = await service.publish_new_events(batch_size=100)

            if published_count > 0:
                print(f"Published {published_count} outbox event(s)")

        await asyncio.sleep(2)


async def main() -> None:
    print("Worker started")
    print(f"RabbitMQ host: {settings.RABBITMQ_HOST}")
    print(f"Database URL: {settings.async_database_url}")

    await declare_dlq()
    await broker.start()
    publisher_task = asyncio.create_task(run_outbox_publisher())

    try:
        await asyncio.Future()
    finally:
        publisher_task.cancel()
        await broker.close()


if __name__ == "__main__":
    asyncio.run(main())
