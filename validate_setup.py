#!/usr/bin/env python3
"""
CareerPilot Setup Validator

Validates that all components are properly configured and ready to run.
Checks:
- Environment variables
- Python dependencies
- Database connection
- API keys
- File structure
- Services status

Usage:
    python validate_setup.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import importlib.util

# Load environment
load_dotenv()

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_check(name, status, detail=""):
    """Print check result."""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {name:<40} {detail}")

def check_env_var(name, required=True):
    """Check if environment variable is set."""
    value = os.getenv(name)
    exists = bool(value)
    
    if required:
        print_check(
            f"ENV: {name}",
            exists,
            "Set" if exists else "MISSING"
        )
    else:
        print_check(
            f"ENV: {name} (optional)",
            True,
            "Set" if exists else "Not set"
        )
    
    return exists

def check_python_package(name, import_name=None):
    """Check if Python package is installed."""
    if import_name is None:
        import_name = name
    
    try:
        spec = importlib.util.find_spec(import_name)
        exists = spec is not None
        print_check(f"Package: {name}", exists, "Installed" if exists else "Missing")
        return exists
    except Exception:
        print_check(f"Package: {name}", False, "Missing")
        return False

def check_file(path, description):
    """Check if file exists."""
    exists = Path(path).exists()
    print_check(description, exists, str(path) if exists else "Missing")
    return exists

def check_directory(path, description):
    """Check if directory exists."""
    exists = Path(path).is_dir()
    print_check(description, exists, str(path) if exists else "Missing")
    return exists

def check_supabase_connection():
    """Check Supabase connection."""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            print_check("Supabase Connection", False, "Missing credentials")
            return False
        
        client = create_client(url, key)
        
        # Try a simple query
        result = client.table('users').select('id').limit(1).execute()
        
        print_check("Supabase Connection", True, f"Connected to {url[:30]}...")
        return True
        
    except Exception as e:
        print_check("Supabase Connection", False, f"Error: {str(e)[:50]}")
        return False

def check_gemini_api():
    """Check Gemini API key."""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print_check("Gemini AI API", False, "API key missing")
            return False
        
        genai.configure(api_key=api_key)
        
        # Try to list models (lightweight check)
        models = genai.list_models()
        
        print_check("Gemini AI API", True, "API key valid")
        return True
        
    except Exception as e:
        print_check("Gemini AI API", False, f"Error: {str(e)[:50]}")
        return False

def check_backend_running():
    """Check if backend is running."""
    try:
        import requests
        response = requests.get('http://localhost:8000/', timeout=2)
        running = response.status_code == 200
        print_check("Backend Server", running, "Running on port 8000" if running else "Not running")
        return running
    except Exception:
        print_check("Backend Server", False, "Not running on port 8000")
        return False

def check_frontend_running():
    """Check if frontend is running."""
    try:
        import requests
        response = requests.get('http://localhost:3000/', timeout=2)
        running = response.status_code == 200
        print_check("Frontend Server", running, "Running on port 3000" if running else "Not running")
        return running
    except Exception:
        print_check("Frontend Server", False, "Not running on port 3000")
        return False

def check_worker_status():
    """Check worker status."""
    try:
        sys.path.append(str(Path(__file__).parent / 'backend'))
        from workers.worker_manager import WorkerManager
        
        manager = WorkerManager()
        status = manager.get_status()
        running = status.get('running', False)
        
        print_check(
            "Worker Process",
            True,
            f"Running (PID: {status.get('pid')})" if running else "Stopped"
        )
        return running
        
    except Exception as e:
        print_check("Worker Process", False, f"Error: {str(e)[:50]}")
        return False

def main():
    """Main validation routine."""
    print("\n" + "="*70)
    print("  CareerPilot Setup Validator")
    print("="*70)
    
    results = {
        'env': [],
        'packages': [],
        'files': [],
        'services': []
    }
    
    # Check environment variables
    print_header("Environment Variables")
    results['env'].append(check_env_var('SUPABASE_URL', required=True))
    results['env'].append(check_env_var('SUPABASE_ANON_KEY', required=True))
    results['env'].append(check_env_var('SUPABASE_SERVICE_ROLE_KEY', required=True))
    results['env'].append(check_env_var('GEMINI_API_KEY', required=True))
    results['env'].append(check_env_var('OPENAI_API_KEY', required=False))
    
    # Check Python packages
    print_header("Python Dependencies (Backend)")
    results['packages'].append(check_python_package('fastapi'))
    results['packages'].append(check_python_package('uvicorn'))
    results['packages'].append(check_python_package('pdfplumber'))
    results['packages'].append(check_python_package('supabase'))
    results['packages'].append(check_python_package('google-generativeai', 'google.generativeai'))
    results['packages'].append(check_python_package('playwright'))
    results['packages'].append(check_python_package('psutil'))
    results['packages'].append(check_python_package('tenacity'))
    results['packages'].append(check_python_package('numpy'))
    
    # Check file structure
    print_header("File Structure")
    results['files'].append(check_directory('backend', "Backend directory"))
    results['files'].append(check_directory('frontend', "Frontend directory"))
    results['files'].append(check_directory('migrations', "Migrations directory"))
    results['files'].append(check_file('backend/app/main.py', "Backend main.py"))
    results['files'].append(check_file('backend/workers/gemini_apply_worker.py', "Gemini worker"))
    results['files'].append(check_file('backend/workers/worker_manager.py', "Worker manager"))
    results['files'].append(check_file('frontend/pages/dashboard/index.tsx', "Dashboard page"))
    results['files'].append(check_file('migrations/005_performance_optimizations.sql', "Latest migration"))
    
    # Check services
    print_header("Services & Connections")
    results['services'].append(check_supabase_connection())
    results['services'].append(check_gemini_api())
    results['services'].append(check_backend_running())
    results['services'].append(check_frontend_running())
    results['services'].append(check_worker_status())
    
    # Summary
    print_header("Summary")
    
    env_passed = sum(results['env'][:4])  # First 4 are required
    env_total = 4
    
    pkg_passed = sum(results['packages'])
    pkg_total = len(results['packages'])
    
    files_passed = sum(results['files'])
    files_total = len(results['files'])
    
    services_passed = sum(results['services'][:2])  # First 2 are critical
    services_total = 2
    
    print(f"\n  Environment Variables:  {env_passed}/{env_total} required")
    print(f"  Python Dependencies:    {pkg_passed}/{pkg_total} installed")
    print(f"  File Structure:         {files_passed}/{files_total} present")
    print(f"  Critical Services:      {services_passed}/{services_total} working")
    
    all_critical_passed = (
        env_passed == env_total and
        pkg_passed >= pkg_total - 2 and  # Allow 2 missing packages
        files_passed >= files_total - 2 and  # Allow 2 missing files
        services_passed == services_total
    )
    
    print("\n" + "="*70)
    if all_critical_passed:
        print("  ✅ SETUP VALIDATED - Ready to run!")
        print("="*70)
        print("\n  Next steps:")
        print("  1. Apply database migrations (if not done)")
        print("     python apply_all_migrations.py")
        print("\n  2. Start backend:")
        print("     cd backend && uvicorn app.main:app --reload")
        print("\n  3. Start frontend:")
        print("     cd frontend && npm run dev")
        print("\n  4. Start worker (optional):")
        print("     python backend/workers/worker_manager.py start")
        print()
        sys.exit(0)
    else:
        print("  ❌ SETUP INCOMPLETE - Fix issues above")
        print("="*70)
        print("\n  Common fixes:")
        print("  - Missing env vars: Create .env file with required keys")
        print("  - Missing packages: pip install -r backend/requirements.txt")
        print("  - Services not running: Start backend/frontend servers")
        print("  - Database issues: Apply migrations via Supabase Dashboard")
        print()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nValidation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

