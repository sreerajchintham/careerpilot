#!/usr/bin/env python3
"""
Test script to verify that the embedding fix resolves the low/negative similarity scores.

This script tests the job matching with real embeddings computed on the backend
instead of dummy random embeddings from the frontend.
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "http://127.0.0.1:8001"
MATCH_ENDPOINT = f"{BACKEND_URL}/match-jobs"

def test_job_matching_with_real_embeddings():
    """Test job matching with real embeddings computed on the backend."""
    
    print("🧪 Testing job matching with real embeddings...")
    print(f"URL: {MATCH_ENDPOINT}")
    
    # Sample resume text that should match with some jobs
    sample_resume_text = """
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
    
    test_data = {
        "user_id": "test-user-123",
        "text": sample_resume_text,
        "top_n": 5
        # No embedding field - let backend compute it
    }
    
    try:
        print("📤 Sending request to backend...")
        response = requests.post(
            MATCH_ENDPOINT,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for embedding computation
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get('matches', [])
            user_skills = data.get('user_skills', [])
            total_searched = data.get('total_jobs_searched', 0)
            
            print("✅ Success!")
            print(f"📊 Total jobs searched: {total_searched}")
            print(f"🎯 User skills extracted: {len(user_skills)}")
            print(f"🔍 Top skills: {user_skills[:5]}")
            print(f"📋 Job matches found: {len(matches)}")
            print()
            
            if matches:
                print("🏆 Job Matches (with REAL similarity scores):")
                print("=" * 60)
                
                for i, match in enumerate(matches, 1):
                    score = match.get('score', 0)
                    title = match.get('title', 'Unknown')
                    company = match.get('company', 'Unknown')
                    matching_skills = match.get('top_keywords', [])
                    missing_skills = match.get('missing_skills', [])
                    
                    print(f"{i}. {title} at {company}")
                    print(f"   📈 Match Score: {score:.3f} ({score*100:.1f}%)")
                    print(f"   ✅ Matching Skills: {', '.join(matching_skills[:3])}")
                    print(f"   ❌ Missing Skills: {', '.join(missing_skills[:3])}")
                    print()
                
                # Check if scores are reasonable
                max_score = max(match.get('score', 0) for match in matches)
                min_score = min(match.get('score', 0) for match in matches)
                
                print("📊 Score Analysis:")
                print(f"   Highest score: {max_score:.3f} ({max_score*100:.1f}%)")
                print(f"   Lowest score: {min_score:.3f} ({min_score*100:.1f}%)")
                
                if max_score > 0.1:  # 10% similarity
                    print("✅ Scores look reasonable! Real embeddings are working.")
                elif max_score > 0.01:  # 1% similarity
                    print("⚠️  Scores are low but positive. This might be normal for diverse job descriptions.")
                else:
                    print("❌ Scores are still very low. There might be an issue with embeddings.")
                    
            else:
                print("❌ No job matches found!")
                
        elif response.status_code == 400:
            error_data = response.json()
            print("❌ Bad Request!")
            print(f"Error: {error_data.get('detail', 'Unknown error')}")
            
        else:
            print("❌ Error!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("Make sure the backend server is running on http://127.0.0.1:8001")
        print("Run: uvicorn app.main:app --reload --port 8001")
        
    except requests.exceptions.Timeout:
        print("❌ Request Timeout!")
        print("The server took too long to respond (embedding computation can be slow)")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_embedding_computation():
    """Test if the backend can compute embeddings."""
    
    print("\n🔍 Testing embedding computation capability...")
    
    try:
        # Test health endpoint first
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if health_response.status_code != 200:
            print("❌ Backend not responding")
            return
            
        print("✅ Backend is running")
        
        # Test with a simple text
        simple_data = {
            "user_id": "test",
            "text": "Python developer with React experience",
            "top_n": 1
        }
        
        response = requests.post(
            MATCH_ENDPOINT,
            json=simple_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Embedding computation is working!")
        elif response.status_code == 400:
            error_data = response.json()
            if "embedding" in error_data.get('detail', '').lower():
                print("❌ Embedding computation not available")
                print("Make sure sentence-transformers is installed: pip install sentence-transformers")
            else:
                print(f"❌ Other error: {error_data.get('detail')}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing embedding: {e}")

if __name__ == "__main__":
    print("🚀 Embedding Fix Test")
    print("=" * 50)
    print("This test verifies that job matching now uses real embeddings")
    print("instead of dummy random embeddings from the frontend.")
    print()
    
    test_embedding_computation()
    test_job_matching_with_real_embeddings()
    
    print("\n" + "=" * 50)
    print("📝 Expected Results:")
    print("- Similarity scores should be positive and reasonable (0.1-0.8 range)")
    print("- No more negative scores or extremely low percentages")
    print("- Job matches should make semantic sense")
    print("- Skills analysis should be accurate")
    print("\n🎯 If scores are still low:")
    print("1. Check that sentence-transformers is installed")
    print("2. Verify that job embeddings exist in the database")
    print("3. Ensure the model is loading correctly")
