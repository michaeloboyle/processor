import asyncio
import json
import random
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page
import pandas as pd
from datetime import datetime


class LackawannaRealDataCollector:
    """Real data collector for Lackawanna County assessment database"""
    
    def __init__(self):
        self.base_url = "https://lcao.lackawannacounty.org"
        self.session_limit = 50
        self.request_count = 0
        self.browser = None
        self.page = None
        self.collected_data = {
            'properties': [],
            'appeals': [],
            'appeal_guidelines': [],
            'assessment_criteria': [],
            'forms_and_procedures': [],
            'raw_html': []
        }
        
    async def __aenter__(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        
        # Set realistic user agent
        await self.page.set_extra_http_headers({
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser"""
        if self.browser:
            await self.browser.close()
    
    async def explore_site_structure(self) -> Dict[str, Any]:
        """Explore the site to understand its structure"""
        try:
            print(f"Exploring {self.base_url}...")
            await self.page.goto(self.base_url, wait_until='networkidle')
            
            # Get page title and basic info
            title = await self.page.title()
            url = self.page.url
            
            # Look for forms, search boxes, navigation
            forms = await self.page.locator('form').count()
            links = await self.page.locator('a').count()
            
            # Try to find search functionality
            search_inputs = await self.page.locator('input[type="text"]').count()
            search_buttons = await self.page.locator('input[type="submit"], button').count()
            
            # Get page content for analysis
            content = await self.page.content()
            
            structure = {
                'title': title,
                'url': url,
                'forms_count': forms,
                'links_count': links,
                'search_inputs': search_inputs,
                'search_buttons': search_buttons,
                'page_length': len(content),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            print(f"Site exploration completed:")
            print(f"  Title: {title}")
            print(f"  Forms: {forms}, Links: {links}")
            print(f"  Search inputs: {search_inputs}, Buttons: {search_buttons}")
            
            return structure
            
        except Exception as e:
            print(f"Error exploring site: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow().isoformat()}
    
    async def find_search_functionality(self) -> Dict[str, Any]:
        """Try to find and interact with search functionality"""
        try:
            # Common selectors for property search
            search_selectors = [
                'input[placeholder*="search"]',
                'input[placeholder*="property"]',
                'input[placeholder*="address"]',
                'input[name*="search"]',
                'input[name*="property"]',
                'input[id*="search"]',
                'input[id*="property"]'
            ]
            
            search_info = {}
            
            for selector in search_selectors:
                elements = await self.page.locator(selector).count()
                if elements > 0:
                    search_info[selector] = elements
                    
                    # Try to get attributes
                    element = self.page.locator(selector).first
                    try:
                        placeholder = await element.get_attribute('placeholder')
                        name = await element.get_attribute('name')
                        id_attr = await element.get_attribute('id')
                        
                        search_info[f"{selector}_details"] = {
                            'placeholder': placeholder,
                            'name': name,
                            'id': id_attr
                        }
                    except:
                        pass
            
            return search_info
            
        except Exception as e:
            return {'error': str(e)}
    
    async def attempt_property_search(self, search_term: str = "Main St") -> Dict[str, Any]:
        """Attempt to search for properties"""
        try:
            print(f"Attempting property search for: {search_term}")
            
            # Try common search input selectors
            search_found = False
            search_selectors = [
                'input[type="text"]',
                'input[placeholder*="search"]',
                'input[name*="search"]'
            ]
            
            for selector in search_selectors:
                try:
                    await self.page.fill(selector, search_term)
                    search_found = True
                    print(f"Found search input: {selector}")
                    break
                except:
                    continue
            
            if not search_found:
                return {'error': 'No search input found'}
            
            # Try to submit search
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'button:has-text("Search")',
                'input[value*="Search"]'
            ]
            
            for selector in submit_selectors:
                try:
                    await self.page.click(selector)
                    print(f"Clicked search button: {selector}")
                    break
                except:
                    continue
            
            # Wait for results
            await self.page.wait_for_timeout(3000)
            
            # Capture results
            content = await self.page.content()
            url = self.page.url
            title = await self.page.title()
            
            return {
                'search_term': search_term,
                'result_url': url,
                'result_title': title,
                'content_length': len(content),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'error': str(e), 'search_term': search_term}
    
    async def extract_property_data_sample(self) -> List[Dict[str, Any]]:
        """Extract sample property data from current page"""
        try:
            # Look for common property data patterns
            properties = []
            
            # Try to find tables with property data
            tables = await self.page.locator('table').count()
            print(f"Found {tables} tables on page")
            
            if tables > 0:
                for i in range(min(tables, 3)):  # Check first 3 tables
                    table = self.page.locator('table').nth(i)
                    rows = await table.locator('tr').count()
                    
                    if rows > 1:  # Has header + data rows
                        print(f"Table {i} has {rows} rows")
                        
                        # Get headers
                        headers = []
                        header_cells = table.locator('tr').first.locator('th, td')
                        header_count = await header_cells.count()
                        
                        for j in range(header_count):
                            header_text = await header_cells.nth(j).inner_text()
                            headers.append(header_text.strip())
                        
                        # Get first few data rows
                        for row_idx in range(1, min(rows, 6)):  # First 5 data rows
                            row = table.locator('tr').nth(row_idx)
                            cells = row.locator('td')
                            cell_count = await cells.count()
                            
                            row_data = {}
                            for cell_idx in range(min(cell_count, len(headers))):
                                cell_text = await cells.nth(cell_idx).inner_text()
                                header = headers[cell_idx] if cell_idx < len(headers) else f"column_{cell_idx}"
                                row_data[header] = cell_text.strip()
                            
                            if row_data:  # Only add if we got data
                                properties.append({
                                    'table_index': i,
                                    'row_index': row_idx,
                                    'data': row_data,
                                    'headers': headers
                                })
            
            # Also look for div-based property listings
            property_divs = await self.page.locator('div:has-text("Property"), div:has-text("Address")').count()
            print(f"Found {property_divs} potential property divs")
            
            return properties
            
        except Exception as e:
            print(f"Error extracting property data: {e}")
            return []
    
    async def find_appeal_information(self) -> Dict[str, Any]:
        """Look for appeal-related pages and information"""
        try:
            appeal_info = {
                'appeal_links': [],
                'guideline_links': [],
                'form_links': [],
                'procedure_links': [],
                'deadline_info': [],
                'fee_info': []
            }
            
            # Look for appeal-related links
            appeal_keywords = [
                'appeal', 'Assessment Appeal', 'Tax Appeal', 'Property Appeal',
                'appeal process', 'appeal form', 'appeal guidelines',
                'assessment review', 'property review', 'tax review'
            ]
            
            guideline_keywords = [
                'guidelines', 'criteria', 'procedure', 'process', 'requirements',
                'how to appeal', 'appeal steps', 'appeal instructions'
            ]
            
            form_keywords = [
                'form', 'application', 'petition', 'request form',
                'appeal form', 'assessment form'
            ]
            
            # Search for links containing these keywords
            all_links = await self.page.locator('a').all()
            
            for link in all_links:
                try:
                    link_text = await link.inner_text()
                    href = await link.get_attribute('href')
                    
                    if not href:
                        continue
                    
                    link_text_lower = link_text.lower()
                    
                    # Categorize links
                    for keyword in appeal_keywords:
                        if keyword.lower() in link_text_lower:
                            appeal_info['appeal_links'].append({
                                'text': link_text.strip(),
                                'href': href,
                                'keyword_match': keyword
                            })
                            break
                    
                    for keyword in guideline_keywords:
                        if keyword.lower() in link_text_lower:
                            appeal_info['guideline_links'].append({
                                'text': link_text.strip(),
                                'href': href,
                                'keyword_match': keyword
                            })
                            break
                    
                    for keyword in form_keywords:
                        if keyword.lower() in link_text_lower:
                            appeal_info['form_links'].append({
                                'text': link_text.strip(),
                                'href': href,
                                'keyword_match': keyword
                            })
                            break
                
                except Exception as e:
                    continue
            
            # Look for deadline and fee information in page text
            page_text = await self.page.inner_text('body')
            
            # Search for deadline patterns
            deadline_patterns = [
                r'appeal.*deadline.*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'file.*appeal.*(\d+)\s*days',
                r'appeal.*must.*filed.*(\d+)\s*days',
                r'deadline.*appeal.*(\w+\s+\d{1,2},?\s+\d{4})'
            ]
            
            import re
            for pattern in deadline_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    appeal_info['deadline_info'].extend(matches)
            
            # Search for fee patterns
            fee_patterns = [
                r'appeal.*fee.*\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'filing.*fee.*\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'cost.*appeal.*\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ]
            
            for pattern in fee_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    appeal_info['fee_info'].extend(matches)
            
            return appeal_info
            
        except Exception as e:
            return {'error': str(e)}
    
    async def collect_appeal_guidelines(self, appeal_links: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Visit appeal-related pages and collect guidelines"""
        guidelines = []
        
        for link_info in appeal_links[:5]:  # Limit to first 5 links
            try:
                href = link_info['href']
                
                # Handle relative URLs
                if href.startswith('/'):
                    full_url = self.base_url + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"{self.base_url}/{href}"
                
                print(f"Visiting appeal page: {full_url}")
                
                # Navigate to the page
                await self.page.goto(full_url, wait_until='networkidle', timeout=10000)
                await asyncio.sleep(2)
                
                # Extract content
                title = await self.page.title()
                content = await self.page.inner_text('body')
                html_content = await self.page.content()
                
                # Look for structured information
                guideline_data = {
                    'source_link': link_info,
                    'page_title': title,
                    'page_url': full_url,
                    'content_length': len(content),
                    'timestamp': datetime.utcnow().isoformat(),
                    'extracted_sections': {}
                }
                
                # Extract specific sections
                sections_to_find = [
                    ('appeal_process', ['process', 'steps', 'procedure', 'how to']),
                    ('deadlines', ['deadline', 'due date', 'filing date', 'time limit']),
                    ('requirements', ['requirement', 'eligibility', 'criteria', 'must']),
                    ('fees', ['fee', 'cost', 'payment', 'charge']),
                    ('forms', ['form', 'application', 'petition', 'document']),
                    ('evidence', ['evidence', 'documentation', 'proof', 'support']),
                    ('hearing', ['hearing', 'meeting', 'review', 'board'])
                ]
                
                content_lower = content.lower()
                for section_name, keywords in sections_to_find:
                    section_content = []
                    
                    # Find paragraphs containing these keywords
                    paragraphs = content.split('\n')
                    for para in paragraphs:
                        para_lower = para.lower()
                        if any(keyword in para_lower for keyword in keywords) and len(para.strip()) > 20:
                            section_content.append(para.strip())
                    
                    if section_content:
                        guideline_data['extracted_sections'][section_name] = section_content[:3]  # Top 3 relevant paragraphs
                
                # Look for lists and bullet points
                try:
                    lists = await self.page.locator('ul, ol').all()
                    list_items = []
                    
                    for lst in lists[:5]:  # First 5 lists
                        items = await lst.locator('li').all()
                        current_list = []
                        
                        for item in items[:10]:  # First 10 items per list
                            item_text = await item.inner_text()
                            if len(item_text.strip()) > 5:
                                current_list.append(item_text.strip())
                        
                        if current_list:
                            list_items.append(current_list)
                    
                    guideline_data['structured_lists'] = list_items
                
                except Exception as e:
                    guideline_data['list_extraction_error'] = str(e)
                
                guidelines.append(guideline_data)
                
                # Conservative rate limiting
                await asyncio.sleep(random.uniform(8, 12))
                
            except Exception as e:
                print(f"Error collecting from {link_info.get('href', 'unknown')}: {e}")
                guidelines.append({
                    'source_link': link_info,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return guidelines
    
    async def extract_assessment_criteria(self) -> Dict[str, Any]:
        """Extract information about assessment criteria and methodology"""
        try:
            criteria_info = {
                'assessment_methods': [],
                'valuation_approaches': [],
                'property_types': [],
                'exemptions': [],
                'assessment_dates': [],
                'contact_information': []
            }
            
            # Look for assessment-related content
            page_text = await self.page.inner_text('body')
            
            # Search for assessment methodology patterns
            method_keywords = [
                'market value', 'assessed value', 'fair market value',
                'replacement cost', 'income approach', 'sales comparison',
                'assessment ratio', 'equalization', 'property valuation'
            ]
            
            approach_keywords = [
                'cost approach', 'income approach', 'market approach',
                'sales comparison', 'replacement cost', 'depreciation'
            ]
            
            # Extract sentences containing these keywords
            sentences = page_text.split('.')
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:
                    continue
                
                sentence_lower = sentence.lower()
                
                for keyword in method_keywords:
                    if keyword in sentence_lower:
                        criteria_info['assessment_methods'].append({
                            'content': sentence,
                            'keyword_match': keyword
                        })
                        break
                
                for keyword in approach_keywords:
                    if keyword in sentence_lower:
                        criteria_info['valuation_approaches'].append({
                            'content': sentence,
                            'keyword_match': keyword
                        })
                        break
            
            # Look for contact information
            import re
            
            # Phone numbers
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phones = re.findall(phone_pattern, page_text)
            
            # Email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)
            
            # Addresses (basic pattern)
            address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)(?:\s*,\s*[\w\s]+)*'
            addresses = re.findall(address_pattern, page_text, re.IGNORECASE)
            
            criteria_info['contact_information'] = {
                'phones': list(set(phones)),
                'emails': list(set(emails)),
                'addresses': list(set(addresses))[:3]  # First 3 addresses
            }
            
            return criteria_info
            
        except Exception as e:
            return {'error': str(e)}
    
    async def collect_sample_data(self, max_searches: int = 5) -> Dict[str, Any]:
        """Collect sample data using various search terms"""
        sample_data = {
            'site_structure': {},
            'search_functionality': {},
            'appeal_information': {},
            'appeal_guidelines': [],
            'assessment_criteria': {},
            'sample_searches': [],
            'property_samples': [],
            'collection_metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'max_searches': max_searches,
                'success_count': 0,
                'error_count': 0
            }
        }
        
        try:
            # 1. Explore site structure
            print("Step 1: Exploring site structure...")
            sample_data['site_structure'] = await self.explore_site_structure()
            
            # 2. Find search functionality
            print("Step 2: Finding search functionality...")
            sample_data['search_functionality'] = await self.find_search_functionality()
            
            # 3. Find appeal information and guidelines
            print("Step 3: Finding appeal information...")
            sample_data['appeal_information'] = await self.find_appeal_information()
            
            # 4. Collect appeal guidelines from found links
            appeal_links = sample_data['appeal_information'].get('appeal_links', [])
            guideline_links = sample_data['appeal_information'].get('guideline_links', [])
            all_appeal_links = appeal_links + guideline_links
            
            if all_appeal_links:
                print("Step 4: Collecting appeal guidelines...")
                sample_data['appeal_guidelines'] = await self.collect_appeal_guidelines(all_appeal_links)
            
            # 5. Extract assessment criteria
            print("Step 5: Extracting assessment criteria...")
            sample_data['assessment_criteria'] = await self.extract_assessment_criteria()
            
            # 6. Try sample searches
            search_terms = ["Main St", "Oak Ave", "Pine St", "1st Street", "Church St"]
            
            for i, term in enumerate(search_terms[:max_searches]):
                print(f"Step 6.{i+1}: Searching for '{term}'...")
                await asyncio.sleep(random.uniform(5, 8))  # Conservative rate limiting
                
                search_result = await self.attempt_property_search(term)
                
                if 'error' not in search_result:
                    # Extract property data from results
                    property_samples = await self.extract_property_data_sample()
                    search_result['property_samples'] = property_samples
                    sample_data['collection_metadata']['success_count'] += 1
                else:
                    sample_data['collection_metadata']['error_count'] += 1
                
                sample_data['sample_searches'].append(search_result)
                
                # Navigate back to start for next search
                try:
                    await self.page.goto(self.base_url, wait_until='networkidle')
                    await asyncio.sleep(1)
                except:
                    pass
            
            return sample_data
            
        except Exception as e:
            sample_data['collection_error'] = str(e)
            return sample_data
    
    def save_sample_data(self, data: Dict[str, Any], filename: str = None) -> str:
        """Save collected sample data to file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"lackawanna_sample_data_{timestamp}.json"
        
        filepath = f"data_samples/{filename}"
        
        # Create directory if it doesn't exist
        import os
        os.makedirs("data_samples", exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Sample data saved to: {filepath}")
        return filepath


async def collect_lackawanna_sample():
    """Main function to collect sample data"""
    async with LackawannaRealDataCollector() as collector:
        print("Starting Lackawanna County data collection...")
        sample_data = await collector.collect_sample_data(max_searches=1)
        
        # Save the data
        filepath = collector.save_sample_data(sample_data)
        
        # Print summary
        print("\n=== Collection Summary ===")
        print(f"Site title: {sample_data.get('site_structure', {}).get('title', 'Unknown')}")
        print(f"Appeal links found: {len(sample_data.get('appeal_information', {}).get('appeal_links', []))}")
        print(f"Guideline links found: {len(sample_data.get('appeal_information', {}).get('guideline_links', []))}")
        print(f"Appeal guidelines collected: {len(sample_data.get('appeal_guidelines', []))}")
        print(f"Assessment criteria sections: {len(sample_data.get('assessment_criteria', {}).get('assessment_methods', []))}")
        print(f"Property searches attempted: {len(sample_data.get('sample_searches', []))}")
        print(f"Success count: {sample_data.get('collection_metadata', {}).get('success_count', 0)}")
        print(f"Error count: {sample_data.get('collection_metadata', {}).get('error_count', 0)}")
        print(f"Data saved to: {filepath}")
        
        return sample_data


if __name__ == "__main__":
    # Run the data collection
    sample_data = asyncio.run(collect_lackawanna_sample())