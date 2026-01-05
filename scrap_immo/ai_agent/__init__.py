"""AI agent for generating property scraper scripts."""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path


class ScraperGenerator:
    """AI-powered scraper script generator."""
    
    def __init__(self, provider: str = "gemini", api_key: Optional[str] = None):
        """Initialize the scraper generator.
        
        Args:
            provider: AI provider to use ('gemini', 'openai', or 'anthropic')
            api_key: API key for the provider (or use environment variable)
        """
        self.provider = provider.lower()
        
        if self.provider == "gemini":
            import google.genai as genai
            api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError(
                    "Gemini API key must be provided via api_key parameter or "
                    "GEMINI_API_KEY/GOOGLE_API_KEY environment variable"
                )
            self.client = genai.Client(api_key=api_key)
            self.model = "gemini-2.0-flash-exp"
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-opus-20240229"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate_scraper(
        self,
        agency_name: str,
        website_url: str,
        sample_listing_url: Optional[str] = None,
    ) -> str:
        """Generate a scraper script for a real estate agency website.
        
        Args:
            agency_name: Name of the agency
            website_url: Base URL of the agency website
            sample_listing_url: Optional URL of a sample property listing
            
        Returns:
            str: Generated Python scraper script
        """
        prompt = self._build_prompt(agency_name, website_url, sample_listing_url)
        
        if self.provider == "gemini":
            return self._generate_with_gemini(prompt)
        elif self.provider == "openai":
            return self._generate_with_openai(prompt)
        elif self.provider == "anthropic":
            return self._generate_with_anthropic(prompt)
    
    def _build_prompt(
        self,
        agency_name: str,
        website_url: str,
        sample_listing_url: Optional[str] = None,
    ) -> str:
        """Build the prompt for the AI agent."""
        prompt = f"""You are an expert web scraping engineer. Your task is to create a Python script that scrapes property listings from a real estate agency website.

**Agency Information:**
- Name: {agency_name}
- Website: {website_url}
"""
        
        if sample_listing_url:
            prompt += f"- Sample listing URL: {sample_listing_url}\n"
        
        prompt += """
**Requirements:**
1. The script must be a standalone Python module with a main function called `scrape_properties()`
2. The function should return a list of dictionaries, where each dictionary represents a property
3. Each property dictionary must include the following keys (use None if not available):
   - 'title': Property title/headline
   - 'description': Full property description
   - 'property_type': Type of property (apartment, house, etc.)
   - 'transaction_type': 'sale' or 'rent'
   - 'address': Street address
   - 'city': City name
   - 'postal_code': Postal code
   - 'country': Country name
   - 'price': Price as a float
   - 'currency': Currency code (e.g., 'EUR', 'USD')
   - 'surface_area': Surface area in square meters
   - 'num_bedrooms': Number of bedrooms
   - 'num_bathrooms': Number of bathrooms
   - 'num_rooms': Total number of rooms
   - 'floor': Floor number
   - 'year_built': Year of construction
   - 'features': List of features/amenities
   - 'images': List of image URLs
   - 'property_url': URL to the property listing
   - 'external_id': Property ID from the agency website

4. Use requests and BeautifulSoup for scraping (avoid Selenium unless absolutely necessary)
5. Include proper error handling and logging
6. Add delays between requests to be respectful to the server
7. Handle pagination if the website has multiple pages of listings
8. Extract as much information as possible, but handle missing data gracefully

**Output Format:**
Provide ONLY the Python code, no explanations. The code should start with imports and end with the scrape_properties() function.

**Example Structure:**
```python
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_properties() -> List[Dict[str, Any]]:
    \"\"\"Scrape property listings.\"\"\"
    properties = []
    
    # Your scraping logic here
    
    return properties
```

Generate the complete scraper script now:
"""
        return prompt
    
    def _generate_with_gemini(self, prompt: str) -> str:
        """Generate script using Google Gemini."""
        # Add system instruction to the prompt
        system_instruction = (
            "You are an expert Python web scraping engineer. "
            "Generate clean, efficient, and well-documented scraping code."
        )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                'temperature': 0.3,
                'max_output_tokens': 4000,
                'system_instruction': system_instruction,
            }
        )
        
        content = response.text
        # Extract code from markdown code blocks if present
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
        
        return code
    
    def _generate_with_openai(self, prompt: str) -> str:
        """Generate script using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Python web scraping engineer. Generate clean, efficient, and well-documented scraping code.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content
        # Extract code from markdown code blocks if present
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
        
        return code
    
    def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate script using Anthropic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.3,
            system="You are an expert Python web scraping engineer. Generate clean, efficient, and well-documented scraping code.",
            messages=[{"role": "user", "content": prompt}],
        )
        
        content = response.content[0].text
        # Extract code from markdown code blocks if present
        if "```python" in content:
            code = content.split("```python")[1].split("```")[0].strip()
        elif "```" in content:
            code = content.split("```")[1].split("```")[0].strip()
        else:
            code = content.strip()
        
        return code
    
    def save_scraper(self, script_content: str, agency_name: str, output_dir: str = "scrapers/generated") -> str:
        """Save the generated scraper script to a file.
        
        Args:
            script_content: The generated Python script
            agency_name: Name of the agency (used for filename)
            output_dir: Directory to save the script
            
        Returns:
            str: Path to the saved script
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create a safe filename from agency name
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in agency_name.lower())
        filename = f"{safe_name}_scraper.py"
        filepath = output_path / filename
        
        # Save the script
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        return str(filepath)
    
    def validate_scraper(self, script_path: str) -> bool:
        """Validate that a scraper script is syntactically correct and has required function.
        
        Args:
            script_path: Path to the scraper script
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                script_content = f.read()
            
            # Check syntax
            compile(script_content, script_path, "exec")
            
            # Check for required function
            if "def scrape_properties()" not in script_content:
                return False
            
            return True
        except Exception as e:
            print(f"Validation error: {e}")
            return False
