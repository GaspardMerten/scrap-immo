"""Command-line interface for scrap-immo."""

import click
import os
from pathlib import Path
from datetime import datetime

from scrap_immo.database import init_database, get_database
from scrap_immo.models import Agency, Property, ScraperLog
from scrap_immo.ai_agent import ScraperGenerator
from scrap_immo.scrapers import ScraperExecutor


@click.group()
@click.option("--database-url", envvar="DATABASE_URL", help="Database connection URL")
@click.pass_context
def main(ctx, database_url):
    """Scrap-Immo: AI-powered property scraping system."""
    ctx.ensure_object(dict)
    ctx.obj["database_url"] = database_url
    
    # Initialize database
    init_database(database_url)


@main.command()
def init():
    """Initialize the database."""
    click.echo("Initializing database...")
    db = get_database()
    db.create_tables()
    click.echo("✓ Database initialized successfully!")


@main.group()
def agency():
    """Manage real estate agencies."""
    pass


@agency.command("add")
@click.argument("name")
@click.argument("website-url")
@click.option("--generate-scraper", is_flag=True, help="Generate scraper script immediately")
@click.option("--sample-url", help="Sample listing URL for better scraper generation")
@click.option("--provider", default="gemini", help="AI provider (gemini, openai, or anthropic)")
def agency_add(name, website_url, generate_scraper, sample_url, provider):
    """Add a new agency."""
    db = get_database()
    
    with db.get_session() as session:
        # Check if agency already exists
        existing = session.query(Agency).filter(Agency.name == name).first()
        if existing:
            click.echo(f"✗ Agency '{name}' already exists!", err=True)
            return
        
        # Create agency
        agency_obj = Agency(name=name, website_url=website_url)
        session.add(agency_obj)
        session.commit()
        session.refresh(agency_obj)
        
        click.echo(f"✓ Agency '{name}' added successfully (ID: {agency_obj.id})")
        
        # Generate scraper if requested
        if generate_scraper:
            click.echo(f"\nGenerating scraper script using {provider}...")
            try:
                generator = ScraperGenerator(provider=provider)
                script = generator.generate_scraper(name, website_url, sample_url)
                script_path = generator.save_scraper(script, name)
                
                # Validate script
                if generator.validate_scraper(script_path):
                    # Update agency with script path
                    agency_obj.scraper_script_path = script_path
                    agency_obj.scraper_generated_at = datetime.utcnow()
                    session.commit()
                    
                    click.echo(f"✓ Scraper generated and saved to: {script_path}")
                else:
                    click.echo(f"✗ Generated scraper failed validation", err=True)
                    click.echo(f"Script saved at: {script_path}")
                    
            except Exception as e:
                click.echo(f"✗ Error generating scraper: {e}", err=True)


@agency.command("list")
def agency_list():
    """List all agencies."""
    db = get_database()
    
    with db.get_session() as session:
        agencies = session.query(Agency).all()
        
        if not agencies:
            click.echo("No agencies found.")
            return
        
        click.echo(f"\n{'ID':<5} {'Name':<30} {'Website':<50} {'Scraper':<10} {'Last Scraped':<20}")
        click.echo("-" * 115)
        
        for agency in agencies:
            has_scraper = "✓" if agency.scraper_script_path else "✗"
            last_scraped = (
                agency.last_scraped_at.strftime("%Y-%m-%d %H:%M")
                if agency.last_scraped_at
                else "Never"
            )
            click.echo(
                f"{agency.id:<5} {agency.name[:28]:<30} {agency.website_url[:48]:<50} "
                f"{has_scraper:<10} {last_scraped:<20}"
            )


@agency.command("generate-scraper")
@click.argument("agency-id", type=int)
@click.option("--sample-url", help="Sample listing URL for better scraper generation")
@click.option("--provider", default="gemini", help="AI provider (gemini, openai, or anthropic)")
def agency_generate_scraper(agency_id, sample_url, provider):
    """Generate scraper script for an agency."""
    db = get_database()
    
    with db.get_session() as session:
        agency = session.query(Agency).filter(Agency.id == agency_id).first()
        if not agency:
            click.echo(f"✗ Agency with ID {agency_id} not found!", err=True)
            return
        
        click.echo(f"Generating scraper for '{agency.name}' using {provider}...")
        
        try:
            generator = ScraperGenerator(provider=provider)
            script = generator.generate_scraper(agency.name, agency.website_url, sample_url)
            script_path = generator.save_scraper(script, agency.name)
            
            # Validate script
            if generator.validate_scraper(script_path):
                # Update agency with script path
                agency.scraper_script_path = script_path
                agency.scraper_generated_at = datetime.utcnow()
                session.commit()
                
                click.echo(f"✓ Scraper generated and saved to: {script_path}")
            else:
                click.echo(f"✗ Generated scraper failed validation", err=True)
                click.echo(f"Script saved at: {script_path}")
                
        except Exception as e:
            click.echo(f"✗ Error generating scraper: {e}", err=True)


