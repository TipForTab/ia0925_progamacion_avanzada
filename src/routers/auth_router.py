from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends

from src.core.security import create_access_token
from src.schemas.jwt import LoginRequest, TokenResponse
from src.services.auth_service import AuthService
from src.dependencies import get_auth_service  # Add this dependency
from src.conf import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and return JWT token",
)
async def login(
    credentials: LoginRequest, service: AuthService = Depends(get_auth_service)
):
    """
    Login endpoint that returns JWT token.

    Validates credentials and returns access token.
    """
    try:
        username = await service.authenticate_user(credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
