#!/usr/bin/env python3
"""
Job URL Scraper for Jobright.ai and LinkedIn

This scraper automatically discovers job postings from multiple platforms:
- Jobright.ai
- LinkedIn Jobs
- (Extensible to other platforms)

Usage:
    python workers/job_scraper.py scrape --keywords "Python Developer" --location "Remote"
    python workers/job_scraper.py scrape --platform linkedin --keywords "Software Engineer"
    python workers/job_scraper.py scrape --platform all --keywords "Backend Engineer"
"""

import os
import sys
import json
import uuid
import logging
import argparse
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('job_scraper')


class JobScraper:
    """Base class for job scraping."""
    
    def __init__(self, headless: bool = False):
        """Initialize scraper."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required. Run: pip install playwright && playwright install chromium")
        
        if not BS4_AVAILABLE:
            raise ImportError("BeautifulSoup is required. Run: pip install beautifulsoup4 lxml")
        
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        # Initialize Supabase if available
        if SUPABASE_AVAILABLE:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if supabase_url and supabase_key:
                self.supabase: Client = create_client(supabase_url, supabase_key)
                logger.info("✅ Supabase initialized")
            else:
                self.supabase = None
                logger.warning("⚠️  Supabase credentials not found")
        else:
            self.supabase = None
            logger.warning("⚠️  Supabase not available")
    
    async def start_browser(self):
        """Start Playwright browser."""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        
        logger.info("✅ Browser started")
    
    async def close_browser(self):
        """Close browser."""
        try:
            if self.context:
                await self.context.close()
        except:
            pass
        
        try:
            if self.browser:
                await self.browser.close()
        except:
            pass
        
        try:
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except:
            pass
    
    async def random_delay(self, min_sec: float = 1, max_sec: float = 3):
        """Random delay."""
        import random
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    def save_jobs_to_database(self, jobs: List[Dict[str, Any]]) -> int:
        """Save jobs to Supabase."""
        if not self.supabase:
            logger.warning("Supabase not configured")
            return 0
        
        saved = 0
        for job in jobs:
            try:
                # Check if exists
                existing = self.supabase.table('jobs').select('id').eq('raw->>url', job.get('url')).execute()
                
                if existing.data:
                    logger.debug(f"Job exists: {job.get('title')}")
                    continue
                
                # Insert job
                job_data = {
                    'id': str(uuid.uuid4()),
                    'source': job.get('source', 'unknown'),
                    'title': job.get('title', 'Unknown'),
                    'company': job.get('company', 'Unknown'),
                    'location': job.get('location'),
                    'posted_at': job.get('posted_at'),
                    'raw': {
                        'url': job.get('url'),
                        'description': job.get('description', ''),
                        'requirements': job.get('requirements', []),
                        'scraped_at': datetime.now(timezone.utc).isoformat()
                    },
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                response = self.supabase.table('jobs').insert(job_data).execute()
                
                if response.data:
                    saved += 1
                    logger.info(f"✅ Saved: {job.get('title')} at {job.get('company')}")
            
            except Exception as e:
                logger.error(f"Error saving job: {e}")
        
        return saved


class LinkedInScraper(JobScraper):
    """LinkedIn job scraper."""
    
    BASE_URL = "https://www.linkedin.com"
    
    async def scrape_jobs(self, keywords: str, location: str = "", max_pages: int = 3) -> List[Dict]:
        """Scrape LinkedIn jobs."""
        logger.info(f"🔍 Scraping LinkedIn: {keywords} in {location or 'Worldwide'}")
        
        jobs = []
        page = None
        
        try:
            await self.start_browser()
            
            # Build search URL
            params = {
                'keywords': keywords,
                'location': location or '',
                'f_TPR': 'r604800',  # Last week
                'position': 1,
                'pageNum': 0
            }
            
            url = f"{self.BASE_URL}/jobs/search/?{urlencode(params)}"
            logger.info(f"Navigating to: {url}")
            
            # Create page
            page = await self.context.new_page()
            
            # Navigate
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await self.random_delay(2, 4)
            
            # Extract jobs
            jobs = await self._extract_jobs(page, max_results=max_pages * 25)
            
            # Close page first
            if page:
                await page.close()
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        finally:
            # Cleanup
            try:
                if page and not page.is_closed():
                    await page.close()
            except:
                pass
            
            await self.close_browser()
        
        logger.info(f"✅ Found {len(jobs)} jobs on LinkedIn")
        return jobs
    
    async def _extract_jobs(self, page: Page, max_results: int = 75) -> List[Dict]:
        """Extract job listings."""
        jobs = []
        
        try:
            await page.wait_for_selector('.job-search-card', timeout=10000)
            
            job_cards = await page.query_selector_all('.job-search-card')
            logger.info(f"Found {len(job_cards)} job cards")
            
            for card in job_cards[:max_results]:
                try:
                    job = await self._parse_card(card)
                    if job and job.get('url'):
                        jobs.append(job)
                        await self.random_delay(0.5, 1)
                except Exception as e:
                    logger.debug(f"Error parsing card: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting jobs: {e}")
        
        return jobs
    
    async def _parse_card(self, card) -> Dict:
        """Parse job card."""
        job = {
            'source': 'linkedin',
            'url': None,
            'title': None,
            'company': None,
            'location': None,
            'posted_at': None
        }
        
        try:
            # URL
            link = await card.query_selector('a[href*="/jobs/view/"]')
            if link:
                href = await link.get_attribute('href')
                if href:
                    job_id = href.split('/jobs/view/')[-1].split('?')[0]
                    job['url'] = f"{self.BASE_URL}/jobs/view/{job_id}"
            
            # Title
            title_elem = await card.query_selector('h3')
            if title_elem:
                job['title'] = (await title_elem.inner_text()).strip()
            
            # Company
            company_elem = await card.query_selector('h4')
            if company_elem:
                job['company'] = (await company_elem.inner_text()).strip()
            
            # Location
            location_elem = await card.query_selector('.job-search-card__location')
            if location_elem:
                job['location'] = (await location_elem.inner_text()).strip()
        
        except Exception as e:
            logger.debug(f"Error parsing elements: {e}")
        
        return job


async def main():
    """Main CLI."""
    parser = argparse.ArgumentParser(description='Job Scraper')
    parser.add_argument('command', choices=['scrape'], help='Command')
    parser.add_argument('--platform', choices=['linkedin', 'all'], default='linkedin')
    parser.add_argument('--keywords', required=True, help='Job keywords')
    parser.add_argument('--location', default='', help='Job location')
    parser.add_argument('--max-pages', type=int, default=3, help='Max pages')
    parser.add_argument('--headless', action='store_true', help='Headless mode')
    
    args = parser.parse_args()
    
    if args.command == 'scrape':
        all_jobs = []
        
        # Scrape LinkedIn
        if args.platform in ['linkedin', 'all']:
            print("\n🔍 Scraping LinkedIn...")
            print("=" * 60)
            
            scraper = LinkedInScraper(headless=args.headless)
            jobs = await scraper.scrape_jobs(
                keywords=args.keywords,
                location=args.location,
                max_pages=args.max_pages
            )
            all_jobs.extend(jobs)
            
            print(f"✅ Found {len(jobs)} jobs")
        
        # Save to database
        if all_jobs:
            print(f"\n💾 Saving {len(all_jobs)} jobs to database...")
            scraper = JobScraper()
            saved = scraper.save_jobs_to_database(all_jobs)
            print(f"✅ Saved {saved} jobs to Supabase")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SCRAPING SUMMARY")
        print("=" * 60)
        print(f"Total jobs found: {len(all_jobs)}")
        print(f"Keywords: {args.keywords}")
        print(f"Location: {args.location or 'Any'}")
        print("=" * 60)
        
        # Sample
        if all_jobs:
            print("\n📋 Sample Jobs:")
            for job in all_jobs[:5]:
                print(f"\n  - {job.get('title')} at {job.get('company')}")
                print(f"    Location: {job.get('location')}")
                print(f"    URL: {job.get('url')}")


if __name__ == "__main__":
    asyncio.run(main())

