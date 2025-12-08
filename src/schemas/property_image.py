from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List


class ImageBase(BaseModel):
    """Base image schema with common fields"""

    property_id: int = Field(..., gt=0, description="ID of the associated property")
    img_url: str = Field(..., min_length=1, max_length=1000, description="Image URL")
    calculated_tags: Optional[Dict[str, Any]] = Field(None, description="AI-generated tags for the image")

    @field_validator('img_url')  # type: ignore[misc]
    @classmethod
    def validate_url_format(cls, v):
        """Validate that img_url looks like a URL"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Image URL must start with http:// or https://")
        return v


class ImageCreate(ImageBase):
    """Schema for creating a new image"""
    pass


class ImageUpdate(BaseModel):
    """Schema for updating an image - all fields optional"""

    property_id: Optional[int] = Field(None, gt=0, description="ID of the associated property")
    img_url: Optional[str] = Field(None, min_length=1, max_length=1000, description="Image URL")
    calculated_tags: Optional[Dict[str, Any]] = Field(None, description="AI-generated tags for the image")

    @field_validator('img_url')  # type: ignore[misc]
    @classmethod
    def validate_url_format(cls, v):
        """Validate that img_url looks like a URL"""
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError("Image URL must start with http:// or https://")
        return v


class ImageResponse(ImageBase):
    """Schema for image responses - includes metadata"""

    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ImageBulkCreate(BaseModel):
    """Schema for bulk creating images for a property"""

    property_id: int = Field(..., gt=0, description="ID of the associated property")
    image_urls: List[str] = Field(..., min_length=1, max_length=50, description="List of image URLs")

    @field_validator('image_urls')  # type: ignore[misc]
    @classmethod
    def validate_urls(cls, v):
        """Validate all URLs"""
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL format: {url}")
        return v


class ImageTagsUpdate(BaseModel):
    """Schema for updating only the calculated_tags field"""

    calculated_tags: Dict[str, Any] = Field(..., description="AI-generated tags for the image")

    @field_validator('calculated_tags')  # type: ignore[misc]
    @classmethod
    def validate_tags_not_empty(cls, v):
        """Ensure tags are not empty"""
        if not v:
            raise ValueError("Tags cannot be empty")
        return v