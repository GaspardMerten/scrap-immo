"""
Example scraper script for demonstration purposes.
This shows the structure that AI-generated scrapers should follow.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_properties() -> List[Dict[str, Any]]:
    """
    Scrape property listings from the agency website.
    
    Returns:
        List[Dict[str, Any]]: List of property dictionaries
    """
    properties = []
    
    # Base URL for the agency
    base_url = "https://example-agency.com"
    listings_url = f"{base_url}/properties"
    
    try:
        # Fetch the listings page
        logger.info(f"Fetching listings from {listings_url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(listings_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find all property cards (example selector - adjust based on actual website)
        property_cards = soup.find_all("div", class_="property-card")
        
        logger.info(f"Found {len(property_cards)} property cards")
        
        for card in property_cards:
            try:
                # Extract property details
                property_data = {
                    "title": None,
                    "description": None,
                    "property_type": None,
                    "transaction_type": None,
                    "address": None,
                    "city": None,
                    "postal_code": None,
                    "country": "Belgium",  # Default if not specified
                    "price": None,
                    "currency": "EUR",
                    "surface_area": None,
                    "num_bedrooms": None,
                    "num_bathrooms": None,
                    "num_rooms": None,
                    "floor": None,
                    "year_built": None,
                    "features": [],
                    "images": [],
                    "property_url": None,
                    "external_id": None,
                }
                
                # Title
                title_elem = card.find("h3", class_="property-title")
                if title_elem:
                    property_data["title"] = title_elem.text.strip()
                
                # Price
                price_elem = card.find("span", class_="property-price")
                if price_elem:
                    price_text = price_elem.text.strip()
                    # Extract numeric value (e.g., "€250,000" -> 250000.0)
                    price_numeric = "".join(c for c in price_text if c.isdigit() or c == ".")
                    if price_numeric:
                        property_data["price"] = float(price_numeric)
                
                # Property URL
                link_elem = card.find("a", class_="property-link")
                if link_elem and link_elem.get("href"):
                    property_data["property_url"] = base_url + link_elem["href"]
                    # Extract ID from URL if possible
                    if "/property/" in link_elem["href"]:
                        property_data["external_id"] = link_elem["href"].split("/property/")[-1]
                
                # Location
                location_elem = card.find("span", class_="property-location")
                if location_elem:
                    location_text = location_elem.text.strip()
                    # Try to parse city and postal code
                    parts = location_text.split(",")
                    if len(parts) >= 2:
                        property_data["city"] = parts[0].strip()
                        property_data["postal_code"] = parts[1].strip()
                
                # Bedrooms
                bedrooms_elem = card.find("span", class_="bedrooms")
                if bedrooms_elem:
                    bedrooms_text = bedrooms_elem.text.strip()
                    bedrooms_numeric = "".join(c for c in bedrooms_text if c.isdigit())
                    if bedrooms_numeric:
                        property_data["num_bedrooms"] = int(bedrooms_numeric)
                
                # Surface area
                surface_elem = card.find("span", class_="surface-area")
                if surface_elem:
                    surface_text = surface_elem.text.strip()
                    surface_numeric = "".join(c for c in surface_text if c.isdigit() or c == ".")
                    if surface_numeric:
                        property_data["surface_area"] = float(surface_numeric)
                
                # Images
                img_elems = card.find_all("img", class_="property-image")
                for img in img_elems:
                    if img.get("src"):
                        image_url = img["src"]
                        if not image_url.startswith("http"):
                            image_url = base_url + image_url
                        property_data["images"].append(image_url)
                
                # Only add property if it has at least a title
                if property_data["title"]:
                    properties.append(property_data)
                    logger.debug(f"Scraped: {property_data['title']}")
                
                # Be respectful to the server
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing property card: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(properties)} properties")
        
    except Exception as e:
        logger.error(f"Error fetching listings: {e}")
    
    return properties


if __name__ == "__main__":
    # Test the scraper
    results = scrape_properties()
    print(f"Scraped {len(results)} properties")
    if results:
        print(f"First property: {results[0]}")
