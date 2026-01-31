from typing import Callable
from functools import wraps
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verify_password
from src.repositories.user import UserRepository
from src.schemas.jwt import LoginRequest
from src.core import log_error, log_debug


def handle_auth_errors(operation_name: str):
    """Decorator to reduce error handling boilerplate"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                log_error(e, f"Failed to {operation_name}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation_name}"
                )

        return wrapper

    return decorator


class AuthService:
    """Service layer for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)

    @handle_auth_errors("authenticate user")
    async def authenticate_user(self, credentials: LoginRequest) -> str:
        """
        Authenticate user and return username if valid

        Args:
            credentials: LoginRequest with username and password

        Returns:
            username if authentication successful

        Raises:
            ValueError: If credentials are invalid
        """
        log_debug("Authenticating user", {"username": credentials.username})

        # Get user from database
        db_user = await self.repository.get_by_username(credentials.username)

        if not db_user or not verify_password(credentials.password, db_user.hashed_password):
            log_debug("Authentication failed", {"username": credentials.username})
            raise ValueError("Invalid credentials")

        log_debug("User authenticated successfully", {"username": credentials.username})
        return credentials.username