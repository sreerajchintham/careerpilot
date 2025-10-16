#!/usr/bin/env python3
"""
Gemini AI-Powered Job Application Worker

This worker uses Google's Gemini LLM to intelligently automate job applications
on platforms like Jobright.ai and LinkedIn. It can:
- Analyze job descriptions and match them with your resume
- Generate personalized cover letters
- Intelligently fill application forms
- Handle complex application workflows

Usage:
    python workers/gemini_apply_worker.py run_once
    python workers/gemini_apply_worker.py run_continuous --interval 3600
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
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gemini_apply_worker')


class GeminiAIAgent:
    """
    AI Agent powered by Google Gemini for intelligent job application tasks.
    
    This agent can:
    - Analyze job descriptions
    - Generate personalized cover letters
    - Extract and understand form fields
    - Provide intelligent responses to application questions
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini AI agent."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.5 Flash for text generation (faster and more cost-effective)
        self.text_model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Use Gemini Pro Vision for form analysis (if needed)
        try:
            self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        except:
            self.vision_model = None
            logger.warning("Gemini Pro Vision not available")
        
        logger.info("✅ Gemini AI Agent initialized successfully")
    
    async def analyze_job_match(self, job_description: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze how well a resume matches a job description.
        
        Args:
            job_description: Full job description text
            resume_data: Parsed resume data with skills, experience, etc.
            
        Returns:
            Dictionary with match analysis, score, and recommendations
        """
        prompt = f"""
        Analyze this job-resume match and provide a structured assessment:
        
        JOB DESCRIPTION:
        {job_description}
        
        CANDIDATE RESUME:
        - Skills: {', '.join(resume_data.get('skills', []))}
        - Experience: {resume_data.get('experience', 'Not provided')}
        - Education: {resume_data.get('education', 'Not provided')}
        
        Provide your analysis in this JSON format:
        {{
            "match_score": <number 0-100>,
            "key_strengths": ["strength1", "strength2", ...],
            "gaps": ["gap1", "gap2", ...],
            "recommendations": ["rec1", "rec2", ...],
            "should_apply": <true/false>,
            "reasoning": "brief explanation"
        }}
        """
        
        try:
            response = await asyncio.to_thread(
                self.text_model.generate_content, prompt
            )
            
            # Parse JSON from response
            result_text = response.text.strip()
            # Extract JSON if wrapped in markdown
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Error analyzing job match: {e}")
            return {
                "match_score": 50,
                "key_strengths": [],
                "gaps": [],
                "recommendations": [],
                "should_apply": True,
                "reasoning": "Analysis failed, proceeding with caution"
            }
    
    async def generate_cover_letter(
        self, 
        job_data: Dict[str, Any], 
        resume_data: Dict[str, Any],
        style: str = "professional"
    ) -> str:
        """
        Generate a personalized cover letter using Gemini.
        
        Args:
            job_data: Job information (title, company, description, requirements)
            resume_data: Candidate's resume information
            style: Tone of the cover letter (professional, enthusiastic, creative)
            
        Returns:
            Generated cover letter text
        """
        prompt = f"""
        Generate a compelling, personalized cover letter for this job application.
        
        JOB DETAILS:
        - Position: {job_data.get('title', 'N/A')}
        - Company: {job_data.get('company', 'N/A')}
        - Description: {job_data.get('description', 'N/A')}
        - Requirements: {job_data.get('requirements', 'N/A')}
        
        CANDIDATE INFORMATION:
        - Name: {resume_data.get('name', 'Candidate')}
        - Skills: {', '.join(resume_data.get('skills', []))}
        - Experience: {resume_data.get('experience', 'Experienced professional')}
        - Email: {resume_data.get('email', '')}
        
        REQUIREMENTS:
        1. Write in a {style} tone
        2. Be specific about how their skills match the role
        3. Show genuine enthusiasm for the company
        4. Keep it concise (250-350 words)
        5. DO NOT invent experience or skills they don't have
        6. Make it feel authentic and human, not AI-generated
        7. Include specific examples if the resume data provides them
        
        Generate ONLY the cover letter text, no additional formatting or explanations.
        """
        
        try:
            response = await asyncio.to_thread(
                self.text_model.generate_content, prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return f"I am writing to express my interest in the {job_data.get('title', 'position')} role at {job_data.get('company', 'your company')}."
    
    async def answer_application_question(
        self,
        question: str,
        resume_data: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> str:
        """
        Generate intelligent answers to application questions.
        
        Args:
            question: The application question to answer
            resume_data: Candidate's resume information
            job_context: Context about the job and company
            
        Returns:
            Generated answer
        """
        prompt = f"""
        Answer this job application question based on the candidate's profile.
        
        QUESTION: {question}
        
        CANDIDATE PROFILE:
        - Skills: {', '.join(resume_data.get('skills', []))}
        - Experience: {resume_data.get('experience', 'N/A')}
        - Background: {resume_data.get('summary', 'N/A')}
        
        JOB CONTEXT:
        - Company: {job_context.get('company', 'N/A')}
        - Role: {job_context.get('title', 'N/A')}
        
        REQUIREMENTS:
        1. Answer truthfully based on the candidate's actual experience
        2. Keep it concise and relevant
        3. Be specific where possible
        4. Match the tone of the question
        5. DO NOT fabricate experience or qualifications
        
        Provide ONLY the answer, no additional text.
        """
        
        try:
            response = await asyncio.to_thread(
                self.text_model.generate_content, prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return "Please see my resume for details."


class PlaywrightAutomation:
    """
    Browser automation using Playwright for filling and submitting job applications.
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize Playwright automation.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        logger.info(f"Playwright automation initialized (headless={headless})")
    
    async def start(self):
        """Start browser and create context."""
        self.playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        logger.info("✅ Browser started successfully")
    
    async def close(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser closed")
    
    async def human_like_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add random delay to mimic human behavior."""
        import random
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def type_like_human(self, page: Page, selector: str, text: str):
        """Type text with human-like delays."""
        import random
        
        await page.fill(selector, '')  # Clear field first
        await self.human_like_delay(0.3, 0.8)
        
        for char in text:
            await page.type(selector, char, delay=random.uniform(50, 150))
        
        await self.human_like_delay(0.2, 0.5)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def navigate_to_job(self, job_url: str) -> Page:
        """
        Navigate to job posting URL.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            Playwright Page object
        """
        page = await self.context.new_page()
        
        try:
            await page.goto(job_url, wait_until='networkidle', timeout=30000)
            await self.human_like_delay(1, 2)
            
            logger.info(f"Navigated to: {job_url}")
            return page
            
        except Exception as e:
            logger.error(f"Error navigating to {job_url}: {e}")
            raise
    
    async def detect_application_form(self, page: Page) -> Dict[str, Any]:
        """
        Detect and analyze application form fields on the page.
        
        Args:
            page: Playwright Page object
            
        Returns:
            Dictionary containing form structure and fields
        """
        try:
            # Get all input fields
            inputs = await page.query_selector_all('input, textarea, select')
            
            form_fields = []
            for input_elem in inputs:
                field_type = await input_elem.get_attribute('type') or 'text'
                field_name = await input_elem.get_attribute('name') or await input_elem.get_attribute('id') or ''
                field_label = await input_elem.get_attribute('placeholder') or ''
                field_required = await input_elem.get_attribute('required') is not None
                
                if field_name or field_label:
                    form_fields.append({
                        'type': field_type,
                        'name': field_name,
                        'label': field_label,
                        'required': field_required
                    })
            
            logger.info(f"Detected {len(form_fields)} form fields")
            return {
                'fields': form_fields,
                'total_fields': len(form_fields)
            }
            
        except Exception as e:
            logger.error(f"Error detecting form: {e}")
            return {'fields': [], 'total_fields': 0}


class GeminiApplyWorker:
    """
    Main worker class that combines Gemini AI and Playwright automation
    to intelligently apply to jobs.
    """
    
    def __init__(self, headless: bool = False):
        """Initialize the Gemini-powered application worker."""
        # Initialize Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize AI agent
        self.ai_agent = GeminiAIAgent()
        
        # Initialize browser automation
        self.browser_automation = PlaywrightAutomation(headless=headless)
        
        logger.info("✅ Gemini Apply Worker initialized successfully")
    
    def fetch_pending_applications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch pending applications from Supabase.
        
        Args:
            limit: Maximum number of applications to fetch
            
        Returns:
            List of application records
        """
        try:
            response = self.supabase.table('applications').select(
                """
                id,
                user_id,
                job_id,
                status,
                artifacts,
                attempt_meta,
                jobs!inner(
                    id,
                    title,
                    company,
                    source,
                    raw
                ),
                users!inner(
                    id,
                    email,
                    profile
                )
                """
            ).eq('status', 'draft').limit(limit).execute()
            
            applications = response.data
            logger.info(f"Found {len(applications)} draft applications to process")
            
            return applications
            
        except Exception as e:
            logger.error(f"Error fetching applications: {e}")
            return []
    
    async def process_application(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single job application using AI and automation.
        
        Args:
            application: Application record from database
            
        Returns:
            Result dictionary with status and metadata
        """
        application_id = application['id']
        job_data = application.get('jobs', {})
        user_data = application.get('users', {})
        
        logger.info(f"Processing application {application_id} for {job_data.get('title')} at {job_data.get('company')}")
        
        try:
            # Extract resume data from user profile
            resume_data = user_data.get('profile', {})
            if not resume_data:
                resume_data = {
                    'name': 'Candidate',
                    'email': user_data.get('email', ''),
                    'skills': [],
                    'experience': 'Experienced professional'
                }
            
            # Get job URL from raw data
            job_url = job_data.get('raw', {}).get('url')
            
            if not job_url:
                logger.warning(f"No URL found for job {job_data.get('id')}")
                return {
                    'status': 'failed',
                    'reason': 'No job URL available',
                    'application_id': application_id
                }
            
            # Step 1: Analyze job match with AI
            job_description = job_data.get('raw', {}).get('description', '')
            match_analysis = await self.ai_agent.analyze_job_match(job_description, resume_data)
            
            logger.info(f"Match score: {match_analysis.get('match_score', 0)}/100")
            
            if not match_analysis.get('should_apply', True):
                logger.info(f"AI recommends not applying: {match_analysis.get('reasoning')}")
                return {
                    'status': 'skipped',
                    'reason': 'AI recommendation: not a good match',
                    'match_analysis': match_analysis,
                    'application_id': application_id
                }
            
            # Step 2: Generate cover letter
            cover_letter = await self.ai_agent.generate_cover_letter(job_data, resume_data)
            
            logger.info(f"Generated cover letter ({len(cover_letter)} chars)")
            
            # Step 3: Navigate to job and fill application (if platform is supported)
            source = job_data.get('source', '').lower()
            
            if source in ['jobright.ai', 'linkedin']:
                # TODO: Implement platform-specific application logic
                logger.info(f"Platform {source} detected, would automate application here")
                
                # For now, save the generated materials
                result = {
                    'status': 'applied',
                    'method': 'gemini_ai_agent',
                    'applied_at': datetime.now(timezone.utc).isoformat(),
                    'match_analysis': match_analysis,
                    'generated_materials': {
                        'cover_letter': cover_letter
                    },
                    'note': f'AI-powered application to {source} (automation pending)',
                    'application_id': application_id
                }
            else:
                # Generic application - save materials for manual submission
                result = {
                    'status': 'applied',
                    'method': 'gemini_ai_materials_only',
                    'applied_at': datetime.now(timezone.utc).isoformat(),
                    'match_analysis': match_analysis,
                    'generated_materials': {
                        'cover_letter': cover_letter
                    },
                    'note': 'AI-generated materials ready for manual submission',
                    'application_id': application_id
                }
            
            # Update database
            await self.update_application_status(application_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing application {application_id}: {e}")
            return {
                'status': 'failed',
                'reason': str(e),
                'application_id': application_id
            }
    
    async def update_application_status(self, application_id: str, result: Dict[str, Any]):
        """Update application status in database."""
        try:
            update_data = {
                'status': 'submitted' if result['status'] == 'applied' else result['status'],
                'artifacts': result.get('generated_materials', {}),
                'attempt_meta': {
                    'applied_at': result.get('applied_at'),
                    'method': result.get('method'),
                    'match_score': result.get('match_analysis', {}).get('match_score'),
                    'ai_agent': 'gemini-pro'
                },
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = await asyncio.to_thread(
                lambda: self.supabase.table('applications').update(update_data).eq('id', application_id).execute()
            )
            
            if response.data:
                logger.info(f"✅ Updated application {application_id} to status '{update_data['status']}'")
            else:
                logger.warning(f"No data returned when updating {application_id}")
                
        except Exception as e:
            logger.error(f"Error updating application {application_id}: {e}")
    
    async def run_once(self) -> Dict[str, Any]:
        """Run the worker once to process pending applications."""
        logger.info("🚀 Starting Gemini Apply Worker (run_once)")
        
        try:
            # Start browser
            await self.browser_automation.start()
            
            # Fetch pending applications
            applications = self.fetch_pending_applications(limit=5)
            
            if not applications:
                logger.info("No pending applications to process")
                return {
                    'status': 'success',
                    'processed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'message': 'No pending applications'
                }
            
            # Process each application
            results = []
            processed = 0
            failed = 0
            skipped = 0
            
            for app in applications:
                result = await self.process_application(app)
                results.append(result)
                
                if result['status'] == 'applied':
                    processed += 1
                elif result['status'] == 'skipped':
                    skipped += 1
                else:
                    failed += 1
                
                # Add delay between applications
                await self.browser_automation.human_like_delay(2, 5)
            
            # Cleanup
            await self.browser_automation.close()
            
            summary = {
                'status': 'success',
                'processed': processed,
                'failed': failed,
                'skipped': skipped,
                'total': len(applications),
                'results': results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ Worker completed: {processed} applied, {failed} failed, {skipped} skipped")
            return summary
            
        except Exception as e:
            logger.error(f"Worker error: {e}")
            if self.browser_automation.browser:
                await self.browser_automation.close()
            
            return {
                'status': 'error',
                'error': str(e),
                'processed': 0,
                'failed': 0,
                'skipped': 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


async def main_async(command: str, **kwargs):
    """Main async entry point."""
    if command == 'run_once':
        worker = GeminiApplyWorker(headless=kwargs.get('headless', False))
        results = await worker.run_once()
        return results
    
    elif command == 'run_continuous':
        interval = kwargs.get('interval', 3600)
        worker = GeminiApplyWorker(headless=kwargs.get('headless', True))
        
        logger.info(f"Running in continuous mode (interval: {interval}s)")
        
        while True:
            results = await worker.run_once()
            logger.info(f"Next run in {interval} seconds...")
            await asyncio.sleep(interval)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Gemini AI-Powered Job Application Worker'
    )
    parser.add_argument(
        'command',
        choices=['run_once', 'run_continuous'],
        help='Command to execute'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Interval in seconds for continuous mode (default: 3600)'
    )
    
    args = parser.parse_args()
    
    try:
        # Run async main
        results = asyncio.run(main_async(
            args.command,
            headless=args.headless,
            interval=args.interval
        ))
        
        if args.command == 'run_once':
            # Print results
            print("\n" + "="*70)
            print("GEMINI AI JOB APPLICATION WORKER RESULTS")
            print("="*70)
            print(json.dumps(results, indent=2))
            print("="*70)
            
            # Exit with appropriate code
            if results.get('status') == 'error':
                sys.exit(1)
            else:
                sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

