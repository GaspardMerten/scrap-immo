# Scrap-Immo

An AI-powered property scraping system that automatically generates and manages web scrapers for real estate agencies. This project creates a comprehensive database of properties available for sale or rent by intelligently scraping agency websites.

## Features

- 🤖 **AI-Powered Scraper Generation**: Uses Google Gemini (default), GPT-4, or Claude to automatically generate Python scraper scripts for any real estate agency website
- 📊 **Comprehensive Database**: Stores all property details including images, prices, descriptions, and more
- 🔄 **Reusable Scrapers**: Generate scrapers once and reuse them on subsequent runs
- 🏢 **Multi-Agency Support**: Manage and scrape properties from multiple agencies
- 📈 **Progress Tracking**: Monitor scraping activities with detailed logs
- 🛠️ **CLI Interface**: Easy-to-use command-line interface for all operations

## Installation

### Requirements

- Python 3.9 or higher
- Google Gemini API key (default), OpenAI API key, or Anthropic API key (for AI-powered scraper generation)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/GaspardMerten/scrap-immo.git
cd scrap-immo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install in development mode:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
# Create a .env file
# Using Gemini (default)
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env

# Or using OpenAI
# echo "OPENAI_API_KEY=your_openai_api_key_here" > .env

# Or using Anthropic
# echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" > .env

# Optional: Set custom database URL (defaults to SQLite)
echo "DATABASE_URL=sqlite:///./scrap_immo.db" >> .env
```

4. Initialize the database:
```bash
scrap-immo init
```

## Usage

### Managing Agencies

#### Add a new agency
```bash
# Add an agency without generating scraper
scrap-immo agency add "Agency Name" "https://agency-website.com"

# Add an agency and generate scraper immediately
scrap-immo agency add "Agency Name" "https://agency-website.com" --generate-scraper

# Provide a sample listing URL for better scraper generation
scrap-immo agency add "Agency Name" "https://agency-website.com" \
  --generate-scraper \
  --sample-url "https://agency-website.com/property/12345"

# Use Anthropic Claude instead of OpenAI
scrap-immo agency add "Agency Name" "https://agency-website.com" \
  --generate-scraper \
  --provider anthropic

# Use OpenAI GPT-4 instead of Gemini
scrap-immo agency add "Agency Name" "https://agency-website.com" \
  --generate-scraper \
  --provider openai
```

#### List all agencies
```bash
scrap-immo agency list
```

#### Generate scraper for an existing agency
```bash
scrap-immo agency generate-scraper AGENCY_ID

# With sample URL
scrap-immo agency generate-scraper AGENCY_ID \
  --sample-url "https://agency-website.com/property/12345"
```

#### Remove an agency
```bash
scrap-immo agency remove AGENCY_ID
```

### Running Scrapers

#### Scrape a specific agency
```bash
scrap-immo scrape agency AGENCY_ID
```

#### Scrape all active agencies
```bash
scrap-immo scrape all
```

### Viewing Properties

#### List properties
```bash
# List recent properties
scrap-immo properties list

# Filter by agency
scrap-immo properties list --agency-id AGENCY_ID

# Show more properties
scrap-immo properties list --limit 50
```

#### Count properties
```bash
scrap-immo properties count
```

### Viewing Logs

```bash
# View recent scraper logs
scrap-immo logs

# Show more logs
scrap-immo logs --limit 20
```

## Architecture

### Components

1. **Database Layer** (`scrap_immo/database/`)
   - SQLAlchemy-based ORM
   - Supports SQLite, PostgreSQL, and other SQL databases
   - Manages agencies, properties, images, and scraper logs

2. **AI Agent** (`scrap_immo/ai_agent/`)
   - Generates scraper scripts using GPT-4 or Claude
   - Creates reusable Python scripts for each agency
   - Validates generated scripts

3. **Scraper Executor** (`scrap_immo/scrapers/`)
   - Dynamically loads and executes generated scrapers
   - Manages property deduplication
   - Tracks scraping statistics

4. **CLI** (`scrap_immo/cli.py`)
   - User-friendly command-line interface
   - Manages all operations (agencies, scraping, viewing data)

### Database Schema

- **agencies**: Real estate agency information
- **properties**: Property listings with all details
- **property_images**: Images associated with properties
- **scraper_logs**: Execution history and statistics

## How It Works

1. **Add an Agency**: Provide the agency name and website URL
2. **Generate Scraper**: The AI agent analyzes the website and generates a custom Python scraper
3. **Run Scraper**: Execute the generated scraper to extract property data
4. **Store Data**: Properties are saved to the database with deduplication
5. **Repeat**: Run scrapers periodically to keep data up-to-date

## Generated Scrapers

Generated scrapers are stored in `scrapers/generated/` and follow this structure:

```python
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

def scrape_properties() -> List[Dict[str, Any]]:
    """Scrape property listings."""
    properties = []
    # Custom scraping logic for the agency
    return properties
```

Each scraper returns a list of dictionaries with standardized property information.

## Configuration

### Environment Variables

- `DATABASE_URL`: Database connection string (default: SQLite)
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Google Gemini API key (default provider)
- `OPENAI_API_KEY`: OpenAI API key for GPT-4 (alternative)
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude (alternative)

### Database Options

```bash
# SQLite (default)
export DATABASE_URL="sqlite:///./scrap_immo.db"

# PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost/scrap_immo"

# MySQL
export DATABASE_URL="mysql://user:password@localhost/scrap_immo"
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black scrap_immo/
ruff check scrap_immo/
```

## Project Goals

This project aims to:
- Replace commercial property aggregators like ImmoWeb
- Provide a flexible, extensible system for property data collection
- Use AI to reduce manual scraper development effort
- Build a comprehensive property database for analysis and comparison

## Future Enhancements

- [ ] Web UI for browsing properties
- [ ] Property comparison features
- [ ] Price history tracking
- [ ] Email notifications for new properties
- [ ] Advanced filtering and search
- [ ] Image download and local storage
- [ ] Property deduplication across agencies
- [ ] API for third-party integrations

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Gaspard Merten