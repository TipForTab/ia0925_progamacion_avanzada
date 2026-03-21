import re
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., max_length=100, description="User email address")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(
        ..., min_length=8, max_length=100, description="User password"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Optional: Add more password requirements
        # if not re.search(r'[A-Z]', v):
        #     raise ValueError('Password must contain at least one uppercase letter')
        # if not re.search(r'[a-z]', v):
        #     raise ValueError('Password must contain at least one lowercase letter')
        # if not re.search(r'\d', v):
        #     raise ValueError('Password must contain at least one number')

        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=100)
    password: Optional[str] = Field(
        None, min_length=8, max_length=100, description="New password"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password strength"""
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserResponse(UserBase):
    """Schema for user response (excludes password)"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _parse_dt(cls, v):
        """Parse datetime from string if needed"""
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


class UserInDB(UserBase):
    """Schema for user in database (includes hashed_password)"""

    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
