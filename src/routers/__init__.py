from .property import router as property_router
from .property_image import router as property_image_router
from .auth_router import router as auth_router
from .extract_data_router import router as extract_data_router
from .califier_router import router as califier_router

__all__ = ["property_router", "property_image_router", "auth_router", "extract_data_router", "califier_router"]