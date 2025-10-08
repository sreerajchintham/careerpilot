#!/usr/bin/env python3
"""
Debug script to test skill extraction and matching.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import extract_skills_from_text, analyze_job_match, simple_parse_resume

def test_skill_extraction():
    """Test skill extraction from different texts."""
    
    # Test resume text
    resume_text = """
    John Smith
    Senior Software Engineer
    
    Technical Skills:
    - Python, JavaScript, React, Node.js
    - AWS, Docker, Kubernetes
    - PostgreSQL, MongoDB
    - Machine Learning, Data Science
    """
    
    print("🧪 Testing skill extraction from resume:")
    print(f"Text: {resume_text}")
    
    # Test resume parsing
    parsed = simple_parse_resume(resume_text)
    print(f"Parsed skills: {parsed['skills']}")
    
    # Test direct skill extraction
    extracted = extract_skills_from_text(resume_text)
    print(f"Extracted skills: {extracted}")
    
    # Test job description
    job_text = """
    We're looking for a Senior Software Engineer to join our growing team. 
    You'll work on building scalable web applications using modern technologies.
    
    Requirements:
    - 5+ years of software development experience
    - Strong proficiency in Python, JavaScript, and React
    - Experience with PostgreSQL and MongoDB
    - Knowledge of AWS services
    - Experience with Docker and Kubernetes
    """
    
    print("\n🧪 Testing skill extraction from job description:")
    print(f"Text: {job_text}")
    
    job_skills = extract_skills_from_text(job_text)
    print(f"Job skills: {job_skills}")
    
    # Test skill matching
    print("\n🧪 Testing skill matching:")
    user_skills = parsed['skills']
    job_requirements = ["5+ years of software development experience", "Strong proficiency in Python, JavaScript, and React"]
    
    match_result = analyze_job_match(user_skills, job_text, job_requirements)
    print(f"Matching skills: {match_result['top_keywords']}")
    print(f"Missing skills: {match_result['missing_skills']}")

if __name__ == "__main__":
    test_skill_extraction()
