"""Tests for database models and operations."""

import pytest
from datetime import datetime
from scrap_immo.database import Database
from scrap_immo.models import Agency, Property, PropertyImage, ScraperLog


@pytest.fixture
def db():
    """Create a test database."""
    test_db = Database("sqlite:///:memory:")
    test_db.create_tables()
    return test_db


def test_create_agency(db):
    """Test creating an agency."""
    with db.get_session() as session:
        agency = Agency(
            name="Test Agency",
            website_url="https://test-agency.com",
        )
        session.add(agency)
        session.commit()
        
        # Verify agency was created
        assert agency.id is not None
        assert agency.name == "Test Agency"
        assert agency.website_url == "https://test-agency.com"
        assert agency.is_active is True


def test_create_property(db):
    """Test creating a property."""
    with db.get_session() as session:
        # Create agency first
        agency = Agency(name="Test Agency", website_url="https://test.com")
        session.add(agency)
        session.commit()
        
        # Create property
        property_obj = Property(
            agency_id=agency.id,
            title="Beautiful Apartment",
            description="A nice place to live",
            property_type="apartment",
            transaction_type="sale",
            price=250000.0,
            currency="EUR",
            city="Brussels",
            num_bedrooms=2,
        )
        session.add(property_obj)
        session.commit()
        
        # Verify property was created
        assert property_obj.id is not None
        assert property_obj.title == "Beautiful Apartment"
        assert property_obj.price == 250000.0
        assert property_obj.agency_id == agency.id


def test_property_with_images(db):
    """Test creating a property with images."""
    with db.get_session() as session:
        # Create agency
        agency = Agency(name="Test Agency", website_url="https://test.com")
        session.add(agency)
        session.commit()
        
        # Create property with images
        property_obj = Property(
            agency_id=agency.id,
            title="House with Images",
            price=300000.0,
        )
        
        # Add images
        image1 = PropertyImage(
            image_url="https://test.com/image1.jpg",
            order=0,
            is_primary=True,
        )
        image2 = PropertyImage(
            image_url="https://test.com/image2.jpg",
            order=1,
            is_primary=False,
        )
        
        property_obj.images.append(image1)
        property_obj.images.append(image2)
        
        session.add(property_obj)
        session.commit()
        
        # Verify property and images
        assert len(property_obj.images) == 2
        assert property_obj.images[0].is_primary is True
        assert property_obj.images[1].is_primary is False


def test_agency_relationship(db):
    """Test agency-property relationship."""
    with db.get_session() as session:
        # Create agency
        agency = Agency(name="Test Agency", website_url="https://test.com")
        session.add(agency)
        session.commit()
        
        # Create multiple properties
        for i in range(3):
            prop = Property(
                agency_id=agency.id,
                title=f"Property {i}",
                price=100000.0 + i * 50000,
            )
            session.add(prop)
        session.commit()
        
        # Verify relationship
        session.refresh(agency)
        assert len(agency.properties) == 3


def test_scraper_log(db):
    """Test creating scraper logs."""
    with db.get_session() as session:
        # Create agency
        agency = Agency(name="Test Agency", website_url="https://test.com")
        session.add(agency)
        session.commit()
        
        # Create log
        log = ScraperLog(
            agency_id=agency.id,
            status="success",
            properties_found=10,
            properties_new=5,
            properties_updated=3,
        )
        session.add(log)
        session.commit()
        
        # Verify log
        assert log.id is not None
        assert log.status == "success"
        assert log.properties_found == 10
