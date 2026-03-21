import re

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from src.schemas.property_image import ImageResponse


class PropertyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Property title")
    address: str = Field(
        ..., min_length=1, max_length=500, description="Property address"
    )
    price: float = Field(..., ge=100, description="Property price (minimum $100)")
    operation_type: Optional[Literal["rent", "sale"]] = Field(
        None, description="Operation type: rent or sale"
    )
    bathrooms: int = Field(..., ge=0, description="Number of bathrooms")
    rooms: int = Field(..., ge=0, description="Number of rooms")
    square_meters: float = Field(
        ..., gt=0, le=10000, description="Property size in square meters (max 10,000)"
    )
    is_apartment: bool = Field(
        default=False, description="Is this property an apartment"
    )
    is_house: bool = Field(default=False, description="Is this property a house")
    building_floor: Optional[int] = Field(None, description="Building floor (optional)")
    source_url: str = Field(..., description="URL of the property source")
    is_available: bool = Field(default=True, description="Property availability status")
    amenities: Optional[Dict[str, Any]] = Field(
        None, description="Property amenities as JSON"
    )

    @field_validator("building_floor")
    @classmethod
    def validate_building_floor(cls, v):
        if v is not None and v < 0:
            raise ValueError("Building floor must be non-negative")
        return v

    @field_validator("price")
    @classmethod
    def validate_price_reasonable(cls, v):
        """Ensure price is reasonable"""
        if v > 100_000_000:  # 100 million - sanity check
            raise ValueError("Price seems unreasonably high. Please verify.")
        return v

    @field_validator("square_meters")
    @classmethod
    def validate_square_meters_reasonable(cls, v):
        """Validate square meters is reasonable"""
        if v < 5:
            raise ValueError(
                "Square meters seems too small (minimum 5 sqm). Please verify."
            )
        return v

    @field_validator("rooms", "bathrooms")
    @classmethod
    def validate_room_counts_reasonable(cls, v):
        """Validate room/bathroom counts are reasonable"""
        if v > 50:
            raise ValueError("Number seems unreasonably high (max 50). Please verify.")
        return v

    @model_validator(mode="after")
    def validate_property_type(self):
        """Ensure at least one property type is selected"""
        if not self.is_apartment and not self.is_house:
            raise ValueError("Property must be either an apartment or a house")
        return self


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, ge=100)
    operation_type: Optional[Literal["rent", "sale"]] = Field(
        None, description="Operation type: rent or sale"
    )
    bathrooms: Optional[int] = Field(None, ge=0)
    rooms: Optional[int] = Field(None, ge=0)
    square_meters: Optional[float] = Field(None, gt=0, le=10000)
    is_apartment: Optional[bool] = None
    is_house: Optional[bool] = None
    building_floor: Optional[int] = None
    source_url: Optional[str] = None
    is_available: Optional[bool] = None
    amenities: Optional[Dict[str, Any]] = None

    @field_validator("building_floor")
    @classmethod
    def validate_building_floor(cls, v):
        if v is not None and v < 0:
            raise ValueError("Building floor must be non-negative")
        return v

    @field_validator("price")
    @classmethod
    def validate_price_reasonable(cls, v):
        if v is not None and v > 100_000_000:
            raise ValueError("Price seems unreasonably high. Please verify.")
        return v

    @field_validator("square_meters")
    @classmethod
    def validate_square_meters_reasonable(cls, v):
        if v is not None and v < 5:
            raise ValueError(
                "Square meters seems too small (minimum 5 sqm). Please verify."
            )
        return v

    @field_validator("rooms", "bathrooms")
    @classmethod
    def validate_room_counts_reasonable(cls, v):
        if v is not None and v > 50:
            raise ValueError("Number seems unreasonably high (max 50). Please verify.")
        return v


