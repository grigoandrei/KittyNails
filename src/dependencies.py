import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

OWNER_TOKEN = os.environ.get("OWNER_TOKEN")


def require_owner(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    if not OWNER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured",
        )
    if credentials.credentials != OWNER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication token",
        )
    return credentials.credentials
