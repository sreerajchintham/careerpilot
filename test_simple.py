#!/usr/bin/env python3
"""Simple test for the parser function."""

import sys
from pathlib import Path

# Add the backend app directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.main import simple_parse_resume

# Test with a simple skills section
test_text = """
John Doe
Software Engineer

Contact: john@example.com
Phone: (555) 123-4567

Skills:
Python, JavaScript, React, Node.js, PostgreSQL, MongoDB, Docker, AWS, Git,
REST APIs, GraphQL, TypeScript, HTML/CSS, Linux, Agile methodologies

Experience:
Software Engineer at TechCorp (2020-2023)
"""

result = simple_parse_resume(test_text)
print("Name:", result['name'])
print("Email:", result['email'])
print("Phone:", result['phone'])
print("Skills:", result['skills'])
print("Total skills found:", len(result['skills']))
