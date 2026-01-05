"""Database models for the property scraping system."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Agency(Base):
    """Model for real estate agencies."""
    
    __tablename__ = "agencies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    website_url: Mapped[str] = mapped_column(String(500), nullable=False)
    scraper_script_path: Mapped[Optional[str]] = mapped_column(String(500))
    scraper_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    properties: Mapped[List["Property"]] = relationship(
        "Property", back_populates="agency", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Agency(id={self.id}, name='{self.name}', website='{self.website_url}')>"


class Property(Base):
    """Model for properties (for sale or rent)."""
    
    __tablename__ = "properties"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id"), nullable=False)
    
    # Basic information
    external_id: Mapped[Optional[str]] = mapped_column(String(255))  # ID from agency website
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    property_type: Mapped[Optional[str]] = mapped_column(String(100))  # apartment, house, etc.
    transaction_type: Mapped[Optional[str]] = mapped_column(String(50))  # sale, rent
    
    # Location
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(255))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    
    # Pricing
    price: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default="EUR")
    
    # Property details
    surface_area: Mapped[Optional[float]] = mapped_column(Float)  # in square meters
    num_bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    num_bathrooms: Mapped[Optional[int]] = mapped_column(Integer)
    num_rooms: Mapped[Optional[int]] = mapped_column(Integer)
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Amenities/Features (stored as JSON-like text)
    features: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    
    # URLs
    property_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # Status
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    agency: Mapped["Agency"] = relationship("Agency", back_populates="properties")
    images: Mapped[List["PropertyImage"]] = relationship(
        "PropertyImage", back_populates="property", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Property(id={self.id}, title='{self.title}', price={self.price})>"


class PropertyImage(Base):
    """Model for property images."""
    
    __tablename__ = "property_images"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    local_path: Mapped[Optional[str]] = mapped_column(String(500))
    caption: Mapped[Optional[str]] = mapped_column(String(500))
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    property: Mapped["Property"] = relationship("Property", back_populates="images")
    
    def __repr__(self) -> str:
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, url='{self.image_url}')>"


class ScraperLog(Base):
    """Model for logging scraper execution."""
    
    __tablename__ = "scraper_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id"), nullable=False)
    
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50))  # running, success, failed
    properties_found: Mapped[int] = mapped_column(Integer, default=0)
    properties_new: Mapped[int] = mapped_column(Integer, default=0)
    properties_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    def __repr__(self) -> str:
        return f"<ScraperLog(id={self.id}, agency_id={self.agency_id}, status='{self.status}')>"
