from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)


@app.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
    }


@app.get("/")
async def root():
    return {"message": "Payment service is running"}