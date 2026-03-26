from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.include_router(api_router)


@app.get("/health")
async def healthcheck():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
    }


@app.get("/")
async def root():
    return {"message": "Payment service is running"}
