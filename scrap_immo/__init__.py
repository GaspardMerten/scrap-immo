"""Scrap-Immo: AI-powered property scraping system."""

__version__ = "0.1.0"

from scrap_immo.database import init_database, get_database
from scrap_immo.ai_agent import ScraperGenerator
from scrap_immo.scrapers import ScraperExecutor

__all__ = [
    "init_database",
    "get_database",
    "ScraperGenerator",
    "ScraperExecutor",
]
