from .property import router as property_router
from .property_image import router as property_image_router
from .auth_router import router as auth_router

__all__ = ["property_router", "property_image_router", "auth_router"]
