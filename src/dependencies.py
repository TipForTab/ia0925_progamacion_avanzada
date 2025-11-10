from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.core import get_async_db
from src.services import PropertyService, ImageService


async def get_property_service(db: AsyncSession = Depends(get_async_db)) -> PropertyService:
    """Dependency to get PropertyService instance"""
    return PropertyService(db)

async def get_image_service(db: AsyncSession = Depends(get_async_db)) -> ImageService:
    """Dependency to get PropertyService instance"""
    return ImageService(db)