class PropertyResponse(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    images: Optional[List[ImageResponse]] = Field(
        default_factory=list, description="Property images"
    )

    class Config:
        from_attributes = True

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _parse_dt(cls, v):
        if isinstance(v, str):
            s = v.strip()
            # insert 'T' between date and time if it's missing
            if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}", s):
                s = s.replace(" ", "T", 1)
            # turn "+00" into "+00:00"
            if s.endswith("+00"):
                s = s + ":00"
            try:
                return datetime.fromisoformat(s)
            except ValueError:
                # optional fallback if you have python-dateutil installed
                from dateutil.parser import isoparse

                return isoparse(s)
        return v


class PropertySearchFilters(BaseModel):
    """Schema for search filters with validation"""

    # Property type filters
    is_apartment: Optional[bool] = None
    is_house: Optional[bool] = None

    # Operation type filter
    operation_type: Optional[Literal["rent", "sale"]] = Field(
        None, description="Filter by operation type"
    )

    # Price filters
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)

    # Room filters
    rooms: Optional[int] = Field(None, ge=0)
    min_rooms: Optional[int] = Field(None, ge=0)
    max_rooms: Optional[int] = Field(None, ge=0)

    # Bathroom filters
    bathrooms: Optional[int] = Field(None, ge=0)
    min_bathrooms: Optional[int] = Field(None, ge=0)
    max_bathrooms: Optional[int] = Field(None, ge=0)

    # Size filters
    min_square_meters: Optional[float] = Field(None, ge=0)
    max_square_meters: Optional[float] = Field(None, ge=0)

    # Floor filters
    floor: Optional[int] = None
    min_floor: Optional[int] = None
    max_floor: Optional[int] = None

    # Location filters
    address: Optional[str] = Field(None, max_length=500)
    title: Optional[str] = Field(None, max_length=255)

    # Availability
    is_available: Optional[bool] = None

    # Amenity filter
    amenity: Optional[str] = None

    # Images filter
    has_images: Optional[bool] = None

    # Date filters
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    date_field: Optional[str] = Field("created_at", pattern="^(created_at|updated_at)$")

    # Ordering
    order_by: Optional[str] = Field(
        "created_at", pattern="^(price|rooms|square_meters|created_at|updated_at)$"
    )
    ascending: bool = False

    # Pagination
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

    @model_validator(mode="after")
    def validate_ranges(self):
        """Validate that min values are not greater than max values"""

        # Price range validation
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot be greater than max_price")

        # Room range validation
        if self.min_rooms is not None and self.max_rooms is not None:
            if self.min_rooms > self.max_rooms:
                raise ValueError("min_rooms cannot be greater than max_rooms")

        # Bathroom range validation
        if self.min_bathrooms is not None and self.max_bathrooms is not None:
            if self.min_bathrooms > self.max_bathrooms:
                raise ValueError("min_bathrooms cannot be greater than max_bathrooms")

        # Square meters range validation
        if self.min_square_meters is not None and self.max_square_meters is not None:
            if self.min_square_meters > self.max_square_meters:
                raise ValueError(
                    "min_square_meters cannot be greater than max_square_meters"
                )

        # Floor range validation
        if self.min_floor is not None and self.max_floor is not None:
            if self.min_floor > self.max_floor:
                raise ValueError("min_floor cannot be greater than max_floor")

        return self


class BulkUpdateAvailability(BaseModel):
    """Schema for bulk availability updates"""

    property_ids: List[int] = Field(..., min_length=1, max_length=1000)
    is_available: bool

    @field_validator("property_ids")
    @classmethod
    def validate_unique_ids(cls, v):
        """Ensure property IDs are unique"""
        if len(v) != len(set(v)):
            raise ValueError("Property IDs must be unique")
        return v


class BulkUpdateOperationType(BaseModel):
    """Schema for bulk operation type updates"""

    property_ids: List[int] = Field(..., min_length=1, max_length=1000)
    operation_type: Literal["rent", "sale"]

    @field_validator("property_ids")
    @classmethod
    def validate_unique_ids(cls, v):
        """Ensure property IDs are unique"""
        if len(v) != len(set(v)):
            raise ValueError("Property IDs must be unique")
        return v
