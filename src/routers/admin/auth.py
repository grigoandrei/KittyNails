from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from src.auth import verify_password, create_access_token
from src.config import settings
from src.limiter import limiter

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest):
    if data.username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, settings.ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": data.username})
    return LoginResponse(access_token=token)
