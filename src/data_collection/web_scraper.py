import asyncio
import random
from typing import List, Dict, Any
import pandas as pd
from playwright.async_api import async_playwright, Page
from .models import PropertyRecord, AppealRecord, CollectionResult


class LackawannaDataCollector:
    
    def __init__(self):
        self.base_url = "https://lcao.lackawannacounty.org"
        self.session_limit = 50
        self.request_delay = random.uniform(2, 5)
        self.request_count = 0
        self.browser = None
        self.page = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
    
    async def _setup_anti_detection(self):
        """Set up anti-detection measures for the browser"""
        if not self.page:
            return
            
        # Rotate user agent
        user_agent = random.choice(self.user_agents)
        await self.page.set_user_agent(user_agent)
        
        # Set realistic viewport
        await self.page.set_viewport({'width': 1920, 'height': 1080})
        
        # Set extra headers
        await self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
    
    async def _apply_rate_limiting(self):
        """Apply rate limiting with random delays"""
        delay = random.uniform(2, 5)
        await asyncio.sleep(delay)
    
    async def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make a request with rate limiting and session limits"""
        if self.request_count >= self.session_limit:
            raise Exception("Session request limit reached")
        
        await self._apply_rate_limiting()
        self.request_count += 1
        
        # This is a mock implementation for testing
        # In a real implementation, this would make actual HTTP requests
        if endpoint.startswith('/property/'):
            return {
                'property_id': '12-345-67',
                'address': '123 Main St, Scranton, PA',
                'assessed_value': 125000,
                'market_value': 150000,
                'owner_name': 'John Doe',
                'property_type': 'Residential'
            }
        elif endpoint == '/appeals':
            return [{
                'appeal_id': 'AP-2024-001',
                'property_id': '12-345-67',
                'appeal_date': '2024-01-15',
                'status': 'Pending',
                'requested_value': 100000,
                'reason': 'Overassessment'
            }]
        else:
            return {}
    
    async def fetch_property_data(self, property_id: str) -> PropertyRecord:
        """Fetch property data for a specific property ID"""
        endpoint = f"/property/{property_id}"
        data = await self._make_request(endpoint)
        return PropertyRecord(**data)
    
    async def fetch_appeals_data(self) -> List[AppealRecord]:
        """Fetch all appeals data"""
        data = await self._make_request("/appeals")
        return [AppealRecord(**appeal) for appeal in data]
    
    async def collect_batch(self, property_ids: List[str]) -> List[PropertyRecord]:
        """Collect property data for a batch of property IDs"""
        results = []
        for property_id in property_ids:
            property_data = await self.fetch_property_data(property_id)
            results.append(property_data)
        return results
    
    def to_dataframe(self, records: List[PropertyRecord]) -> pd.DataFrame:
        """Convert property records to pandas DataFrame"""
        data = [record.model_dump() for record in records]
        return pd.DataFrame(data)
    
    async def __aenter__(self):
        """Async context manager entry"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        await self._setup_anti_detection()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser:
            await self.browser.close()