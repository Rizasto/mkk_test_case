from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_HOST: str
    APP_PORT: int

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_URL: str

    TEST_DB_HOST: str
    TEST_DB_NAME: str
    TEST_DB_USER: str
    TEST_DB_PASSWORD: str
    TEST_DB_PORT: str
    TEST_DATABASE_URL: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    API_KEY: str
    WEBHOOK_TIMEOUT: int
    MAX_RETRIES: int
    BACKOFF_BASE_SECONDS: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return ("postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}").format(
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            db_name=self.DB_NAME,
        )

    @property
    def sync_database_url(self) -> str:
        return ("postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}").format(
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            db_name=self.DB_NAME,
        )

    @property
    def rabbitmq_url(self) -> str:
        return "amqp://{user}:{password}@{host}:{port}/".format(
            user=self.RABBITMQ_USER,
            password=self.RABBITMQ_PASSWORD,
            host=self.RABBITMQ_HOST,
            port=self.RABBITMQ_PORT,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
