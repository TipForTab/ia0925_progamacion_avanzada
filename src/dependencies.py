from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status

from src.core import get_async_db, verify_token
from src.services import PropertyService, ImageService, AuthService, UserService
from src.models.user import User


async def get_property_service(
    db: AsyncSession = Depends(get_async_db),
) -> PropertyService:
    """Dependency to get PropertyService instance"""
    return PropertyService(db)


async def get_image_service(db: AsyncSession = Depends(get_async_db)) -> ImageService:
    """Dependency to get ImageService instance"""
    return ImageService(db)


async def get_auth_service(db: AsyncSession = Depends(get_async_db)) -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService(db)


async def get_user_service(db: AsyncSession = Depends(get_async_db)) -> UserService:
    """Dependency to get UserService instance"""
    return UserService(db)


# Authentication dependency
async def get_current_user(
    username: str = Depends(verify_token), db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    Use this dependency to protect routes that require authentication.

    Usage:
        @router.post("/properties")
        async def create_property(
            property_data: PropertyCreate,
            current_user: User = Depends(get_current_user),  # 🔒 Protected
            db: AsyncSession = Depends(get_async_db)
        ):
            # Only authenticated users can access this route
            ...
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
