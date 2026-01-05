"""Scraper execution and management."""

import importlib.util
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from scrap_immo.models import Agency, Property, PropertyImage, ScraperLog
from scrap_immo.database import get_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperExecutor:
    """Execute scraper scripts and manage results."""
    
    def __init__(self):
        """Initialize the scraper executor."""
        self.db = get_database()
    
    def load_scraper_module(self, script_path: str):
        """Dynamically load a scraper module.
        
        Args:
            script_path: Path to the scraper script
            
        Returns:
            Module: Loaded Python module
        """
        spec = importlib.util.spec_from_file_location("scraper_module", script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load scraper from {script_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules["scraper_module"] = module
        spec.loader.exec_module(module)
        return module
    
    def execute_scraper(self, agency_id: int) -> Dict[str, Any]:
        """Execute a scraper for a specific agency.
        
        Args:
            agency_id: ID of the agency to scrape
            
        Returns:
            dict: Execution results with statistics
        """
        with self.db.get_session() as session:
            # Get agency
            agency = session.query(Agency).filter(Agency.id == agency_id).first()
            if not agency:
                raise ValueError(f"Agency with ID {agency_id} not found")
            
            if not agency.scraper_script_path:
                raise ValueError(f"Agency '{agency.name}' does not have a scraper script")
            
            # Create scraper log
            log = ScraperLog(
                agency_id=agency_id,
                status="running",
                started_at=datetime.utcnow(),
            )
            session.add(log)
            session.commit()
            
            try:
                # Load and execute scraper
                logger.info(f"Loading scraper for {agency.name} from {agency.scraper_script_path}")
                scraper_module = self.load_scraper_module(agency.scraper_script_path)
                
                logger.info(f"Executing scraper for {agency.name}")
                scraped_properties = scraper_module.scrape_properties()
                
                # Process results
                stats = self._process_scraped_properties(
                    session, agency, scraped_properties
                )
                
                # Update log
                log.status = "success"
                log.finished_at = datetime.utcnow()
                log.properties_found = stats["found"]
                log.properties_new = stats["new"]
                log.properties_updated = stats["updated"]
                
                # Update agency last scraped time
                agency.last_scraped_at = datetime.utcnow()
                
                session.commit()
                
                logger.info(
                    f"Scraping completed for {agency.name}: "
                    f"{stats['found']} found, {stats['new']} new, {stats['updated']} updated"
                )
                
                return stats
                
            except Exception as e:
                logger.error(f"Error executing scraper for {agency.name}: {e}", exc_info=True)
                log.status = "failed"
                log.finished_at = datetime.utcnow()
                log.error_message = str(e)
                session.commit()
                raise
    
    def _process_scraped_properties(
        self, session, agency: Agency, scraped_properties: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Process scraped properties and update database.
        
        Args:
            session: Database session
            agency: Agency object
            scraped_properties: List of scraped property dictionaries
            
        Returns:
            dict: Statistics with 'found', 'new', 'updated' counts
        """
        stats = {"found": len(scraped_properties), "new": 0, "updated": 0}
        
        for prop_data in scraped_properties:
            # Check if property already exists
            existing = None
            if prop_data.get("external_id"):
                existing = (
                    session.query(Property)
                    .filter(
                        Property.agency_id == agency.id,
                        Property.external_id == prop_data["external_id"],
                    )
                    .first()
                )
            elif prop_data.get("property_url"):
                existing = (
                    session.query(Property)
                    .filter(
                        Property.agency_id == agency.id,
                        Property.property_url == prop_data["property_url"],
                    )
                    .first()
                )
            
            if existing:
                # Update existing property
                self._update_property(existing, prop_data)
                existing.last_seen_at = datetime.utcnow()
                stats["updated"] += 1
            else:
                # Create new property
                new_property = self._create_property(agency.id, prop_data)
                session.add(new_property)
                stats["new"] += 1
        
        return stats
    
    def _create_property(self, agency_id: int, prop_data: Dict[str, Any]) -> Property:
        """Create a new Property object from scraped data.
        
        Args:
            agency_id: ID of the agency
            prop_data: Scraped property data
            
        Returns:
            Property: New property object
        """
        # Handle features
        features = prop_data.get("features")
        if isinstance(features, list):
            features = json.dumps(features)
        
        property_obj = Property(
            agency_id=agency_id,
            external_id=prop_data.get("external_id"),
            title=prop_data.get("title", ""),
            description=prop_data.get("description"),
            property_type=prop_data.get("property_type"),
            transaction_type=prop_data.get("transaction_type"),
            address=prop_data.get("address"),
            city=prop_data.get("city"),
            postal_code=prop_data.get("postal_code"),
            country=prop_data.get("country"),
            latitude=prop_data.get("latitude"),
            longitude=prop_data.get("longitude"),
            price=prop_data.get("price"),
            currency=prop_data.get("currency", "EUR"),
            surface_area=prop_data.get("surface_area"),
            num_bedrooms=prop_data.get("num_bedrooms"),
            num_bathrooms=prop_data.get("num_bathrooms"),
            num_rooms=prop_data.get("num_rooms"),
            floor=prop_data.get("floor"),
            year_built=prop_data.get("year_built"),
            features=features,
            property_url=prop_data.get("property_url"),
        )
        
        # Add images
        if prop_data.get("images"):
            for idx, image_url in enumerate(prop_data["images"]):
                image = PropertyImage(
                    image_url=image_url,
                    order=idx,
                    is_primary=(idx == 0),
                )
                property_obj.images.append(image)
        
        return property_obj
    
    def _update_property(self, property_obj: Property, prop_data: Dict[str, Any]):
        """Update an existing property with new data.
        
        Args:
            property_obj: Existing property object
            prop_data: New scraped data
        """
        # Update basic fields
        if prop_data.get("title"):
            property_obj.title = prop_data["title"]
        if prop_data.get("description"):
            property_obj.description = prop_data["description"]
        if prop_data.get("price"):
            property_obj.price = prop_data["price"]
        if prop_data.get("surface_area"):
            property_obj.surface_area = prop_data["surface_area"]
        
        # Update other fields as needed
        for field in [
            "property_type",
            "transaction_type",
            "address",
            "city",
            "postal_code",
            "country",
            "num_bedrooms",
            "num_bathrooms",
            "num_rooms",
            "floor",
            "year_built",
        ]:
            if prop_data.get(field):
                setattr(property_obj, field, prop_data[field])
        
        # Update features
        if prop_data.get("features"):
            features = prop_data["features"]
            if isinstance(features, list):
                features = json.dumps(features)
            property_obj.features = features
    
    def execute_all_scrapers(self) -> Dict[str, Any]:
        """Execute scrapers for all active agencies.
        
        Returns:
            dict: Overall statistics
        """
        with self.db.get_session() as session:
            agencies = session.query(Agency).filter(
                Agency.is_active == True,
                Agency.scraper_script_path.isnot(None)
            ).all()
            
            overall_stats = {
                "total_agencies": len(agencies),
                "successful": 0,
                "failed": 0,
                "total_properties_found": 0,
                "total_new": 0,
                "total_updated": 0,
            }
            
            for agency in agencies:
                try:
                    stats = self.execute_scraper(agency.id)
                    overall_stats["successful"] += 1
                    overall_stats["total_properties_found"] += stats["found"]
                    overall_stats["total_new"] += stats["new"]
                    overall_stats["total_updated"] += stats["updated"]
                except Exception as e:
                    logger.error(f"Failed to scrape {agency.name}: {e}")
                    overall_stats["failed"] += 1
            
            return overall_stats
