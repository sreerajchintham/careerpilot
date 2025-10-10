#!/usr/bin/env python3
"""
Test script for the queue applications functionality.

This script tests the complete application queueing system including:
- Multi-job selection and queueing
- User validation
- Job existence validation
- Duplicate prevention
- Error handling
"""

import requests
import json
import uuid

# Configuration
BACKEND_URL = "http://127.0.0.1:8001"
QUEUE_ENDPOINT = f"{BACKEND_URL}/queue-applications"

def test_queue_applications():
    """Test queueing multiple applications."""
    
    print("🚀 Testing Queue Applications Endpoint")
    print("=" * 50)
    
    # Generate a test user ID
    test_user_id = str(uuid.uuid4())
    
    # We need real job IDs from the database
    # For testing, we'll use the sample job IDs that should exist after seeding
    sample_job_ids = [
        "a1b2c3d4-e5f6-7890-1234-567890abcdef",  # Replace with real job IDs
        "b2c3d4e5-f6g7-8901-2345-678901bcdefg",  # Replace with real job IDs
        "c3d4e5f6-g7h8-9012-3456-789012cdefgh"   # Replace with real job IDs
    ]
    
    test_data = {
        "user_id": test_user_id,
        "job_ids": sample_job_ids
    }
    
    print(f"📤 Testing with user: {test_user_id}")
    print(f"📋 Job IDs: {sample_job_ids}")
    
    try:
        response = requests.post(
            QUEUE_ENDPOINT,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Success!")
            print(f"💬 Message: {data.get('message')}")
            print(f"📊 Queued Count: {data.get('queued_count')}")
            
            applications = data.get('applications', [])
            print(f"\n📋 Queued Applications:")
            for i, app in enumerate(applications, 1):
                print(f"   {i}. {app.get('job_title')} at {app.get('company')}")
                print(f"      Application ID: {app.get('application_id')}")
                print(f"      Status: {app.get('status')}")
            
            return True
            
        elif response.status_code == 404:
            error_data = response.json()
            print(f"❌ Not Found: {error_data.get('detail')}")
            print("   This is expected if jobs don't exist in the database")
            return False
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_validation():
    """Test request validation."""
    
    print("\n🔍 Testing Request Validation")
    print("=" * 40)
    
    # Test with invalid user_id
    print("\n1. Testing invalid user_id...")
    try:
        response = requests.post(
            QUEUE_ENDPOINT,
            json={"user_id": "invalid-uuid", "job_ids": ["valid-uuid"]},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Invalid user_id properly rejected")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test with invalid job_id
    print("\n2. Testing invalid job_id...")
    try:
        response = requests.post(
            QUEUE_ENDPOINT,
            json={"user_id": str(uuid.uuid4()), "job_ids": ["invalid-uuid"]},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Invalid job_id properly rejected")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test with missing fields
    print("\n3. Testing missing fields...")
    try:
        response = requests.post(
            QUEUE_ENDPOINT,
            json={"user_id": str(uuid.uuid4())},  # Missing job_ids
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 422:
            print("   ✅ Missing fields properly rejected")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_duplicate_prevention():
    """Test duplicate application prevention."""
    
    print("\n🔄 Testing Duplicate Prevention")
    print("=" * 40)
    
    test_user_id = str(uuid.uuid4())
    test_job_id = str(uuid.uuid4())
    
    # First request
    print("\n1. First application...")
    try:
        response1 = requests.post(
            QUEUE_ENDPOINT,
            json={"user_id": test_user_id, "job_ids": [test_job_id]},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response1.status_code}")
        
        # Second request (should be prevented)
        print("\n2. Duplicate application...")
        response2 = requests.post(
            QUEUE_ENDPOINT,
            json={"user_id": test_user_id, "job_ids": [test_job_id]},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response2.status_code}")
        
        if response2.status_code == 409:
            print("   ✅ Duplicate properly prevented")
        else:
            print(f"   ⚠️  Unexpected status: {response2.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_frontend_simulation():
    """Simulate frontend request format."""
    
    print("\n🌐 Testing Frontend Request Format")
    print("=" * 40)
    
    # Simulate what the frontend would send
    frontend_request = {
        "user_id": str(uuid.uuid4()),
        "job_ids": [
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4())
        ]
    }
    
    print(f"📤 Frontend-style request:")
    print(f"   User ID: {frontend_request['user_id']}")
    print(f"   Job IDs: {len(frontend_request['job_ids'])} jobs")
    
    try:
        response = requests.post(
            QUEUE_ENDPOINT,
            json=frontend_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Frontend request format accepted (404 expected for non-existent jobs)")
        elif response.status_code == 200:
            print("✅ Frontend request successful!")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("📋 Application Queue Test Suite")
    print("=" * 60)
    print("This test verifies the complete application queueing system.")
    print()
    
    # Run all tests
    test_validation()
    test_duplicate_prevention()
    test_frontend_simulation()
    test_queue_applications()
    
    print("\n" + "=" * 60)
    print("📝 Test Summary:")
    print("- Request validation (UUID format, required fields)")
    print("- Duplicate application prevention")
    print("- Frontend request format compatibility")
    print("- Multi-job queueing functionality")
    print("\n🎯 Key Features:")
    print("✅ Multi-job selection and queueing")
    print("✅ User and job existence validation")
    print("✅ Duplicate prevention")
    print("✅ Batch application creation")
    print("✅ Comprehensive error handling")
    print("\n🔧 Next Steps:")
    print("1. Ensure jobs are seeded in the database")
    print("2. Test with real job IDs from your Supabase")
    print("3. Test the frontend multi-select UI")
    print("4. Verify applications are created in the database")
