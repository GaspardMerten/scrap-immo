"""Tests for AI agent scraper generator."""

import pytest
import os
from scrap_immo.ai_agent import ScraperGenerator


@pytest.fixture(autouse=True)
def mock_api_key(monkeypatch):
    """Mock API key for testing."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")


def test_build_prompt():
    """Test building the AI prompt."""
    generator = ScraperGenerator(provider="gemini")
    
    prompt = generator._build_prompt(
        "Test Agency",
        "https://test-agency.com",
        "https://test-agency.com/property/123"
    )
    
    assert "Test Agency" in prompt
    assert "https://test-agency.com" in prompt
    assert "https://test-agency.com/property/123" in prompt
    assert "scrape_properties()" in prompt


def test_validate_scraper_valid(tmp_path):
    """Test validating a valid scraper."""
    generator = ScraperGenerator(provider="gemini")
    
    # Create a valid scraper
    script_path = tmp_path / "test_scraper.py"
    script_path.write_text("""
import requests
from typing import List, Dict, Any

def scrape_properties() -> List[Dict[str, Any]]:
    return []
""")
    
    assert generator.validate_scraper(str(script_path)) is True


def test_validate_scraper_invalid_syntax(tmp_path):
    """Test validating a scraper with invalid syntax."""
    generator = ScraperGenerator(provider="gemini")
    
    # Create an invalid scraper
    script_path = tmp_path / "test_scraper.py"
    script_path.write_text("""
def scrape_properties(
    # Missing closing parenthesis
    return []
""")
    
    assert generator.validate_scraper(str(script_path)) is False


def test_validate_scraper_missing_function(tmp_path):
    """Test validating a scraper without required function."""
    generator = ScraperGenerator(provider="gemini")
    
    # Create a scraper without the required function
    script_path = tmp_path / "test_scraper.py"
    script_path.write_text("""
import requests

def some_other_function():
    return []
""")
    
    assert generator.validate_scraper(str(script_path)) is False


def test_save_scraper(tmp_path):
    """Test saving a scraper script."""
    generator = ScraperGenerator(provider="gemini")
    
    script_content = """
import requests

def scrape_properties():
    return []
"""
    
    script_path = generator.save_scraper(
        script_content,
        "Test Agency",
        str(tmp_path)
    )
    
    assert script_path.endswith("test_agency_scraper.py")
    with open(script_path, "r") as f:
        assert "def scrape_properties():" in f.read()
