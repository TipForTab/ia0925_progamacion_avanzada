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

#A MODIFICAR CUANDO SEA REAL
async def get_current_user(auth_service: AuthService = Depends(get_auth_service)):
    """Dependency to get current authenticated user"""
    # Aquí deberías implementar la lógica para extraer el token de la cabecera,
    # verificarlo y devolver el usuario asociado. Esto es solo un ejemplo.
    token = "fake-token-for-demo"  # En un caso real, extraerías esto de la cabecera Authorization
    user = await auth_service.authenticate_user(token)
    return user
