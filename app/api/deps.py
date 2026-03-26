from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import validate_api_key
from app.db.session import get_session

DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
ApiKeyDep = Annotated[str, Depends(validate_api_key)]


async def get_idempotency_key(
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> str:
    value = idempotency_key.strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header must not be empty",
        )
    return value


IdempotencyKeyDep = Annotated[str, Depends(get_idempotency_key)]
