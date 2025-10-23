from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from core import get_async_db
from services import PropertyService


async def get_property_service(db: AsyncSession = Depends(get_async_db)) -> PropertyService:
    """Dependency to get PropertyService instance"""
    return PropertyService(db)
