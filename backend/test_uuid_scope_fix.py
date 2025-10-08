#!/usr/bin/env python3
"""
Quick test to verify the UUID scope fix works.
"""

import requests
import uuid

def test_save_draft():
    """Test saving a draft with proper UUID."""
    
    print("🔧 Testing UUID scope fix...")
    
    # Generate a valid UUID
    test_user_id = str(uuid.uuid4())
    
    test_data = {
        "user_id": test_user_id,
        "resume_text": "Test resume content for UUID fix",
        "applied_suggestions": [
            {
                "text": "Add or emphasize: Test suggestion",
                "confidence": "high",
                "applied_text": "Test suggestion text"
            }
        ],
        "job_context": {
            "job_title": "Test Job",
            "company": "Test Company"
        }
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8001/save-resume-draft",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! UUID scope fix working correctly")
            print(f"   Draft ID: {data.get('draft_id')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 UUID Scope Fix Test")
    print("=" * 30)
    
    success = test_save_draft()
    
    if success:
        print("\n🎉 Fix successful! The UUID scope issue is resolved.")
        print("   The backend can now properly generate and validate UUIDs.")
    else:
        print("\n⚠️  Test failed. Please check the backend logs for details.")
    
    print("\n💡 The issue was caused by redundant 'import uuid' statements")
    print("   inside functions, which created local variables that shadowed")
    print("   the global import. This has been fixed by removing the redundant imports.")