@agency.command("remove")
@click.argument("agency-id", type=int)
@click.confirmation_option(prompt="Are you sure you want to remove this agency?")
def agency_remove(agency_id):
    """Remove an agency."""
    db = get_database()
    
    with db.get_session() as session:
        agency = session.query(Agency).filter(Agency.id == agency_id).first()
        if not agency:
            click.echo(f"✗ Agency with ID {agency_id} not found!", err=True)
            return
        
        name = agency.name
        session.delete(agency)
        session.commit()
        
        click.echo(f"✓ Agency '{name}' removed successfully")


@main.group()
def scrape():
    """Run scrapers."""
    pass


@scrape.command("agency")
@click.argument("agency-id", type=int)
def scrape_agency(agency_id):
    """Scrape properties for a specific agency."""
    executor = ScraperExecutor()
    
    try:
        click.echo(f"Starting scraper for agency ID {agency_id}...")
        stats = executor.execute_scraper(agency_id)
        
        click.echo("\n✓ Scraping completed successfully!")
        click.echo(f"  Properties found: {stats['found']}")
        click.echo(f"  New properties: {stats['new']}")
        click.echo(f"  Updated properties: {stats['updated']}")
        
    except Exception as e:
        click.echo(f"\n✗ Scraping failed: {e}", err=True)


@scrape.command("all")
def scrape_all():
    """Scrape properties for all active agencies."""
    executor = ScraperExecutor()
    
    click.echo("Starting scrapers for all active agencies...")
    stats = executor.execute_all_scrapers()
    
    click.echo("\n✓ All scrapers completed!")
    click.echo(f"  Total agencies: {stats['total_agencies']}")
    click.echo(f"  Successful: {stats['successful']}")
    click.echo(f"  Failed: {stats['failed']}")
    click.echo(f"  Total properties found: {stats['total_properties_found']}")
    click.echo(f"  New properties: {stats['total_new']}")
    click.echo(f"  Updated properties: {stats['total_updated']}")


@main.group()
def properties():
    """View properties."""
    pass


@properties.command("list")
@click.option("--agency-id", type=int, help="Filter by agency ID")
@click.option("--limit", default=20, help="Number of properties to show")
def properties_list(agency_id, limit):
    """List properties."""
    db = get_database()
    
    with db.get_session() as session:
        query = session.query(Property)
        
        if agency_id:
            query = query.filter(Property.agency_id == agency_id)
        
        properties_list = query.order_by(Property.created_at.desc()).limit(limit).all()
        
        if not properties_list:
            click.echo("No properties found.")
            return
        
        click.echo(f"\n{'ID':<7} {'Title':<40} {'Price':<15} {'Type':<15} {'City':<20}")
        click.echo("-" * 97)
        
        for prop in properties_list:
            title = prop.title[:38] if len(prop.title) > 38 else prop.title
            price = f"{prop.price} {prop.currency}" if prop.price else "N/A"
            prop_type = prop.property_type or "N/A"
            city = prop.city or "N/A"
            
            click.echo(f"{prop.id:<7} {title:<40} {price:<15} {prop_type:<15} {city:<20}")
        
        click.echo(f"\nShowing {len(properties_list)} properties")


@properties.command("count")
def properties_count():
    """Count total properties."""
    db = get_database()
    
    with db.get_session() as session:
        total = session.query(Property).count()
        available = session.query(Property).filter(Property.is_available == True).count()
        
        click.echo(f"\nTotal properties: {total}")
        click.echo(f"Available properties: {available}")


@main.command("logs")
@click.option("--limit", default=10, help="Number of logs to show")
def logs(limit):
    """View scraper execution logs."""
    db = get_database()
    
    with db.get_session() as session:
        logs_list = (
            session.query(ScraperLog)
            .order_by(ScraperLog.started_at.desc())
            .limit(limit)
            .all()
        )
        
        if not logs_list:
            click.echo("No logs found.")
            return
        
        click.echo(f"\n{'ID':<7} {'Agency ID':<12} {'Status':<12} {'Started':<20} {'Found':<8} {'New':<8}")
        click.echo("-" * 67)
        
        for log in logs_list:
            started = log.started_at.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(
                f"{log.id:<7} {log.agency_id:<12} {log.status:<12} {started:<20} "
                f"{log.properties_found:<8} {log.properties_new:<8}"
            )


if __name__ == "__main__":
    main()
