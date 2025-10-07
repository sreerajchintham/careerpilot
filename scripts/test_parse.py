#!/usr/bin/env python3
"""
Test script for simple_parse_resume function.

This script loads sample resume text and tests the parsing functionality
to verify email, phone, and skills extraction works correctly.
"""

import sys
import os
from pathlib import Path

# Add the backend app directory to Python path so we can import the function
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import simple_parse_resume


def test_parse_resume():
    """Test the simple_parse_resume function with sample data."""
    
    # Sample resume text for testing
    sample_resume = """
    John Doe
    Software Engineer
    
    Contact Information:
    Email: john.doe@email.com
    Phone: (555) 123-4567
    Location: San Francisco, CA
    
    Professional Summary:
    Experienced software engineer with 5+ years in full-stack development.
    
    Technical Skills:
    Python, JavaScript, React, Node.js, PostgreSQL, MongoDB, Docker, AWS, Git, 
    REST APIs, GraphQL, TypeScript, HTML/CSS, Linux, Agile methodologies
    
    Core Competencies:
    • Backend Development
    • Frontend Development  
    • Database Design
    • Cloud Architecture
    • Team Leadership
    
    Experience:
    Senior Software Engineer at TechCorp (2020-2023)
    - Led development of microservices architecture
    - Mentored junior developers
    - Improved system performance by 40%
    
    Software Engineer at StartupXYZ (2018-2020)
    - Built REST APIs using Python and Flask
    - Developed React frontend components
    - Implemented CI/CD pipelines
    
    Education:
    Bachelor of Science in Computer Science
    University of California, Berkeley (2014-2018)
    """
    
    print("Testing simple_parse_resume function...")
    print("=" * 50)
    
    # Test the parsing function
    result = simple_parse_resume(sample_resume)
    
    # Debug: Let's see what the skills section looks like
    print("\nDebug - Raw skills section from sample resume:")
    import re
    # Look for the actual pattern in our sample
    skills_match = re.search(r'Technical Skills:\s*([^C]+?)(?=Core Competencies)', sample_resume, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if skills_match:
        print(f"Found skills section: '{skills_match.group(1)}'")
    else:
        print("No skills section found with debug pattern")
        # Let's see what comes after "Technical Skills:"
        after_skills = re.search(r'Technical Skills:\s*(.+)', sample_resume, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if after_skills:
            print(f"After 'Technical Skills:': '{after_skills.group(1)[:200]}...'")
    
    # Print results
    print("Parsed Results:")
    print(f"Name: {result['name']}")
    print(f"Email: {result['email']}")
    print(f"Phone: {result['phone']}")
    print(f"Skills ({len(result['skills'])} found):")
    for i, skill in enumerate(result['skills'], 1):
        print(f"  {i}. {skill}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    
    # Verify expected results
    expected_email = "john.doe@email.com"
    expected_phone = "5551234567"
    expected_skills_count = 5  # Should find several skills
    
    print("\nVerification:")
    if result['email'] == expected_email:
        print("✅ Email extraction: PASS")
    else:
        print(f"❌ Email extraction: FAIL (expected {expected_email}, got {result['email']})")
    
    if result['phone'] == expected_phone:
        print("✅ Phone extraction: PASS")
    else:
        print(f"❌ Phone extraction: FAIL (expected {expected_phone}, got {result['phone']})")
    
    if len(result['skills']) >= expected_skills_count:
        print(f"✅ Skills extraction: PASS ({len(result['skills'])} skills found)")
    else:
        print(f"❌ Skills extraction: FAIL (expected at least {expected_skills_count}, got {len(result['skills'])})")


def test_edge_cases():
    """Test edge cases and different formats."""
    
    print("\n" + "=" * 50)
    print("Testing Edge Cases...")
    print("=" * 50)
    
    # Test with different phone formats
    phone_tests = [
        "Phone: 555-123-4567",
        "Tel: (555) 123-4567", 
        "Mobile: 555.123.4567",
        "Call me: 5551234567",
        "Contact: 123-456-7890"
    ]
    
    for phone_text in phone_tests:
        result = simple_parse_resume(phone_text)
        print(f"Input: '{phone_text}' -> Phone: {result['phone']}")
    
    # Test with different skills formats
    skills_tests = [
        "Skills: Python, JavaScript, React",
        "Technical Skills:\n• Python\n• JavaScript\n• React",
        "Core Competencies: Python; JavaScript; React",
        "Technologies: Python | JavaScript | React"
    ]
    
    for skills_text in skills_tests:
        result = simple_parse_resume(skills_text)
        print(f"Input: '{skills_text[:30]}...' -> Skills: {result['skills']}")


if __name__ == "__main__":
    try:
        test_parse_resume()
        test_edge_cases()
    except ImportError as e:
        print(f"Error importing function: {e}")
        print("Make sure you're running this from the project root directory.")
        print("And that the backend dependencies are installed.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
