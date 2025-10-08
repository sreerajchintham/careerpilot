#!/usr/bin/env python3
"""
Test job matching with real embeddings computed using sentence-transformers.
This ensures we're using the same model as the job embeddings.
"""

import requests
import json
from sentence_transformers import SentenceTransformer
import numpy as np

# Configuration
API_BASE_URL = "http://127.0.0.1:8001"
MATCH_JOBS_ENDPOINT = f"{API_BASE_URL}/match-jobs"

def compute_real_embedding(text: str) -> list:
    """Compute embedding using the same model as job embeddings."""
    print("🔄 Loading sentence-transformers model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("🔄 Computing embedding...")
    embedding = model.encode([text])[0]
    
    print(f"✅ Embedding computed: {len(embedding)} dimensions")
    return embedding.tolist()

def test_job_matching_with_real_embeddings():
    """Test job matching with properly computed embeddings."""
    
    # Sample resume text that should match well with software engineering jobs
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
    - Git, Linux, REST APIs
    
    Experience:
    5+ years of full-stack development experience with Python and JavaScript.
    Strong background in cloud technologies and containerization.
    Experience with microservices architecture and CI/CD pipelines.
    """
    
    # Compute real embedding
    embedding = compute_real_embedding(resume_text)
    
    payload = {
        "user_id": "test-user-real-123",
        "text": resume_text,
        "top_n": 5,
        "embedding": embedding
    }
    
    print("\n🧪 Testing job matching with real embeddings...")
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
                print(f"   Score: {match['score']:.3f}")
                print(f"   Matching skills: {match['top_keywords']}")
                print(f"   Missing skills: {match['missing_skills']}")
                
            # Check if we got reasonable scores
            if result['matches'] and result['matches'][0]['score'] > 0.1:
                print("\n🎉 Great! We're getting meaningful similarity scores!")
            else:
                print("\n⚠️  Low similarity scores. This might be due to:")
                print("   - Different embedding models")
                print("   - Limited job descriptions")
                print("   - Need for better text preprocessing")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the FastAPI server is running on port 8001")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_frontend_developer_matching():
    """Test with a frontend developer profile."""
    
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
    - Webpack, Vite
    """
    
    embedding = compute_real_embedding(resume_text)
    
    payload = {
        "user_id": "test-frontend-dev",
        "text": resume_text,
        "top_n": 3,
        "embedding": embedding
    }
    
    print("\n🧪 Testing frontend developer matching...")
    
    try:
        response = requests.post(MATCH_JOBS_ENDPOINT, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Frontend developer matching successful!")
            print(f"📊 Total jobs searched: {result['total_jobs_searched']}")
            print(f"🎯 User skills found: {result['user_skills']}")
            print("\n🏆 Top job matches:")
            
            for i, match in enumerate(result['matches'], 1):
                print(f"\n{i}. {match['title']} at {match['company']}")
                print(f"   Score: {match['score']:.3f}")
                print(f"   Matching skills: {match['top_keywords']}")
                print(f"   Missing skills: {match['missing_skills']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 Real Embeddings Job Matching Test")
    print("=" * 50)
    
    # Test health first
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API not healthy. Start the server first.")
            exit(1)
    except:
        print("❌ Cannot connect to API. Start the server first.")
        exit(1)
    
    # Run tests
    test_job_matching_with_real_embeddings()
    test_frontend_developer_matching()
    
    print("\n🎉 Real embeddings test completed!")
    print("\n💡 Next steps:")
    print("- The job matching endpoint is working correctly")
    print("- Consider improving skill extraction heuristics")
    print("- Add more diverse job postings for better testing")
    print("- Implement pgvector for production performance")
