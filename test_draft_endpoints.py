#!/usr/bin/env python3
"""
Test Draft Endpoints - Verify save and retrieve work end-to-end
"""

import requests
import json
import uuid

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"  # From migration 002

print("=" * 80)
print("TESTING DRAFT SAVE & RETRIEVE ENDPOINTS")
print("=" * 80)

# Test 1: Get existing drafts
print("\n1️⃣  Testing GET /user/{user_id}/drafts...")
try:
    response = requests.get(f"{API_BASE_URL}/user/{TEST_USER_ID}/drafts")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! Found {data['total_count']} draft(s)")
        print(f"   Drafts: {json.dumps(data, indent=2)[:500]}...")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Save a new draft
print("\n2️⃣  Testing POST /save-resume-draft...")
new_draft_payload = {
    "user_id": TEST_USER_ID,
    "resume_text": "John Doe\nSenior Software Engineer\n\nSkills:\n- Python, FastAPI, React\n- PostgreSQL, Docker\n\nExperience:\n- Built scalable APIs\n- Improved performance by 40%",
    "applied_suggestions": [
        {
            "text": "Add or emphasize: Quantify your impact",
            "confidence": "high",
            "applied_text": "Improved performance by 40%"
        },
        {
            "text": "Add or emphasize: Mention cloud technologies",
            "confidence": "medium",
            "applied_text": None
        }
    ],
    "job_context": {
        "job_title": "Senior Backend Engineer",
        "company": "TechCorp Inc"
    }
}

try:
    response = requests.post(
        f"{API_BASE_URL}/save-resume-draft",
        json=new_draft_payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! Draft saved with ID: {data['draft_id']}")
        print(f"   Message: {data['message']}")
        print(f"   Applied count: {data['applied_count']}")
        saved_draft_id = data['draft_id']
    else:
        print(f"   ❌ Failed: {response.text}")
        saved_draft_id = None
except Exception as e:
    print(f"   ❌ Error: {e}")
    saved_draft_id = None

# Test 3: Get drafts again (should show the new one)
print("\n3️⃣  Testing GET /user/{user_id}/drafts (after save)...")
try:
    response = requests.get(f"{API_BASE_URL}/user/{TEST_USER_ID}/drafts")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! Found {data['total_count']} draft(s)")
        
        if saved_draft_id:
            found = any(d.get('draft_id') == saved_draft_id for d in data.get('drafts', []))
            if found:
                print(f"   ✅ New draft {saved_draft_id} is in the list!")
            else:
                print(f"   ⚠️  New draft {saved_draft_id} NOT found in list")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Test with minimal payload (no job_context, no suggestions)
print("\n4️⃣  Testing POST /save-resume-draft (minimal payload)...")
minimal_draft_payload = {
    "user_id": TEST_USER_ID,
    "resume_text": "Jane Smith\nData Scientist\n\nSkills:\n- Python, TensorFlow, SQL",
    "applied_suggestions": [],
    "job_context": None
}

try:
    response = requests.post(
        f"{API_BASE_URL}/save-resume-draft",
        json=minimal_draft_payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! Minimal draft saved with ID: {data['draft_id']}")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Test with new user (should auto-create)
print("\n5️⃣  Testing POST /save-resume-draft (new user - auto-create)...")
new_user_id = str(uuid.uuid4())
print(f"   Using new user ID: {new_user_id}")

new_user_draft_payload = {
    "user_id": new_user_id,
    "resume_text": "Test User\nSoftware Developer",
    "applied_suggestions": [],
    "job_context": None
}

try:
    response = requests.post(
        f"{API_BASE_URL}/save-resume-draft",
        json=new_user_draft_payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success! New user created and draft saved: {data['draft_id']}")
    else:
        print(f"   ❌ Failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("""
If all tests passed:
  ✅ Draft saving works correctly
  ✅ Draft retrieval works correctly
  ✅ Auto-user creation works
  ✅ RPC functions are working

If any tests failed, check:
  - Is the backend running? (http://localhost:8001)
  - Are there errors in backend logs?
  - Run: tail -f backend/nohup.out
""")
print("=" * 80)

