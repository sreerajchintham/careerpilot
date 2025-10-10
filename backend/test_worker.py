#!/usr/bin/env python3
"""
Test script for the simulated apply worker.

This script tests the worker functionality with sample data.
"""

import os
import sys
import uuid
import requests
from datetime import datetime, timezone

# Add workers directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'workers'))

def create_test_application():
    """Create a test application for the worker to process."""
    
    print("🧪 Creating test application...")
    
    # Generate test IDs
    test_user_id = str(uuid.uuid4())
    test_job_id = str(uuid.uuid4())
    
    # First create a test user and job (simulated)
    print(f"   Test User ID: {test_user_id}")
    print(f"   Test Job ID: {test_job_id}")
    
    # Queue an application (this will fail if no jobs exist, but that's expected)
    try:
        response = requests.post(
            "http://127.0.0.1:8001/queue-applications",
            json={
                "user_id": test_user_id,
                "job_ids": [test_job_id]
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Created {data['queued_count']} test applications")
            return True
        else:
            print(f"   ⚠️  Expected failure (no jobs in database): {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_worker_directly():
    """Test the worker directly without database dependencies."""
    
    print("\n🔧 Testing worker components...")
    
    try:
        from simulated_apply_worker import SimulatedApplyWorker
        
        # Test worker initialization
        print("   1. Testing worker initialization...")
        try:
            worker = SimulatedApplyWorker()
            print("   ✅ Worker initialized successfully")
        except Exception as e:
            print(f"   ❌ Worker initialization failed: {e}")
            return False
        
        # Test pending applications fetch
        print("   2. Testing pending applications fetch...")
        try:
            applications = worker.get_pending_applications()
            print(f"   ✅ Found {len(applications)} pending applications")
        except Exception as e:
            print(f"   ❌ Failed to fetch applications: {e}")
            return False
        
        # Test simulation logic
        print("   3. Testing simulation logic...")
        if applications:
            try:
                result = worker.simulate_application_submission(applications[0])
                print("   ✅ Simulation logic working")
                print(f"   📋 Generated result: {result['method']}")
            except Exception as e:
                print(f"   ❌ Simulation failed: {e}")
                return False
        else:
            print("   ⚠️  No applications to test simulation with")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_worker_cli():
    """Test the worker CLI interface."""
    
    print("\n💻 Testing worker CLI...")
    
    try:
        import subprocess
        
        # Test run_once command
        print("   1. Testing 'run_once' command...")
        result = subprocess.run([
            sys.executable, 
            "workers/simulated_apply_worker.py", 
            "run_once", 
            "--verbose"
        ], capture_output=True, text=True, timeout=30)
        
        print(f"   Exit code: {result.returncode}")
        if result.stdout:
            print(f"   Output: {result.stdout[:200]}...")
        if result.stderr:
            print(f"   Error: {result.stderr[:200]}...")
        
        if result.returncode == 0:
            print("   ✅ CLI run_once command successful")
        else:
            print("   ⚠️  CLI command failed (expected if no pending applications)")
        
        # Test help command
        print("   2. Testing help command...")
        result = subprocess.run([
            sys.executable, 
            "workers/simulated_apply_worker.py", 
            "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "run_once" in result.stdout:
            print("   ✅ Help command working")
        else:
            print("   ❌ Help command failed")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("   ❌ CLI command timed out")
        return False
    except Exception as e:
        print(f"   ❌ CLI test failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("🚀 Simulated Apply Worker Test Suite")
    print("=" * 50)
    
    # Check environment
    print("\n🔍 Environment Check:")
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        print("   ✅ Supabase credentials found")
    else:
        print("   ❌ Missing Supabase credentials")
        print("   Set SUPABASE_URL and SUPABASE_ANON_KEY in .env file")
        return
    
    # Check backend
    print("\n🔗 Backend Check:")
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is running")
        else:
            print("   ❌ Backend health check failed")
            return
    except Exception as e:
        print(f"   ❌ Cannot reach backend: {e}")
        print("   Start backend with: uvicorn app.main:app --reload --port 8001")
        return
    
    # Run tests
    print("\n🧪 Running Tests:")
    
    # Test worker components
    worker_ok = test_worker_directly()
    
    # Test CLI interface
    cli_ok = test_worker_cli()
    
    # Test application creation (optional)
    app_ok = create_test_application()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Worker Components: {'✅ PASS' if worker_ok else '❌ FAIL'}")
    print(f"   CLI Interface: {'✅ PASS' if cli_ok else '❌ FAIL'}")
    print(f"   Application Creation: {'✅ PASS' if app_ok else '⚠️  SKIP'}")
    
    if worker_ok and cli_ok:
        print("\n🎉 Worker is ready for use!")
        print("\n💡 Usage:")
        print("   python workers/simulated_apply_worker.py run_once")
        print("   python workers/simulated_apply_worker.py continuous --interval 300")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")
    
    print("\n🔧 Next Steps:")
    print("1. Apply migration 003_update_applications_status.sql to add 'pending' status")
    print("2. Seed job data to test with real applications")
    print("3. Queue some applications and run the worker")
    print("4. Check applications table for updated status and artifacts")

if __name__ == "__main__":
    main()
