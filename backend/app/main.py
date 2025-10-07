import logging
import os
import uuid
import io
import re
from pathlib import Path
from typing import Dict, List, Optional

import pdfplumber
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# Configure basic logging to stdout. In production, prefer structured logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("careerpilot.backend")

app = FastAPI(title="CareerPilot Agent API")


def simple_parse_resume(text: str) -> Dict[str, any]:
    """
    Extract key information from resume text using regex heuristics.
    
    Looks for:
    - Email addresses (standard email format)
    - Phone numbers (10-digit US format, with optional formatting)
    - Skills sections (Technical Skills, Skills, etc.)
    
    Returns structured data for further processing.
    """
    result = {
        "name": None,
        "email": None,
        "phone": None,
        "skills": []
    }
    
    # Name extraction - look for common patterns at the beginning
    # Usually the first line or first few lines contain the name
    lines = text.strip().split('\n')
    for i, line in enumerate(lines[:5]):  # Check first 5 lines
        line = line.strip()
        if line and len(line) < 50:  # Reasonable name length
            # Skip common headers
            if not any(header in line.lower() for header in ['resume', 'cv', 'curriculum', 'contact', 'email', 'phone']):
                # Check if it looks like a name (2-4 words, mostly letters)
                words = line.split()
                if 2 <= len(words) <= 4 and all(word.replace('.', '').replace('-', '').isalpha() for word in words):
                    result["name"] = line
                    break
    
    # Email regex - looks for standard email format
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        result["email"] = email_match.group()
    
    # Phone regex - looks for 10-digit US phone numbers with optional formatting
    # Handles: (123) 456-7890, 123-456-7890, 123.456.7890, 1234567890
    phone_pattern = r'\b(?:\(?(\d{3})\)?[-.\s]?)?(\d{3})[-.\s]?(\d{4})\b'
    phone_matches = re.findall(phone_pattern, text)
    if phone_matches:
        # Take the first valid phone number found
        area, prefix, number = phone_matches[0]
        if area:  # Full 10-digit number
            result["phone"] = f"{area}{prefix}{number}"
        elif len(prefix) == 3 and len(number) == 4:  # 7-digit, might be incomplete
            # Look for area code nearby
            phone_context = text[max(0, text.find(phone_matches[0][1]) - 50):text.find(phone_matches[0][1]) + 50]
            area_match = re.search(r'\b(\d{3})\b', phone_context)
            if area_match:
                result["phone"] = f"{area_match.group(1)}{prefix}{number}"
    
    # Skills extraction - look for common skills section headers
    # Collect ALL skills sections, not just the first one
    all_skills_text = []
    
    skills_patterns = [
        r'(?:Technical\s+)?Skills?\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*[A-Z][a-z]|\n\s*\d|\n\s*[A-Z]{2,}|\Z)',
        r'Core\s+Competencies?\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*[A-Z][a-z]|\n\s*\d|\n\s*[A-Z]{2,}|\Z)',
        r'Technologies?\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*[A-Z][a-z]|\n\s*\d|\n\s*[A-Z]{2,}|\Z)',
        r'Programming\s+Languages?\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*[A-Z][a-z]|\n\s*\d|\n\s*[A-Z]{2,}|\Z)',
        r'Expertise\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*[A-Z][a-z]|\n\s*\d|\n\s*[A-Z]{2,}|\Z)',
        r'Proficiencies?\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*[A-Z][a-z]|\n\s*\d|\n\s*[A-Z]{2,}|\Z)'
    ]
    
    for pattern in skills_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            skills_section = match.group(1).strip()
            if skills_section:
                all_skills_text.append(skills_section)
    
    if all_skills_text:
        # Process each skills section found
        all_skills = []
        for skills_text in all_skills_text:
            # Clean up the skills text first
            skills_text = re.sub(r'\n\s*', ' ', skills_text)  # Replace newlines with spaces
            skills_text = re.sub(r'\s+', ' ', skills_text)   # Normalize whitespace
            
            # Split skills by common delimiters and clean up
            skills = []
            for delimiter in [',', ';', '\n', '|', '•', '·']:
                if delimiter in skills_text:
                    skills = [skill.strip() for skill in skills_text.split(delimiter)]
                    break
            
            # If no delimiter found, try to split by multiple spaces or common patterns
            if not skills:
                skills = re.split(r'\s{2,}|\t+', skills_text)
            
            # Clean up skills - remove empty strings and common prefixes
            for skill in skills:
                skill = skill.strip()
                if skill and len(skill) > 2:  # Skip single characters and very short strings
                    # Remove common prefixes like "•", "-", "*", "●"
                    skill = re.sub(r'^[•●\-*\s]+', '', skill)
                    # Remove trailing punctuation
                    skill = re.sub(r'[.,;:]+$', '', skill)
                    # Skip if it's too long (likely not a skill) or contains common non-skill words
                    if (len(skill) < 50 and 
                        skill and 
                        skill not in all_skills and
                        not any(word in skill.lower() for word in ['experience', 'years', 'worked', 'developed', 'created', 'built'])):
                        all_skills.append(skill)
        
        result["skills"] = all_skills[:20]  # Limit to first 20 skills
    
    return result

