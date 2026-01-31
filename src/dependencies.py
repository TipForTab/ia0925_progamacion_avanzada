from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.core import get_async_db
from src.services import PropertyService, ImageService, AuthService


async def get_property_service(db: AsyncSession = Depends(get_async_db)) -> PropertyService:
    """Dependency to get PropertyService instance"""
    return PropertyService(db)

async def get_image_service(db: AsyncSession = Depends(get_async_db)) -> ImageService:
    """Dependency to get ImageService instance"""
    return ImageService(db)

async def get_auth_service(db: AsyncSession = Depends(get_async_db)) -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService(db)
