"""API Key Authentication"""

from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Include 'X-API-Key' header in your request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key not in settings.valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


RequireAPIKey = Annotated[str, Security(validate_api_key)]
