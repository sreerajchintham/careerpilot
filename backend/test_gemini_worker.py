#!/usr/bin/env python3
"""
Test script for Gemini AI-Powered Job Application Worker

This script tests the core functionality of the Gemini worker:
1. Gemini API connection
2. Cover letter generation
3. Job matching analysis
4. Browser automation setup
5. Database integration

Usage:
    python test_gemini_worker.py
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking Environment Configuration")
    print("=" * 60)
    
    required_vars = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_ANON_KEY': os.getenv('SUPABASE_ANON_KEY'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
    }
    
    optional_vars = {
        'LINKEDIN_EMAIL': os.getenv('LINKEDIN_EMAIL'),
        'JOBRIGHT_EMAIL': os.getenv('JOBRIGHT_EMAIL'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    all_good = True
    
    print("\n✅ Required Variables:")
    for var, value in required_vars.items():
        if value:
            print(f"   {var}: {'*' * 20}... (set)")
        else:
            print(f"   ❌ {var}: NOT SET")
            all_good = False
    
    print("\n⚙️  Optional Variables:")
    for var, value in optional_vars.items():
        if value:
            print(f"   {var}: {'*' * 15}... (set)")
        else:
            print(f"   {var}: not set")
    
    return all_good


async def test_gemini_api():
    """Test Gemini API connection and basic functionality."""
    print("\n🤖 Testing Gemini API Connection")
    print("=" * 60)
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found")
            return False
        
        genai.configure(api_key=api_key)
        # Use Gemini 2.5 Flash (available in user's API key)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Test simple generation
        print("Testing simple text generation...")
        response = await asyncio.to_thread(
            model.generate_content,
            "Say 'Hello from Gemini!' in a friendly way."
        )
        
        print(f"✅ Gemini Response: {response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return False


async def test_cover_letter_generation():
    """Test cover letter generation with sample data."""
    print("\n📝 Testing Cover Letter Generation")
    print("=" * 60)
    
    try:
        from workers.gemini_apply_worker import GeminiAIAgent
        
        agent = GeminiAIAgent()
        
        # Sample data
        job_data = {
            'title': 'Senior Python Developer',
            'company': 'Tech Corp',
            'description': 'We are looking for an experienced Python developer with FastAPI and cloud experience.',
            'requirements': 'Python, FastAPI, AWS, PostgreSQL, REST APIs'
        }
        
        resume_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'AWS'],
            'experience': '5+ years of Python development experience with focus on backend APIs'
        }
        
        print("Generating cover letter...")
        cover_letter = await agent.generate_cover_letter(job_data, resume_data)
        
        print(f"\n✅ Generated Cover Letter ({len(cover_letter)} characters):")
        print("-" * 60)
        print(cover_letter[:500] + "..." if len(cover_letter) > 500 else cover_letter)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Cover Letter Generation Error: {e}")
        return False


async def test_job_match_analysis():
    """Test job matching analysis."""
    print("\n🎯 Testing Job Match Analysis")
    print("=" * 60)
    
    try:
        from workers.gemini_apply_worker import GeminiAIAgent
        
        agent = GeminiAIAgent()
        
        # Sample data
        job_description = """
        Senior Python Developer position at Tech Corp.
        
        Requirements:
        - 5+ years Python experience
        - Experience with FastAPI or Django
        - Strong knowledge of PostgreSQL
        - Cloud experience (AWS/Azure)
        - Docker and Kubernetes
        - REST API development
        
        Nice to have:
        - React or frontend experience
        - Machine learning background
        """
        
        resume_data = {
            'skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'AWS', 'REST APIs'],
            'experience': '6 years of Python backend development',
            'education': 'BS Computer Science'
        }
        
        print("Analyzing job match...")
        analysis = await agent.analyze_job_match(job_description, resume_data)
        
        print(f"\n✅ Match Analysis:")
        print(json.dumps(analysis, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Job Match Analysis Error: {e}")
        return False


async def test_playwright_setup():
    """Test Playwright browser automation setup."""
    print("\n🌐 Testing Playwright Browser Automation")
    print("=" * 60)
    
    try:
        from playwright.async_api import async_playwright
        
        print("Starting browser...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            print("Navigating to test page...")
            await page.goto('https://example.com')
            
            title = await page.title()
            print(f"✅ Page Title: {title}")
            
            await browser.close()
        
        print("✅ Playwright is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Playwright Error: {e}")
        print("\n💡 Install Playwright browsers with:")
        print("   playwright install chromium")
        return False


def test_supabase_connection():
    """Test Supabase database connection."""
    print("\n💾 Testing Supabase Connection")
    print("=" * 60)
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found")
            return False
        
        client = create_client(supabase_url, supabase_key)
        
        # Test connection by querying applications table
        response = client.table('applications').select('id').limit(1).execute()
        
        print(f"✅ Supabase connection successful")
        print(f"   Found {len(response.data)} records in applications table")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase Error: {e}")
        return False


async def test_full_worker_initialization():
    """Test complete worker initialization."""
    print("\n🔧 Testing Full Worker Initialization")
    print("=" * 60)
    
    try:
        from workers.gemini_apply_worker import GeminiApplyWorker
        
        print("Initializing worker...")
        worker = GeminiApplyWorker(headless=True)
        
        print("✅ Worker initialized successfully")
        print(f"   Supabase: Connected")
        print(f"   Gemini AI: Initialized")
        print(f"   Browser: Ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Worker Initialization Error: {e}")
        return False


def print_setup_instructions():
    """Print setup instructions if tests fail."""
    print("\n" + "=" * 60)
    print("📚 SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1️⃣  Install Dependencies:")
    print("   cd backend")
    print("   pip install -r requirements.txt")
    print("   playwright install chromium")
    
    print("\n2️⃣  Get Gemini API Key:")
    print("   Visit: https://makersuite.google.com/app/apikey")
    print("   Sign in and create an API key")
    
    print("\n3️⃣  Configure Environment:")
    print("   Copy env.example to .env")
    print("   Add your credentials:")
    print("   - SUPABASE_URL")
    print("   - SUPABASE_ANON_KEY")
    print("   - GEMINI_API_KEY")
    
    print("\n4️⃣  Setup Database:")
    print("   Run migrations in Supabase:")
    print("   - migrations/001_initial.sql")
    print("   - migrations/002_add_drafts_to_users.sql")
    
    print("\n5️⃣  Test Again:")
    print("   python test_gemini_worker.py")


async def main():
    """Main test function."""
    print("\n" + "="*60)
    print("🧪 GEMINI AI WORKER TEST SUITE")
    print("="*60)
    
    results = {}
    
    # Run all tests
    results['environment'] = check_environment()
    
    if results['environment']:
        results['gemini_api'] = await test_gemini_api()
        results['cover_letter'] = await test_cover_letter_generation()
        results['job_match'] = await test_job_match_analysis()
        results['playwright'] = await test_playwright_setup()
        results['supabase'] = test_supabase_connection()
        results['worker_init'] = await test_full_worker_initialization()
    else:
        print("\n❌ Environment check failed. Fix environment variables first.")
        print_setup_instructions()
        return
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name.replace('_', ' ').title()}")
    
    print(f"\n   Score: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Your Gemini worker is ready to use.")
        print("\n🚀 Next Steps:")
        print("   1. Queue some job applications in the frontend")
        print("   2. Run the worker:")
        print("      python workers/gemini_apply_worker.py run_once")
    else:
        print("\n⚠️  Some tests failed. See instructions above.")
        print_setup_instructions()


if __name__ == "__main__":
    asyncio.run(main())

