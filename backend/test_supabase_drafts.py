#!/usr/bin/env python3
"""
Test script for the Supabase-integrated resume draft functionality.

This script tests the complete draft management system including:
- Saving drafts to Supabase
- Retrieving user drafts
- Getting specific drafts
- Deleting drafts
"""

import requests
import json
import uuid

# Configuration
BACKEND_URL = "http://127.0.0.1:8001"
SAVE_DRAFT_ENDPOINT = f"{BACKEND_URL}/save-resume-draft"
GET_DRAFTS_ENDPOINT = f"{BACKEND_URL}/user/{{user_id}}/drafts"
GET_DRAFT_ENDPOINT = f"{BACKEND_URL}/user/{{user_id}}/draft/{{draft_id}}"
DELETE_DRAFT_ENDPOINT = f"{BACKEND_URL}/user/{{user_id}}/draft/{{draft_id}}"

def test_save_draft_to_supabase():
    """Test saving a draft to Supabase."""
    
    print("💾 Testing draft save to Supabase...")
    
    # Generate a test user ID
    test_user_id = str(uuid.uuid4())
    
    # Sample resume and suggestions
    sample_resume = """
    John Smith
    Software Engineer
    john.smith@email.com
    (555) 123-4567
    
    Experience:
    Senior Software Engineer at TechCorp (2020-2023)
    - Developed scalable web applications using Python and React
    - Implemented microservices architecture with Docker and Kubernetes
    - Led a team of 3 developers
    - Improved application performance by 40%
    
    Skills:
    Python, JavaScript, React, Docker, Kubernetes, AWS
    """
    
    sample_suggestions = [
        {
            "text": "Add or emphasize: Quantify your achievements with specific metrics",
            "confidence": "high",
            "applied_text": "Quantify your achievements with specific metrics (e.g., 'increased performance by 40%')"
        },
        {
            "text": "Add or emphasize: Include any leadership experience you have",
            "confidence": "med",
            "applied_text": "Include any leadership or team management experience you have"
        }
    ]
    
    test_data = {
        "user_id": test_user_id,
        "resume_text": sample_resume,
        "applied_suggestions": sample_suggestions,
        "job_context": {
            "job_title": "Senior Full Stack Developer",
            "company": "Innovation Labs"
        }
    }
    
    try:
        print(f"📤 Saving draft for user: {test_user_id}")
        response = requests.post(
            SAVE_DRAFT_ENDPOINT,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            draft_id = data.get('draft_id')
            
            print("✅ Draft saved successfully!")
            print(f"📋 Draft ID: {draft_id}")
            print(f"💬 Message: {data.get('message')}")
            print(f"📊 Applied Suggestions: {data.get('applied_count')}")
            
            return test_user_id, draft_id
        else:
            print(f"❌ Failed to save draft: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error saving draft: {e}")
        return None, None

def test_get_user_drafts(user_id):
    """Test retrieving all drafts for a user."""
    
    print(f"\n📋 Testing get user drafts for: {user_id}")
    
    try:
        url = GET_DRAFTS_ENDPOINT.format(user_id=user_id)
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Retrieved user drafts successfully!")
            print(f"👤 User ID: {data.get('user_id')}")
            print(f"📊 Total Drafts: {data.get('total_count')}")
            
            drafts = data.get('drafts', [])
            for i, draft in enumerate(drafts, 1):
                print(f"\n📄 Draft {i}:")
                print(f"   ID: {draft.get('draft_id')}")
                print(f"   Job: {draft.get('job_context', {}).get('job_title')} at {draft.get('job_context', {}).get('company')}")
                print(f"   Created: {draft.get('created_at')}")
                print(f"   Word Count: {draft.get('word_count')}")
                print(f"   Suggestions: {draft.get('suggestions_count')}")
            
            return drafts
        else:
            print(f"❌ Failed to get drafts: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Error getting drafts: {e}")
        return []

def test_get_specific_draft(user_id, draft_id):
    """Test retrieving a specific draft."""
    
    print(f"\n🔍 Testing get specific draft: {draft_id}")
    
    try:
        url = GET_DRAFT_ENDPOINT.format(user_id=user_id, draft_id=draft_id)
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Retrieved specific draft successfully!")
            print(f"📋 Draft ID: {data.get('draft_id')}")
            print(f"💼 Job: {data.get('job_context', {}).get('job_title')} at {data.get('job_context', {}).get('company')}")
            print(f"📅 Created: {data.get('created_at')}")
            print(f"📊 Word Count: {data.get('word_count')}")
            print(f"💡 Suggestions: {data.get('suggestions_count')}")
            
            # Show applied suggestions
            suggestions = data.get('applied_suggestions', [])
            if suggestions:
                print(f"\n🎯 Applied Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    confidence_emoji = {
                        'high': '🟢',
                        'med': '🟡',
                        'low': '🔴'
                    }.get(suggestion.get('confidence'), '⚪')
                    
                    print(f"   {i}. {confidence_emoji} [{suggestion.get('confidence', '').upper()}] {suggestion.get('text', '')}")
            
            # Show resume preview (first 200 chars)
            resume_text = data.get('resume_text', '')
            preview = resume_text[:200] + "..." if len(resume_text) > 200 else resume_text
            print(f"\n📄 Resume Preview:")
            print(f"   {preview}")
            
            return data
        else:
            print(f"❌ Failed to get specific draft: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting specific draft: {e}")
        return None

def test_delete_draft(user_id, draft_id):
    """Test deleting a draft."""
    
    print(f"\n🗑️ Testing delete draft: {draft_id}")
    
    try:
        url = DELETE_DRAFT_ENDPOINT.format(user_id=user_id, draft_id=draft_id)
        response = requests.delete(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Draft deleted successfully!")
            print(f"💬 Message: {data.get('message')}")
            print(f"📋 Deleted Draft ID: {data.get('draft_id')}")
            
            return True
        else:
            print(f"❌ Failed to delete draft: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting draft: {e}")
        return False

def test_complete_workflow():
    """Test the complete draft management workflow."""
    
    print("🚀 Testing Complete Draft Management Workflow")
    print("=" * 60)
    
    # Step 1: Save a draft
    user_id, draft_id = test_save_draft_to_supabase()
    
    if not user_id or not draft_id:
        print("❌ Cannot continue - draft save failed")
        return
    
    # Step 2: Get all drafts for the user
    drafts = test_get_user_drafts(user_id)
    
    if not drafts:
        print("❌ Cannot continue - no drafts found")
        return
    
    # Step 3: Get the specific draft we just created
    draft_data = test_get_specific_draft(user_id, draft_id)
    
    if not draft_data:
        print("❌ Cannot continue - specific draft not found")
        return
    
    # Step 4: Delete the draft
    deleted = test_delete_draft(user_id, draft_id)
    
    if deleted:
        print("\n✅ Complete workflow test successful!")
        
        # Step 5: Verify deletion by trying to get the draft again
        print(f"\n🔍 Verifying deletion...")
        url = GET_DRAFT_ENDPOINT.format(user_id=user_id, draft_id=draft_id)
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            print("✅ Deletion verified - draft no longer exists")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
    else:
        print("❌ Workflow test failed - deletion unsuccessful")

def test_error_scenarios():
    """Test error scenarios and edge cases."""
    
    print("\n🔍 Testing Error Scenarios")
    print("=" * 40)
    
    # Test with invalid UUID
    print("\n1. Testing with invalid user UUID...")
    try:
        response = requests.get(
            GET_DRAFTS_ENDPOINT.format(user_id="invalid-uuid"),
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ Invalid UUID properly rejected")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test with non-existent user
    print("\n2. Testing with non-existent user...")
    fake_uuid = str(uuid.uuid4())
    try:
        response = requests.get(
            GET_DRAFTS_ENDPOINT.format(user_id=fake_uuid),
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ Non-existent user properly handled")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test with non-existent draft
    print("\n3. Testing with non-existent draft...")
    fake_user_id = str(uuid.uuid4())
    fake_draft_id = str(uuid.uuid4())
    try:
        response = requests.get(
            GET_DRAFT_ENDPOINT.format(user_id=fake_user_id, draft_id=fake_draft_id),
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ Non-existent draft properly handled")
        else:
            print(f"   ⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🗄️ Supabase Resume Drafts Test")
    print("=" * 50)
    print("This test verifies the complete Supabase integration")
    print("for resume draft management functionality.")
    print()
    
    # Test the complete workflow
    test_complete_workflow()
    
    # Test error scenarios
    test_error_scenarios()
    
    print("\n" + "=" * 50)
    print("📝 Test Summary:")
    print("- Draft saving to Supabase users table")
    print("- Draft retrieval and management")
    print("- Error handling and validation")
    print("- Complete CRUD operations")
    print("\n🎯 Key Features:")
    print("✅ Supabase integration with users table")
    print("✅ JSONB drafts column storage")
    print("✅ Custom PostgreSQL functions")
    print("✅ UUID validation and error handling")
    print("✅ Complete draft lifecycle management")
    print("\n🔧 Next Steps:")
    print("1. Run the migration: psql -f migrations/002_add_drafts_to_users.sql")
    print("2. Test with real Supabase instance")
    print("3. Add frontend draft management UI")
    print("4. Implement draft versioning and comparison")
