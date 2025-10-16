#!/usr/bin/env python3
"""
API-Based Job Fetcher

Fetches jobs from legal, free job APIs:
- Adzuna (5000 calls/month free)
- The Muse (unlimited, no auth)
- Remote OK (unlimited, no auth)
- JSearch (RapidAPI - 100 calls/month free)

Usage:
    python workers/api_job_fetcher.py fetch --keywords "Python Developer" --location "Remote"
    python workers/api_job_fetcher.py fetch --api adzuna --keywords "Software Engineer"
    python workers/api_job_fetcher.py fetch --api all --keywords "Backend Engineer"
"""

import os
import sys
import json
import uuid
import logging
import argparse
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_job_fetcher')


class JobFetcher:
    """Base class for API job fetching."""
    
    def __init__(self):
        """Initialize fetcher."""
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
                        'description': job.get('description', '')[:1000],  # Limit length
                        'requirements': job.get('requirements', []),
                        'salary': job.get('salary'),
                        'job_type': job.get('job_type'),
                        'fetched_at': datetime.now(timezone.utc).isoformat()
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


class AdzunaFetcher(JobFetcher):
    """Fetch jobs from Adzuna API (Free: 5000 calls/month)"""
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    
    def fetch_jobs(self, keywords: str, location: str = "Remote", max_results: int = 50) -> List[Dict]:
        """Fetch jobs from Adzuna."""
        logger.info(f"🔍 Fetching from Adzuna: {keywords} in {location}")
        
        app_id = os.getenv('ADZUNA_APP_ID')
        app_key = os.getenv('ADZUNA_APP_KEY')
        
        if not app_id or not app_key:
            logger.warning("⚠️  Adzuna API credentials not found")
            logger.info("👉 Get free API key at: https://developer.adzuna.com/")
            return []
        
        jobs = []
        
        try:
            # Adzuna uses country codes
            url = f"{self.BASE_URL}/us/search/1"
            
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "results_per_page": min(max_results, 50),
                "what": keywords,
                "where": location,
                "content-type": "application/json"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            for job in results:
                jobs.append({
                    'source': 'adzuna',
                    'title': job.get('title', 'Unknown'),
                    'company': job.get('company', {}).get('display_name', 'Unknown'),
                    'location': job.get('location', {}).get('display_name', location),
                    'url': job.get('redirect_url', ''),
                    'description': job.get('description', '')[:500],
                    'posted_at': job.get('created'),
                    'salary': job.get('salary_max')
                })
            
            logger.info(f"✅ Found {len(jobs)} jobs from Adzuna")
        
        except Exception as e:
            logger.error(f"Error fetching from Adzuna: {e}")
        
        return jobs


