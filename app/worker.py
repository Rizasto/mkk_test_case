import asyncio

from app.core.config import get_settings

settings = get_settings()


async def main():
    print("Worker started")
    print("RabbitMQ host: {0}".format(settings.RABBITMQ_HOST))
    print("Database URL: {0}".format(settings.async_database_url))

    while True:
        print("Worker is alive")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())