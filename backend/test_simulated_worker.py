#!/usr/bin/env python3
"""
Test script for the Simulated Application Worker

This script tests the worker functionality by:
1. Creating test applications with "pending" status
2. Running the worker to process them
3. Verifying the results
"""

import os
import sys
import uuid
import json
from datetime import datetime, timezone

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_test_data():
    """Create test applications with pending status."""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Check if we have jobs to work with
        jobs_response = supabase.table('jobs').select('id, title, company').limit(1).execute()
        
        if not jobs_response.data:
            print("❌ No jobs found in database. Please seed jobs first.")
            return False
        
        job = jobs_response.data[0]
        print(f"✅ Found test job: {job['title']} at {job['company']}")
        
        # Create test user if it doesn't exist
        test_user_id = str(uuid.uuid4())
        test_user_email = f"test-worker-{test_user_id[:8]}@example.com"
        
        try:
            user_response = supabase.table('users').insert({
                'id': test_user_id,
                'email': test_user_email,
                'name': 'Test Worker User',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            print(f"✅ Created test user: {test_user_email}")
            
        except Exception as e:
            print(f"⚠️  User might already exist: {e}")
        
        # Create test applications with pending status
        test_applications = []
        
        for i in range(3):  # Create 3 test applications
            application_id = str(uuid.uuid4())
            
            application_data = {
                'id': application_id,
                'user_id': test_user_id,
                'job_id': job['id'],
                'status': 'pending',  # This is what the worker will process
                'artifacts': {
                    'resume_text': f'Test resume content for application {i+1}',
                    'cover_letter': f'Test cover letter for application {i+1}'
                },
                'attempt_meta': {
                    'queued_at': 'now()',
                    'queued_by': 'test_script',
                    'source': 'worker_test',
                    'test_run': True
                },
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            test_applications.append(application_data)
        
        # Insert test applications
        insert_response = supabase.table('applications').insert(test_applications).execute()
        
        if insert_response.data:
            print(f"✅ Created {len(insert_response.data)} test applications with pending status")
            print(f"   Application IDs: {[app['id'] for app in insert_response.data]}")
            return True
        else:
            print("❌ Failed to create test applications")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        return False

def test_worker():
    """Test the simulated application worker."""
    
    print("\n🧪 Testing Simulated Application Worker")
    print("=" * 50)
    
    try:
        # Import and run the worker
        from workers.simulated_apply_worker import SimulatedApplyWorker
        
        # Initialize worker
        worker = SimulatedApplyWorker()
        print("✅ Worker initialized successfully")
        
        # Run worker once
        results = worker.run_once()
        
        print("\n📊 Worker Results:")
        print(json.dumps(results, indent=2))
        
        # Verify results
        if results['status'] == 'success':
            print(f"\n✅ Worker completed successfully!")
            print(f"   Processed: {results['processed']} applications")
            print(f"   Failed: {results['failed']} applications")
            return True
        elif results['status'] == 'partial_success':
            print(f"\n⚠️  Worker completed with partial success")
            print(f"   Processed: {results['processed']} applications")
            print(f"   Failed: {results['failed']} applications")
            return True
        else:
            print(f"\n❌ Worker failed: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing worker: {e}")
        return False

def verify_results():
    """Verify that applications were updated correctly."""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Check for applications with status "applied"
        applied_response = supabase.table('applications').select(
            'id, status, artifacts, attempt_meta, updated_at'
        ).eq('status', 'applied').execute()
        
        if applied_response.data:
            print(f"\n✅ Found {len(applied_response.data)} applications with 'applied' status")
            
            for app in applied_response.data[:2]:  # Show first 2 as examples
                print(f"\n📄 Application {app['id'][:8]}...")
                print(f"   Status: {app['status']}")
                print(f"   Updated: {app['updated_at']}")
                
                artifacts = app.get('artifacts', {})
                if 'method' in artifacts:
                    print(f"   Method: {artifacts['method']}")
                    print(f"   Note: {artifacts['note']}")
                
                attempt_meta = app.get('attempt_meta', {})
                if 'application_method' in attempt_meta:
                    print(f"   Worker: {attempt_meta['application_method']}")
            
            return True
        else:
            print("\n⚠️  No applications found with 'applied' status")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying results: {e}")
        return False

def cleanup_test_data():
    """Clean up test data (optional)."""
    
    print("\n🧹 Cleanup Test Data")
    print("=" * 30)
    
    response = input("Do you want to clean up test applications? (y/N): ")
    
    if response.lower() == 'y':
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        supabase = create_client(supabase_url, supabase_key)
        
        try:
            # Delete test applications
            delete_response = supabase.table('applications').delete().eq('attempt_meta->test_run', True).execute()
            
            if delete_response.data:
                print(f"✅ Deleted {len(delete_response.data)} test applications")
            else:
                print("⚠️  No test applications found to delete")
                
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
    else:
        print("ℹ️  Test data preserved")

def main():
    """Main test function."""
    
    print("🔧 Simulated Application Worker Test Suite")
    print("=" * 60)
    
    # Step 1: Setup test data
    print("\n1️⃣  Setting up test data...")
    if not setup_test_data():
        print("❌ Failed to setup test data. Exiting.")
        return
    
    # Step 2: Test worker
    print("\n2️⃣  Testing worker...")
    if not test_worker():
        print("❌ Worker test failed. Exiting.")
        return
    
    # Step 3: Verify results
    print("\n3️⃣  Verifying results...")
    verify_results()
    
    # Step 4: Optional cleanup
    print("\n4️⃣  Cleanup...")
    cleanup_test_data()
    
    print("\n🎉 Test suite completed!")

if __name__ == "__main__":
    main()
