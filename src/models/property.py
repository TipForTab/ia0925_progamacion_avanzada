from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base


class Property(Base):
    __tablename__ = "property"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    price = Column(Float, nullable=False, index=True)
    operation_type = Column(String(20), nullable=True, index=True)  # 'rent' or 'sale'
    bathrooms = Column(Integer, nullable=False)
    rooms = Column(Integer, nullable=False)
    square_meters = Column(Float, nullable=False)
    is_apartment = Column(Boolean, nullable=False, default=False)
    is_house = Column(Boolean, nullable=False, default=False)
    building_floor = Column(Integer, nullable=True)
    source_url = Column(Text, nullable=False, unique=True)
    is_available = Column(Boolean, nullable=False, default=True)
    amenities = Column(JSON, nullable=True)
    created_at = Column(String, nullable=True, default=func.now())
    updated_at = Column(String, nullable=True, default=func.now(), onupdate=func.now())
    images = relationship(
        "Image", back_populates="property", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Property(id={self.id}, title='{self.title}', price={self.price}, operation='{self.operation_type}')>"