class TheMuseFetcher(JobFetcher):
    """Fetch jobs from The Muse API (Free, unlimited)"""
    
    BASE_URL = "https://www.themuse.com/api/public/jobs"
    
    def fetch_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Fetch jobs from The Muse."""
        logger.info(f"🔍 Fetching from The Muse: {keywords}")
        
        jobs = []
        
        try:
            params = {
                "page": 0,
                "descending": "true",
                "api_key": "public"
            }
            
            # The Muse doesn't have great keyword search, so we fetch and filter
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            # Filter by keywords
            keywords_lower = keywords.lower().split()
            
            for job in results[:max_results]:
                title = job.get('name', '').lower()
                
                # Simple keyword matching
                if any(kw in title for kw in keywords_lower):
                    jobs.append({
                        'source': 'themuse',
                        'title': job.get('name', 'Unknown'),
                        'company': job.get('company', {}).get('name', 'Unknown'),
                        'location': ', '.join(job.get('locations', [{}])[0].get('name', 'Remote').split() if job.get('locations') else ['Remote']),
                        'url': job.get('refs', {}).get('landing_page', ''),
                        'description': job.get('contents', '')[:500],
                        'posted_at': job.get('publication_date'),
                        'job_type': ', '.join(job.get('type', []))
                    })
            
            logger.info(f"✅ Found {len(jobs)} jobs from The Muse")
        
        except Exception as e:
            logger.error(f"Error fetching from The Muse: {e}")
        
        return jobs


class RemoteOKFetcher(JobFetcher):
    """Fetch jobs from Remote OK API (Free, unlimited)"""
    
    BASE_URL = "https://remoteok.com/api"
    
    def fetch_jobs(self, keywords: str, location: str = "", max_results: int = 50) -> List[Dict]:
        """Fetch jobs from Remote OK."""
        logger.info(f"🔍 Fetching from Remote OK: {keywords}")
        
        jobs = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; JobBot/1.0)'
            }
            
            response = requests.get(self.BASE_URL, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Skip first item (it's metadata)
            results = data[1:] if len(data) > 1 else []
            
            # Filter by keywords
            keywords_lower = keywords.lower().split()
            
            for job in results:
                if isinstance(job, dict):
                    title = job.get('position', '').lower()
                    tags = [tag.lower() for tag in job.get('tags', [])]
                    
                    # Match keywords
                    if any(kw in title or kw in ' '.join(tags) for kw in keywords_lower):
                        jobs.append({
                            'source': 'remoteok',
                            'title': job.get('position', 'Unknown'),
                            'company': job.get('company', 'Unknown'),
                            'location': 'Remote',
                            'url': job.get('url', ''),
                            'description': job.get('description', '')[:500],
                            'posted_at': job.get('date'),
                            'salary': job.get('salary_max'),
                            'job_type': ', '.join(job.get('tags', []))
                        })
                
                if len(jobs) >= max_results:
                    break
            
            logger.info(f"✅ Found {len(jobs)} jobs from Remote OK")
        
        except Exception as e:
            logger.error(f"Error fetching from Remote OK: {e}")
        
        return jobs


def main():
    """Main CLI."""
    parser = argparse.ArgumentParser(description='API Job Fetcher')
    parser.add_argument('command', choices=['fetch'], help='Command')
    parser.add_argument('--api', choices=['adzuna', 'themuse', 'remoteok', 'all'], default='all')
    parser.add_argument('--keywords', required=True, help='Job keywords')
    parser.add_argument('--location', default='Remote', help='Job location')
    parser.add_argument('--max-results', type=int, default=50, help='Max results per API')
    parser.add_argument('--save', action='store_true', default=True, help='Save to database')
    
    args = parser.parse_args()
    
    if args.command == 'fetch':
        all_jobs = []
        
        # Fetch from selected APIs
        if args.api in ['adzuna', 'all']:
            print("\n🔍 Fetching from Adzuna...")
            print("=" * 60)
            
            fetcher = AdzunaFetcher()
            jobs = fetcher.fetch_jobs(
                keywords=args.keywords,
                location=args.location,
                max_results=args.max_results
            )
            all_jobs.extend(jobs)
            print(f"✅ Found {len(jobs)} jobs")
        
        if args.api in ['themuse', 'all']:
            print("\n🔍 Fetching from The Muse...")
            print("=" * 60)
            
            fetcher = TheMuseFetcher()
            jobs = fetcher.fetch_jobs(
                keywords=args.keywords,
                location=args.location,
                max_results=args.max_results
            )
            all_jobs.extend(jobs)
            print(f"✅ Found {len(jobs)} jobs")
        
        if args.api in ['remoteok', 'all']:
            print("\n🔍 Fetching from Remote OK...")
            print("=" * 60)
            
            fetcher = RemoteOKFetcher()
            jobs = fetcher.fetch_jobs(
                keywords=args.keywords,
                location=args.location,
                max_results=args.max_results
            )
            all_jobs.extend(jobs)
            print(f"✅ Found {len(jobs)} jobs")
        
        # Save to database
        if args.save and all_jobs:
            print(f"\n💾 Saving {len(all_jobs)} jobs to database...")
            fetcher = JobFetcher()
            saved = fetcher.save_jobs_to_database(all_jobs)
            print(f"✅ Saved {saved} jobs to Supabase ({len(all_jobs) - saved} duplicates skipped)")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FETCHING SUMMARY")
        print("=" * 60)
        print(f"Total jobs found: {len(all_jobs)}")
        print(f"APIs: {args.api}")
        print(f"Keywords: {args.keywords}")
        print(f"Location: {args.location}")
        print("=" * 60)
        
        # Sample
        if all_jobs:
            print("\n📋 Sample Jobs:")
            for job in all_jobs[:5]:
                print(f"\n  - {job.get('title')} at {job.get('company')}")
                print(f"    Location: {job.get('location')}")
                print(f"    Source: {job.get('source')}")
                print(f"    URL: {job.get('url')[:60]}...")
        else:
            print("\n⚠️  No jobs found. Try different keywords or check API credentials.")
            print("\n💡 Setup tips:")
            print("   - Adzuna: Get free API key at https://developer.adzuna.com/")
            print("   - The Muse: No setup needed!")
            print("   - Remote OK: No setup needed!")


if __name__ == "__main__":
    main()

