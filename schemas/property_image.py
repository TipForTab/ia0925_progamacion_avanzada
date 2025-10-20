from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


# Image schemas
class ImageBase(BaseModel):
    img_url: str = Field(..., min_length=1, max_length=1000, description="Image URL")
    calculated_tags: Optional[Dict[str, Any]] = Field(None, description="AI-calculated image tags as JSON")

class ImageCreate(ImageBase):
    property_id: int = Field(..., gt=0, description="Property ID this image belongs to")

class ImageUpdate(BaseModel):
    img_url: Optional[str] = Field(None, min_length=1, max_length=1000)
    calculated_tags: Optional[Dict[str, Any]] = None

class ImageResponse(ImageBase):
    id: int
    property_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
