#!/usr/bin/env python3
"""
Test script for the new POST /save-resume-draft endpoint.

This script tests the resume draft saving functionality with sample data.
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "http://127.0.0.1:8001"
SAVE_DRAFT_ENDPOINT = f"{BACKEND_URL}/save-resume-draft"

def test_save_resume_draft():
    """Test the save resume draft endpoint with sample data."""
    
    print("💾 Testing POST /save-resume-draft endpoint...")
    print(f"URL: {SAVE_DRAFT_ENDPOINT}")
    
    # Sample resume text
    sample_resume = """
    John Smith
    john.smith@email.com
    (555) 123-4567
    
    Software Engineer with 5+ years of experience in Python, JavaScript, and React.
    
    Skills:
    - Python, Django, Flask
    - JavaScript, React, Node.js
    - AWS, Docker, Kubernetes
    - PostgreSQL, MongoDB
    - Git, CI/CD
    - Machine Learning, Data Science
    
    Experience:
    Senior Software Engineer at TechCorp (2020-2023)
    - Developed scalable web applications using Python and React
    - Implemented microservices architecture with Docker and Kubernetes
    - Worked with AWS services including EC2, S3, and RDS
    - Led a team of 3 developers
    - Improved application performance by 40%
    
    Software Developer at StartupXYZ (2018-2020)
    - Built full-stack applications using Django and React
    - Implemented REST APIs and database optimization
    - Collaborated with cross-functional teams
    """
    
    # Sample applied suggestions
    sample_applied_suggestions = [
        {
            "text": "Add or emphasize: Quantify your achievements with specific metrics",
            "confidence": "high",
            "applied_text": "Quantify your achievements with specific metrics (e.g., 'increased performance by 25%')"
        },
        {
            "text": "Add or emphasize: Highlight your Python experience in the skills section",
            "confidence": "med",
            "applied_text": "Highlight your Python experience in the skills section if you have it"
        },
        {
            "text": "Add or emphasize: Include any leadership experience you have",
            "confidence": "low",
            "applied_text": "Include any leadership or team management experience you have"
        }
    ]
    
    # Sample job context
    sample_job_context = {
        "job_title": "Backend Engineer - Python/Django",
        "company": "DataFlow Solutions"
    }
    
    # Test data
    test_data = {
        "user_id": "test-user-123",
        "resume_text": sample_resume,
        "applied_suggestions": sample_applied_suggestions,
        "job_context": sample_job_context
    }
    
    try:
        print("📤 Sending request to backend...")
        response = requests.post(
            SAVE_DRAFT_ENDPOINT,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Success!")
            print(f"📋 Draft ID: {data.get('draft_id')}")
            print(f"💬 Message: {data.get('message')}")
            print(f"📊 Applied Suggestions: {data.get('applied_count')}")
            
            print("\n📝 Draft Summary:")
            print(f"   User: {test_data['user_id']}")
            print(f"   Job: {test_data['job_context']['job_title']} at {test_data['job_context']['company']}")
            print(f"   Resume Length: {len(test_data['resume_text'])} characters")
            print(f"   Suggestions Applied: {len(test_data['applied_suggestions'])}")
            
            print("\n🎯 Applied Suggestions:")
            for i, suggestion in enumerate(test_data['applied_suggestions'], 1):
                confidence_emoji = {
                    'high': '🟢',
                    'med': '🟡',
                    'low': '🔴'
                }.get(suggestion['confidence'], '⚪')
                
                print(f"   {i}. {confidence_emoji} [{suggestion['confidence'].upper()}] {suggestion['text']}")
                
        elif response.status_code == 422:
            print("❌ Validation Error!")
            print("Request data validation failed")
            try:
                error_data = response.json()
                print(f"Details: {error_data}")
            except:
                print(f"Response: {response.text}")
                
        else:
            print("❌ Error!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("Make sure the backend server is running on http://127.0.0.1:8001")
        print("Run: uvicorn app.main:app --reload --port 8001")
        
    except requests.exceptions.Timeout:
        print("❌ Request Timeout!")
        print("The server took too long to respond")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_validation():
    """Test request validation with invalid data."""
    
    print("\n🔍 Testing request validation...")
    
    # Test with missing required fields
    invalid_requests = [
        {},  # Empty request
        {"user_id": "test"},  # Missing other fields
        {"user_id": "test", "resume_text": "test"},  # Missing suggestions and context
        {"user_id": "test", "resume_text": "test", "applied_suggestions": []},  # Missing job_context
        {
            "user_id": "test",
            "resume_text": "test",
            "applied_suggestions": [{"text": "test"}],  # Missing confidence and applied_text
            "job_context": {"job_title": "test", "company": "test"}
        }
    ]
    
    for i, invalid_request in enumerate(invalid_requests, 1):
        try:
            response = requests.post(
                SAVE_DRAFT_ENDPOINT,
                json=invalid_request,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Test {i}: Status {response.status_code}")
            if response.status_code == 422:
                print("✅ Validation working correctly")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"Test {i}: Error - {e}")

def test_sample_frontend_request():
    """Test with data that would come from the frontend modal."""
    
    print("\n🌐 Testing with frontend-style request...")
    
    # This simulates what the frontend modal would send
    frontend_request = {
        "user_id": "current-user",
        "resume_text": "John Smith\nSoftware Engineer\nPython, JavaScript, React\n\nExperience:\n- Developed web applications\n- Worked with databases",
        "applied_suggestions": [
            {
                "text": "Add or emphasize: Quantify your achievements with specific metrics",
                "confidence": "high",
                "applied_text": "Quantify your achievements with specific metrics (e.g., 'increased performance by 25%')"
            },
            {
                "text": "Add or emphasize: Include any leadership experience you have",
                "confidence": "med",
                "applied_text": "Include any leadership or team management experience you have"
            }
        ],
        "job_context": {
            "job_title": "Full Stack Developer - Node.js/React",
            "company": "WebCraft Studios"
        }
    }
    
    try:
        response = requests.post(
            SAVE_DRAFT_ENDPOINT,
            json=frontend_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Frontend request successful!")
            print(f"📋 Draft saved with ID: {data.get('draft_id')}")
            print(f"📊 Applied {data.get('applied_count')} suggestions")
        else:
            print(f"❌ Frontend request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing frontend request: {e}")

if __name__ == "__main__":
    print("🚀 Resume Draft Save Test")
    print("=" * 50)
    print("This test verifies the new /save-resume-draft endpoint")
    print("that allows users to save modified resume versions.")
    print()
    
    test_validation()
    test_save_resume_draft()
    test_sample_frontend_request()
    
    print("\n" + "=" * 50)
    print("📝 Expected Results:")
    print("- Draft ID generated and returned")
    print("- Applied suggestions count matches input")
    print("- Success message returned")
    print("- Validation working for invalid requests")
    print("- Frontend-style requests work correctly")
    print("\n🎯 Key Features:")
    print("✅ Resume draft versioning")
    print("✅ Applied suggestions tracking")
    print("✅ Job context preservation")
    print("✅ User-specific drafts")
    print("✅ Validation and error handling")
    print("\n🔧 Next Steps:")
    print("1. Implement actual database storage")
    print("2. Add draft retrieval endpoints")
    print("3. Add draft management features")
    print("4. Integrate with user authentication")