# Allow local frontend to access this API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Lightweight liveness endpoint for health checks."""
    return {"status": "ok"}


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Accepts a file upload via multipart/form-data under field name `file` and saves it
    into the local uploads directory using a UUID file name.

    Notes for beginners:
    - UploadFile streams the file and avoids loading the entire content into memory.
    - We don't trust client file names; we generate our own UUID to prevent collisions.
    - This example assumes PDFs; adapt the extension/validation as needed.
    """
    # Create uploads directory if it doesn't exist
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Optional: sanity check for content type (basic)
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        logger.warning("Unsupported content type: %s", file.content_type)
        # Still allow, but you may want to reject in stricter setups

    # Generate a random filename to avoid collisions and path traversal issues
    random_name = f"{uuid.uuid4().hex}.pdf"
    dest_path = uploads_dir / random_name

    try:
        # Read and persist the uploaded file to disk in chunks
        with dest_path.open("wb") as out_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                out_file.write(chunk)
        logger.info("Saved uploaded file to %s", dest_path)
        return {"ok": True, "path": str(dest_path)}
    except Exception as exc:
        logger.exception("Failed to save upload: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    finally:
        await file.close()


@app.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """
    Extracts text from uploaded PDF using pdfplumber.
    
    Common PDF extraction challenges:
    - Multi-column layouts: pdfplumber handles these better than basic text extraction
    - Scanned PDFs: These are images and need OCR (not implemented here)
    - Tables: pdfplumber can extract table data, but we're focusing on text
    - Images with text: Won't extract text from images
    - Complex formatting: May lose some formatting but preserves text content
    - Password-protected PDFs: Will fail unless password is provided
    
    Returns first 20,000 characters to avoid overwhelming responses.
    """
    try:
        # Read the uploaded file content
        file_content = await file.read()
        
        # Reset file pointer for potential retry
        await file.seek(0)
        
        # Try to extract text using pdfplumber
        try:
            # Convert bytes to file-like object for pdfplumber
            pdf_buffer = io.BytesIO(file_content)
            with pdfplumber.open(pdf_buffer) as pdf:
                extracted_text = ""
                
                # Extract text from each page
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += f"\n--- Page {page_num + 1} ---\n"
                        extracted_text += page_text
                
                # If no text extracted, try alternative extraction method
                if not extracted_text.strip():
                    logger.warning("No text extracted with standard method, trying alternative")
                    for page_num, page in enumerate(pdf.pages):
                        # Try extracting with different settings
                        page_text = page.extract_text(x_tolerance=3, y_tolerance=3)
                        if page_text:
                            extracted_text += f"\n--- Page {page_num + 1} (alt) ---\n"
                            extracted_text += page_text
                
                # Limit text length to prevent overwhelming responses
                if len(extracted_text) > 20000:
                    extracted_text = extracted_text[:20000] + "\n... [truncated]"
                
                if extracted_text.strip():
                    logger.info("Successfully extracted %d characters from PDF", len(extracted_text))
                    # Parse the extracted text for structured data
                    parsed_data = simple_parse_resume(extracted_text.strip())
                    return {
                        "text": extracted_text.strip(),
                        "parsed": parsed_data
                    }
                else:
                    logger.warning("No text could be extracted from PDF - may be scanned/image-based")
                    return {
                        "text": "",
                        "parsed": {"name": None, "email": None, "phone": None, "skills": []},
                        "error": "No text found in PDF. This may be a scanned document or image-based PDF that requires OCR."
                    }
                    
        except Exception as pdf_error:
            logger.error("PDF parsing failed: %s", str(pdf_error))
            # Fallback: try to read as plain text (will likely fail for PDFs)
            try:
                fallback_text = file_content.decode('utf-8', errors='ignore')
                if fallback_text.strip():
                    parsed_data = simple_parse_resume(fallback_text.strip())
                    return {
                        "text": fallback_text[:20000] + ("..." if len(fallback_text) > 20000 else ""),
                        "parsed": parsed_data,
                        "warning": "PDF parsing failed, returned raw content"
                    }
            except Exception:
                pass
            
            return {
                "text": "",
                "parsed": {"name": None, "email": None, "phone": None, "skills": []},
                "error": f"Failed to parse PDF: {str(pdf_error)}. This may be a corrupted file or unsupported format."
            }
            
    except Exception as e:
        logger.exception("Unexpected error in parse_resume: %s", str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error while processing file: {str(e)}"
        )
    finally:
        await file.close()


@app.get("/")
def root():
    return {"message": "Hello World"}