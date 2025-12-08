from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.core.database import Base


class Image(Base):
    __tablename__ = "property_image"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("property.id"), nullable=False, index=True)
    img_url = Column(String(1000), nullable=False)
    calculated_tags = Column(JSON, nullable=True)
    created_at = Column(String, nullable=True, default=func.now())
    updated_at = Column(String, nullable=True, default=func.now(), onupdate=func.now())
    property = relationship("Property", back_populates="images")

    def __repr__(self):
        return f"<Image(id={self.id}, property_id={self.property_id}, img_url='{self.img_url}')>"