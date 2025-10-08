#!/usr/bin/env python3
"""
Debug the job matching endpoint to see why skill matching isn't working.
"""

import requests
import json
from sentence_transformers import SentenceTransformer

# Configuration
API_BASE_URL = "http://127.0.0.1:8001"
MATCH_JOBS_ENDPOINT = f"{API_BASE_URL}/match-jobs"

def test_job_matching_debug():
    """Test job matching with debug output."""
    
    # Simple resume text
    resume_text = """
    John Smith
    Python Developer
    
    Skills:
    - Python, JavaScript, React
    - AWS, Docker
    - PostgreSQL, MongoDB
    """
    
    # Compute embedding
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode([resume_text])[0].tolist()
    
    payload = {
        "user_id": "debug-user",
        "text": resume_text,
        "top_n": 1,
        "embedding": embedding
    }
    
    print("🧪 Testing job matching with debug...")
    print(f"📄 Resume text: {resume_text}")
    
    try:
        response = requests.post(MATCH_JOBS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Job matching successful!")
            print(f"📊 Total jobs searched: {result['total_jobs_searched']}")
            print(f"🎯 User skills found: {result['user_skills']}")
            
            if result['matches']:
                match = result['matches'][0]
                print(f"\n🏆 Top match:")
                print(f"   Title: {match['title']}")
                print(f"   Company: {match['company']}")
                print(f"   Score: {match['score']}")
                print(f"   Matching skills: {match['top_keywords']}")
                print(f"   Missing skills: {match['missing_skills']}")
                
                # Debug: Let's check what's in the job data
                print(f"\n🔍 Debugging skill matching...")
                print(f"   User skills: {result['user_skills']}")
                print(f"   Matching skills: {match['top_keywords']}")
                print(f"   Missing skills: {match['missing_skills']}")
                
                if not match['top_keywords'] and not match['missing_skills']:
                    print("   ⚠️  No skills found - this suggests an issue with skill extraction or matching")
                else:
                    print("   ✅ Skills found - matching is working!")
            else:
                print("❌ No matches found")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_job_matching_debug()
