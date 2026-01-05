"""Tests for scraper executor."""

import pytest
import tempfile
from pathlib import Path
from scrap_immo.database import Database
from scrap_immo.models import Agency
from scrap_immo.scrapers import ScraperExecutor


@pytest.fixture
def db():
    """Create a test database."""
    test_db = Database("sqlite:///:memory:")
    test_db.create_tables()
    return test_db


@pytest.fixture
def executor(db, monkeypatch):
    """Create a scraper executor with test database."""
    # Patch the get_database function to return our test database
    import scrap_immo.scrapers
    monkeypatch.setattr(scrap_immo.scrapers, "get_database", lambda: db)
    return ScraperExecutor()


def test_create_property_from_data(executor):
    """Test creating a property from scraped data."""
    prop_data = {
        "title": "Test Property",
        "description": "A test property",
        "property_type": "apartment",
        "transaction_type": "sale",
        "price": 200000.0,
        "currency": "EUR",
        "city": "Brussels",
        "num_bedrooms": 2,
        "images": [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
        ],
        "property_url": "https://example.com/property/123",
        "external_id": "123",
    }
    
    property_obj = executor._create_property(1, prop_data)
    
    assert property_obj.title == "Test Property"
    assert property_obj.price == 200000.0
    assert len(property_obj.images) == 2
    assert property_obj.images[0].is_primary is True


def test_load_scraper_module(executor):
    """Test loading a scraper module."""
    # Create a temporary scraper script
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def scrape_properties():
    return [
        {
            "title": "Test Property",
            "price": 100000.0,
        }
    ]
""")
        script_path = f.name
    
    try:
        # Load the module
        module = executor.load_scraper_module(script_path)
        
        # Test the function
        result = module.scrape_properties()
        assert len(result) == 1
        assert result[0]["title"] == "Test Property"
    finally:
        Path(script_path).unlink()


def test_process_scraped_properties(db, executor):
    """Test processing scraped properties."""
    with db.get_session() as session:
        # Create agency
        agency = Agency(name="Test Agency", website_url="https://test.com")
        session.add(agency)
        session.commit()
        
        # Prepare scraped data
        scraped_properties = [
            {
                "title": "Property 1",
                "price": 100000.0,
                "external_id": "prop1",
                "property_url": "https://test.com/prop1",
            },
            {
                "title": "Property 2",
                "price": 200000.0,
                "external_id": "prop2",
                "property_url": "https://test.com/prop2",
            },
        ]
        
        # Process properties
        stats = executor._process_scraped_properties(session, agency, scraped_properties)
        session.commit()
        
        assert stats["found"] == 2
        assert stats["new"] == 2
        assert stats["updated"] == 0
    
    # Process again in a new session (should update existing)
    with db.get_session() as session:
        agency = session.query(Agency).filter(Agency.name == "Test Agency").first()
        stats = executor._process_scraped_properties(session, agency, scraped_properties)
        
        assert stats["found"] == 2
        assert stats["new"] == 0
        assert stats["updated"] == 2
