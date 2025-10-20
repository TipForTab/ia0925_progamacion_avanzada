from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from schemas.property_image import ImageResponse


class PropertyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Property title")
    address: str = Field(..., min_length=1, max_length=500, description="Property address")
    price: float = Field(..., gt=0, description="Property price")
    bathrooms: int = Field(..., ge=0, description="Number of bathrooms")
    rooms: int = Field(..., ge=0, description="Number of rooms")
    square_meters: float = Field(..., gt=0, description="Property size in square meters")
    is_apartment: bool = Field(default=False, description="Is this property an apartment")
    is_house: bool = Field(default=False, description="Is this property a house")
    building_floor: Optional[int] = Field(None, description="Building floor (optional)")
    source_url: str = Field(..., description="URL of the property source")
    is_available: bool = Field(default=True, description="Property availability status")
    amenities: Optional[Dict[str, Any]] = Field(None, description="Property amenities as JSON")
    
    @field_validator('building_floor')
    def validate_building_floor(cls, v):
        if v is not None and v < 0:
            raise ValueError('Building floor must be non-negative')
        return v
    
    @field_validator('is_apartment', 'is_house')
    def validate_property_type(cls, v, values):
        # Ensure at least one property type is selected
        if 'is_apartment' in values and 'is_house' in values:
            if not values['is_apartment'] and not v:
                raise ValueError('Property must be either an apartment or a house')
        return v

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    rooms: Optional[int] = Field(None, ge=0)
    square_meters: Optional[float] = Field(None, gt=0)
    is_apartment: Optional[bool] = None
    is_house: Optional[bool] = None
    building_floor: Optional[int] = None
    source_url: Optional[str] = None
    is_available: Optional[bool] = None
    amenities: Optional[Dict[str, Any]] = None


class PropertyResponse(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    images: List[ImageResponse] = Field(default=[], description="Property images")
    
    class Config:
        from_attributes = True