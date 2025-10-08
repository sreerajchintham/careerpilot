#!/usr/bin/env python3
"""
Test script for the job matching endpoint.

This script demonstrates how to use the /match-jobs endpoint with different scenarios.
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://127.0.0.1:8001"  # Adjust port if needed
MATCH_JOBS_ENDPOINT = f"{API_BASE_URL}/match-jobs"

def test_job_matching_with_embedding():
    """Test job matching with a provided embedding (using sentence-transformers)."""
    
    # Sample resume text
    resume_text = """
    John Smith
    Senior Software Engineer
    
    Email: john.smith@email.com
    Phone: (555) 123-4567
    
    Technical Skills:
    - Python, JavaScript, React, Node.js
    - AWS, Docker, Kubernetes
    - PostgreSQL, MongoDB
    - Machine Learning, Data Science
    
    Experience:
    5+ years of full-stack development experience with Python and JavaScript.
    Strong background in cloud technologies and containerization.
    """
    
    # For this test, we'll use a dummy embedding (in real usage, compute with sentence-transformers)
    # In production, you would compute this using the same model as your job embeddings
    dummy_embedding = [0.1] * 384  # 384 dimensions for all-MiniLM-L6-v2
    
    payload = {
        "user_id": "test-user-123",
        "text": resume_text,
        "top_n": 3,
        "embedding": dummy_embedding
    }
    
    print("🧪 Testing job matching with provided embedding...")
    print(f"📄 Resume text: {resume_text[:100]}...")
    print(f"🔢 Embedding dimensions: {len(dummy_embedding)}")
    
    try:
        response = requests.post(MATCH_JOBS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Job matching successful!")
            print(f"📊 Total jobs searched: {result['total_jobs_searched']}")
            print(f"🎯 User skills found: {result['user_skills']}")
            print("\n🏆 Top job matches:")
            
            for i, match in enumerate(result['matches'], 1):
                print(f"\n{i}. {match['title']} at {match['company']}")
                print(f"   Score: {match['score']}")
                print(f"   Matching skills: {match['top_keywords']}")
                print(f"   Missing skills: {match['missing_skills']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the FastAPI server is running on port 8001")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_job_matching_with_openai():
    """Test job matching using OpenAI embeddings (requires OPENAI_API_KEY)."""
    
    resume_text = """
    Sarah Johnson
    Frontend Developer
    
    Email: sarah.j@email.com
    Phone: (555) 987-6543
    
    Skills:
    - React, TypeScript, JavaScript
    - HTML, CSS, Tailwind CSS
    - Node.js, Express
    - Git, GitHub
    - Testing with Jest and Cypress
    """
    
    payload = {
        "user_id": "test-user-456",
        "text": resume_text,
        "top_n": 5
        # No embedding provided - will use OpenAI if available
    }
    
    print("\n🧪 Testing job matching with OpenAI embeddings...")
    print(f"📄 Resume text: {resume_text[:100]}...")
    
    try:
        response = requests.post(MATCH_JOBS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Job matching successful!")
            print(f"📊 Total jobs searched: {result['total_jobs_searched']}")
            print(f"🎯 User skills found: {result['user_skills']}")
            print("\n🏆 Top job matches:")
            
            for i, match in enumerate(result['matches'], 1):
                print(f"\n{i}. {match['title']} at {match['company']}")
                print(f"   Score: {match['score']}")
                print(f"   Matching skills: {match['top_keywords']}")
                print(f"   Missing skills: {match['missing_skills']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the FastAPI server is running on port 8001")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_health_check():
    """Test if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is running and healthy!")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running.")
        return False


if __name__ == "__main__":
    print("🚀 CareerPilot Job Matching Test Suite")
    print("=" * 50)
    
    # Test API health first
    if not test_health_check():
        print("\n💡 To start the server, run:")
        print("   cd backend")
        print("   source .venv/bin/activate")
        print("   uvicorn app.main:app --reload --port 8001")
        exit(1)
    
    # Test job matching
    test_job_matching_with_embedding()
    test_job_matching_with_openai()
    
    print("\n🎉 Test suite completed!")
    print("\n💡 Tips:")
    print("- Set OPENAI_API_KEY in .env to use OpenAI embeddings")
    print("- Use sentence-transformers to compute embeddings locally")
    print("- Check Supabase dashboard to see job embeddings")
    print("- Consider using pgvector for production similarity search")
