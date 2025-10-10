import logging
import os
import uuid
import io
import re
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

import pdfplumber
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure basic logging to stdout. In production, prefer structured logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("careerpilot.backend")

# Optional OpenAI integration for embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available. Will require embedding in request.")

# Optional sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Will require embedding in request.")

# Optional Supabase integration
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available. Job matching will not work.")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="CareerPilot Agent API")

# Initialize Supabase client if available
supabase_client: Optional[Client] = None
if SUPABASE_AVAILABLE:
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    if supabase_url and supabase_key:
        try:
            supabase_client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized for job matching")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            supabase_client = None

# Initialize OpenAI client if available
openai_client = None
if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        openai_client = openai
        logger.info("✅ OpenAI client initialized for embeddings")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        openai_client = None

# Initialize sentence transformer model for local embeddings
sentence_model = None
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        # Use the same model as in embeddings_local.py
        sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Sentence transformer model loaded for local embeddings")
    except Exception as e:
        logger.error(f"Failed to load sentence transformer model: {e}")
        sentence_model = None


# Pydantic models for request/response
class JobMatchRequest(BaseModel):
    user_id: str
    text: str
    top_n: int = 5
    embedding: Optional[List[float]] = None  # Optional if OpenAI is available


class JobMatch(BaseModel):
    job_id: str
    title: str
    company: str
    score: float
    top_keywords: List[str]
    missing_skills: List[str]


class JobMatchResponse(BaseModel):
    matches: List[JobMatch]
    total_jobs_searched: int
    user_skills: List[str]


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
        r'Skills?\s*:?\s*(.*?)(?=\n\n|\n[A-Z][a-z]|\n\d|\Z)',
        r'(?:Technical\s+)?Skills?\s*:?\s*(.*?)(?=\n\n|\n[A-Z][a-z]|\n\d|\Z)',
        r'Core\s+Competencies?\s*:?\s*(.*?)(?=\n\n|\n[A-Z][a-z]|\n\d|\Z)',
        r'Technologies?\s*:?\s*(.*?)(?=\n\n|\n[A-Z][a-z]|\n\d|\Z)',
        r'Programming\s+Languages?\s*:?\s*(.*?)(?=\n\n|\n[A-Z][a-z]|\n\d|\Z)',
        r'Expertise\s*:?\s*(.*?)(?=\n\n|\n[A-Z][a-z]|\n\d|\Z)',
        r'Proficiencies?\s*:?\s*(.*?)(?=\n\n|\n[A-Z][a-z]|\n\d|\Z)'
    ]
    
    for pattern in skills_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
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
            # Split skills by common delimiters, prioritizing commas and newlines
            skills = []
            
            # First try comma separation (most common)
            if ',' in skills_text:
                skills = [skill.strip() for skill in skills_text.split(',')]
            # Then try newline separation
            elif '\n' in skills_text:
                skills = [skill.strip() for skill in skills_text.split('\n')]
            # Then try other delimiters
            else:
                for delimiter in [';', '|', '•', '·']:
                    if delimiter in skills_text:
                        skills = [skill.strip() for skill in skills_text.split(delimiter)]
                        break
            
            # If we still have combined skills (like "React - AWS"), split by dashes too
            if skills:
                expanded_skills = []
                for skill in skills:
                    if ' - ' in skill or ' -' in skill or '- ' in skill:
                        # Split by dashes and add each part
                        parts = re.split(r'\s*-\s*', skill)
                        expanded_skills.extend([part.strip() for part in parts if part.strip()])
                    else:
                        expanded_skills.append(skill)
                skills = expanded_skills
            
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


def compute_openai_embedding(text: str) -> List[float]:
    """
    Compute embedding using OpenAI's text-embedding-ada-002 model.
    
    Note: In production, consider using pgvector extension for PostgreSQL
    to store and query embeddings efficiently with cosine similarity.
    """
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not available")
    
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to compute OpenAI embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute embedding")


def compute_local_embedding(text: str) -> List[float]:
    """Compute embedding using local sentence-transformers model"""
    if not sentence_model:
        raise HTTPException(status_code=500, detail="Sentence transformer model not available")
    
    try:
        # Truncate text to reasonable length for embedding
        max_length = 512  # Most models have token limits
        if len(text) > max_length:
            text = text[:max_length]
        
        embedding = sentence_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to compute local embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute local embedding")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    
    For production with pgvector, this would be handled by the database:
    SELECT 1 - (embedding <=> query_embedding) as similarity
    """
    if len(a) != len(b):
        raise ValueError("Vectors must have the same length")
    
    # Convert to numpy arrays for efficient computation
    a_np = np.array(a)
    b_np = np.array(b)
    
    # Compute cosine similarity
    dot_product = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills from job description or resume text using simple heuristics.
    
    This is a basic implementation. In production, consider using:
    - Named Entity Recognition (NER) models
    - Skill extraction APIs
    - Pre-trained skill classification models
    """
    # Common technical skills patterns - more comprehensive
    skill_patterns = [
        # Programming Languages
        r'\b(?:Python|JavaScript|Java|C\+\+|C#|Go|Rust|Swift|Kotlin|PHP|Ruby|Scala|TypeScript)\b',
        # Frameworks & Libraries
        r'\b(?:React|Angular|Vue|Node\.?js|Express|Django|Flask|Spring|Laravel|Rails|Next\.?js|Nuxt)\b',
        # Cloud & DevOps
        r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|Linux|Windows|macOS|Terraform|Ansible)\b',
        # Databases
        r'\b(?:PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|SQLite|Oracle|Cassandra|DynamoDB)\b',
        # AI/ML
        r'\b(?:Machine Learning|AI|Data Science|Analytics|Statistics|TensorFlow|PyTorch|Scikit-learn|Pandas|NumPy)\b',
        # Methodologies & Concepts
        r'\b(?:Agile|Scrum|DevOps|CI/CD|Microservices|REST|GraphQL|API|TDD|BDD)\b',
        # Frontend Technologies
        r'\b(?:HTML|CSS|SASS|LESS|Tailwind|Bootstrap|Webpack|Babel|Jest|Cypress|Selenium)\b',
        # Tools & Platforms
        r'\b(?:GitHub|GitLab|Bitbucket|Jira|Confluence|Slack|Figma|Sketch|VS Code|IntelliJ)\b',
        # Additional Technologies
        r'\b(?:React Native|Flutter|Xamarin|Cordova|Ionic|Electron|WebAssembly)\b',
        r'\b(?:Apache|Nginx|Tomcat|IIS|Load Balancer|CDN|DNS|SSL|TLS)\b'
    ]
    
    skills = set()
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        # Clean up matches and add to set
        for match in matches:
            # Handle special cases like "Node.js" -> "Node.js"
            if match.lower() in ['node.js', 'nodejs']:
                skills.add('Node.js')
            elif match.lower() in ['next.js', 'nextjs']:
                skills.add('Next.js')
            else:
                skills.add(match)
    
    return list(skills)


def analyze_job_match(user_skills: List[str], job_description: str, job_requirements: List[str]) -> Dict[str, List[str]]:
    """
    Analyze job match by comparing user skills with job requirements.
    
    Returns:
        - top_keywords: Skills that match between user and job
        - missing_skills: Skills required by job but not in user profile
    """
    # Extract skills from job description and requirements
    job_skills = set()
    job_skills.update(extract_skills_from_text(job_description))
    
    # Add explicit requirements
    for req in job_requirements:
        job_skills.update(extract_skills_from_text(req))
    
    # Normalize skills for comparison (handle variations)
    def normalize_skill(skill: str) -> str:
        """Normalize skill names for better matching."""
        skill_lower = skill.lower().strip()
        # Handle common variations
        variations = {
            'node.js': 'nodejs',
            'nodejs': 'nodejs',
            'next.js': 'nextjs',
            'nextjs': 'nextjs',
            'c++': 'cpp',
            'c#': 'csharp',
            'machine learning': 'ml',
            'data science': 'ds',
            'artificial intelligence': 'ai'
        }
        return variations.get(skill_lower, skill_lower)
    
    user_skills_normalized = {normalize_skill(skill): skill for skill in user_skills}
    job_skills_normalized = {normalize_skill(skill): skill for skill in job_skills}
    
    # Find matching skills (return original skill names)
    matching_normalized = set(user_skills_normalized.keys()).intersection(set(job_skills_normalized.keys()))
    top_keywords = [user_skills_normalized[skill] for skill in matching_normalized]
    
    # Find missing skills (return original skill names)
    missing_normalized = set(job_skills_normalized.keys()) - set(user_skills_normalized.keys())
    missing_skills = [job_skills_normalized[skill] for skill in missing_normalized]
    
    return {
        "top_keywords": top_keywords[:10],  # Limit to top 10
        "missing_skills": missing_skills[:10]  # Limit to top 10
    }


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


@app.post("/match-jobs", response_model=JobMatchResponse)
async def match_jobs(request: JobMatchRequest):
    """
    Match jobs based on resume text using semantic similarity and skill analysis.
    
    This endpoint:
    1. Computes embedding for the resume text (using OpenAI if available, or accepts embedding in request)
    2. Queries jobs with embeddings from Supabase
    3. Computes cosine similarity between resume and job embeddings
    4. Analyzes skills match using heuristics
    5. Returns top N matching jobs with scores and skill analysis
    
    Production considerations:
    - Use pgvector extension for efficient similarity search in PostgreSQL
    - Consider caching embeddings for frequently searched profiles
    - Implement rate limiting for API calls
    - Add user authentication and authorization
    - Consider using more sophisticated skill extraction models
    """
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not available")
    
    try:
        # Step 1: Parse resume to extract skills
        parsed_resume = simple_parse_resume(request.text)
        user_skills = parsed_resume.get("skills", [])
        
        # Step 2: Compute or use provided embedding
        if request.embedding:
            # Use provided embedding
            resume_embedding = request.embedding
            logger.info("Using provided embedding for job matching")
        elif openai_client:
            # Compute embedding using OpenAI
            resume_embedding = compute_openai_embedding(request.text)
            logger.info("Computed OpenAI embedding for job matching")
        elif sentence_model:
            # Compute embedding using local sentence-transformers model
            resume_embedding = compute_local_embedding(request.text)
            logger.info("Computed local embedding for job matching")
        else:
            raise HTTPException(
                status_code=400, 
                detail="No embedding provided and no embedding service available. Please provide 'embedding' field in request or configure OpenAI/sentence-transformers."
            )
        
        # Step 3: Query jobs with embeddings from Supabase
        # Note: In production with pgvector, this would be:
        # SELECT *, 1 - (raw->'embedding' <=> %s) as similarity 
        # FROM jobs WHERE raw ? 'embedding' 
        # ORDER BY similarity DESC LIMIT %s
        response = supabase_client.table('jobs').select('*').execute()
        
        if not response.data:
            return JobMatchResponse(
                matches=[],
                total_jobs_searched=0,
                user_skills=user_skills
            )
        
        # Step 4: Compute similarities and analyze matches
        job_matches = []
        
        for job in response.data:
            # Check if job has embedding
            raw_data = job.get('raw', {})
            if not isinstance(raw_data, dict) or 'embedding' not in raw_data:
                continue  # Skip jobs without embeddings
            
            job_embedding = raw_data['embedding']
            
            # Compute cosine similarity
            try:
                similarity_score = cosine_similarity(resume_embedding, job_embedding)
            except ValueError as e:
                logger.warning(f"Skipping job {job.get('id')} due to embedding dimension mismatch: {e}")
                continue
            
            # Analyze skills match
            job_description = raw_data.get('description', '')
            job_requirements = raw_data.get('requirements', [])
            
            # Debug: Check if we have job data
            if not job_description and not job_requirements:
                logger.warning(f"Job {job['id']} has no description or requirements data")
            
            skill_analysis = analyze_job_match(user_skills, job_description, job_requirements)
            
            # Create job match object
            job_match = JobMatch(
                job_id=job['id'],
                title=job['title'],
                company=job['company'],
                score=round(similarity_score, 3),
                top_keywords=skill_analysis['top_keywords'],
                missing_skills=skill_analysis['missing_skills']
            )
            
            job_matches.append(job_match)
        
        # Step 5: Sort by similarity score and return top N
        job_matches.sort(key=lambda x: x.score, reverse=True)
        top_matches = job_matches[:request.top_n]
        
        logger.info(f"Found {len(job_matches)} jobs with embeddings, returning top {len(top_matches)}")
        
        return JobMatchResponse(
            matches=top_matches,
            total_jobs_searched=len(job_matches),
            user_skills=user_skills
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in job matching: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Pydantic models for resume edit proposal request
class SuggestionItem(BaseModel):
    text: str
    confidence: str  # "low", "med", "high"

class ResumeEditRequest(BaseModel):
    job_id: str
    resume_text: str

class ResumeEditResponse(BaseModel):
    suggestions: List[SuggestionItem]


def get_ai_resume_suggestions(resume_text: str, job_description: str, job_requirements: List[str], job_title: str, company: str) -> List[SuggestionItem]:
    """
    Generate AI-powered resume suggestions using OpenAI GPT.
    
    IMPORTANT: User must approve any edits before applying them to their resume.
    This function only provides suggestions - it does not modify the user's resume.
    """
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not available for AI suggestions")
    
    try:
        # Prepare the prompt for OpenAI
        requirements_text = "\n".join(f"- {req}" for req in job_requirements) if job_requirements else "Not specified"
        
        prompt = f"""
You are a professional resume consultant helping a candidate improve their resume for a specific job application.

JOB INFORMATION:
- Position: {job_title} at {company}
- Description: {job_description}
- Requirements: 
{requirements_text}

CANDIDATE'S CURRENT RESUME:
{resume_text}

INSTRUCTIONS:
Generate up to 6 concise, actionable resume improvement suggestions. Each suggestion should:
1. Be framed as "Add or emphasize: [specific recommendation]"
2. Be truthful and based on what's actually in the resume
3. NOT invent or suggest fake experience the candidate doesn't have
4. Be 1-2 sentences maximum
5. Focus on improving match with the job requirements
6. Be specific and actionable

EXAMPLES OF GOOD SUGGESTIONS:
- "Add or emphasize: Quantify your achievements with specific metrics (e.g., 'increased performance by 25%')"
- "Add or emphasize: Highlight your Python experience in the skills section if you have it"
- "Add or emphasize: Include any leadership or team management experience you have"

EXAMPLES OF BAD SUGGESTIONS (DON'T DO THIS):
- "Add or emphasize: 5 years of Kubernetes experience" (if not in resume)
- "Add or emphasize: AWS certification" (if not mentioned)

Return your suggestions as a JSON array of objects with this exact format:
[
  {{"text": "Add or emphasize: [your suggestion]", "confidence": "high"}},
  {{"text": "Add or emphasize: [your suggestion]", "confidence": "med"}},
  {{"text": "Add or emphasize: [your suggestion]", "confidence": "low"}}
]

Use confidence levels:
- "high": Very clear improvement that directly matches job requirements
- "med": Good improvement that would help with job match
- "low": Minor improvement or general resume advice

IMPORTANT: Only suggest things that are truthful and can be verified from the resume content.
"""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional resume consultant. Always be truthful and never suggest fake experience."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3  # Lower temperature for more consistent, factual responses
        )
        
        # Parse the AI response
        ai_response = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            # Extract JSON from response (in case there's extra text)
            start_idx = ai_response.find('[')
            end_idx = ai_response.rfind(']') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                suggestions_data = json.loads(json_str)
                
                # Convert to SuggestionItem objects
                suggestions = []
                for item in suggestions_data:
                    if isinstance(item, dict) and 'text' in item and 'confidence' in item:
                        confidence = item['confidence'].lower()
                        if confidence not in ['low', 'med', 'high']:
                            confidence = 'med'  # Default to medium if invalid
                        
                        suggestions.append(SuggestionItem(
                            text=item['text'],
                            confidence=confidence
                        ))
                
                return suggestions[:6]  # Limit to 6 suggestions
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            # Fallback: return a generic suggestion
            return [SuggestionItem(
                text="Add or emphasize: Review the job requirements and ensure your relevant experience is prominently featured",
                confidence="med"
            )]
            
    except Exception as e:
        logger.error(f"Failed to get AI resume suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI suggestions")


@app.post("/propose-resume", response_model=ResumeEditResponse)
async def propose_resume_edits(request: ResumeEditRequest):
    """
    Propose resume edits to better match a specific job.
    
    IMPORTANT: These are only suggestions. Users must approve any edits before 
    applying them to their resume. This endpoint does not modify the user's resume.
    
    Behavior:
    - If OPENAI_API_KEY is set: Uses AI to generate up to 6 personalized suggestions
    - If no OpenAI key: Falls back to heuristic analysis of missing skills
    - All suggestions are framed as "Add or emphasize: [recommendation]"
    - AI suggestions are truthful and don't invent experience
    """
    try:
        # Get job details from Supabase
        if not supabase_client:
            raise HTTPException(status_code=500, detail="Supabase client not available")
        
        # Validate job_id format (should be a UUID)
        try:
            uuid.UUID(request.job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job_id format. Must be a valid UUID.")
        
        # Fetch job details
        response = supabase_client.table('jobs').select('*').eq('id', request.job_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = response.data[0]
        job_data = job.get('raw', {})
        job_title = job.get('title', 'Unknown Position')
        company = job.get('company', 'Unknown Company')
        
        # Extract job requirements and description
        job_description = job_data.get('description', '')
        job_requirements = job_data.get('requirements', [])
        
        suggestions = []
        
        # Try AI-powered suggestions first (if OpenAI is available)
        if openai_client:
            try:
                logger.info(f"Using AI to generate resume suggestions for job {request.job_id}")
                ai_suggestions = get_ai_resume_suggestions(
                    request.resume_text, 
                    job_description, 
                    job_requirements, 
                    job_title, 
                    company
                )
                suggestions = ai_suggestions
                logger.info(f"Generated {len(suggestions)} AI-powered suggestions")
                
            except Exception as e:
                logger.warning(f"AI suggestion generation failed, falling back to heuristics: {e}")
                # Fall through to heuristic suggestions
        
        # Fallback: Heuristic-based suggestions (if no AI or AI failed)
        if not suggestions:
            logger.info(f"Using heuristic analysis for resume suggestions for job {request.job_id}")
            
            # Parse user's resume to extract skills
            parsed_resume = simple_parse_resume(request.resume_text)
            user_skills = parsed_resume.get("skills", [])
            
            # Extract job skills
            job_skills = set()
            job_skills.update(extract_skills_from_text(job_description))
            for req in job_requirements:
                job_skills.update(extract_skills_from_text(req))
            
            # Find missing skills
            user_skills_set = set(skill.lower() for skill in user_skills)
            missing_skills = []
            
            for job_skill in job_skills:
                if job_skill.lower() not in user_skills_set:
                    missing_skills.append(job_skill)
            
            # Generate top 3 missing skill suggestions
            for skill in missing_skills[:3]:
                suggestions.append(SuggestionItem(
                    text=f"Add '{skill}' to Skills section",
                    confidence="high"
                ))
            
            # Add general improvement suggestions
            if len(request.resume_text.split()) < 200:
                suggestions.append(SuggestionItem(
                    text="Add or emphasize: More detailed descriptions of your projects and achievements",
                    confidence="med"
                ))
            
            if not any(keyword in request.resume_text.lower() for keyword in ['project', 'portfolio', 'github']):
                suggestions.append(SuggestionItem(
                    text="Add or emphasize: Links to your projects, portfolio, or GitHub profile",
                    confidence="med"
                ))
        
        # Ensure we have at least one suggestion
        if not suggestions:
            suggestions.append(SuggestionItem(
                text="Add or emphasize: Keywords from the job description that match your experience",
                confidence="low"
            ))
        
        # Limit to 6 suggestions maximum
        suggestions = suggestions[:6]
        
        logger.info(f"Generated {len(suggestions)} resume suggestions for job {request.job_id}")
        
        return ResumeEditResponse(suggestions=suggestions)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in resume edit proposal: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Pydantic models for resume draft saving
class AppliedSuggestion(BaseModel):
    text: str
    confidence: str
    applied_text: str

class JobContext(BaseModel):
    job_title: str
    company: str

class SaveResumeDraftRequest(BaseModel):
    user_id: str
    resume_text: str
    applied_suggestions: List[AppliedSuggestion]
    job_context: JobContext

class SaveResumeDraftResponse(BaseModel):
    draft_id: str
    message: str
    applied_count: int


@app.post("/save-resume-draft", response_model=SaveResumeDraftResponse)
async def save_resume_draft(request: SaveResumeDraftRequest):
    """
    Save a resume draft with applied suggestions.
    
    This endpoint saves a modified resume version with the user's selected
    suggestions applied. The draft is stored for future reference and can
    be used to create multiple versions for different job applications.
    
    IMPORTANT: This creates a new version, it doesn't modify the original resume.
    """
    try:
        # Generate a unique draft ID
        draft_id = str(uuid.uuid4())
        
        # Prepare draft data for storage
        draft_data = {
            "draft_id": draft_id,
            "user_id": request.user_id,
            "resume_text": request.resume_text,
            "applied_suggestions": [
                {
                    "text": suggestion.text,
                    "confidence": suggestion.confidence,
                    "applied_text": suggestion.applied_text
                }
                for suggestion in request.applied_suggestions
            ],
            "job_context": {
                "job_title": request.job_context.job_title,
                "company": request.job_context.company
            },
            "created_at": "now()",  # Will be set by database
            "word_count": len(request.resume_text.split()),
            "suggestions_count": len(request.applied_suggestions)
        }
        
        # Save to Supabase using the drafts column in users table
        if not supabase_client:
            raise HTTPException(status_code=500, detail="Supabase client not available")
        
        logger.info(f"Saving resume draft {draft_id} for user {request.user_id}")
        logger.info(f"Draft contains {len(request.applied_suggestions)} applied suggestions")
        logger.info(f"Target job: {request.job_context.job_title} at {request.job_context.company}")
        
        try:
            # Validate user_id format first
            try:
                uuid.UUID(request.user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
            
            # First, check if user exists, if not create them
            user_response = supabase_client.table('users').select('id').eq('id', request.user_id).execute()
            
            if not user_response.data:
                # Create user if they don't exist
                logger.info(f"Creating new user {request.user_id}")
                new_user = {
                    'id': request.user_id,
                    'email': f'user-{request.user_id}@careerpilot.local',  # Placeholder email
                    'profile': {'name': 'CareerPilot User', 'source': 'draft_system'},
                    'drafts': []
                }
                supabase_client.table('users').insert(new_user).execute()
            
            # Call the add_user_draft function
            # Note: We need to use RPC call since we're using a custom function
            rpc_response = supabase_client.rpc(
                'add_user_draft',
                {
                    'p_user_id': request.user_id,
                    'p_draft_id': draft_id,
                    'p_resume_text': request.resume_text,
                    'p_applied_suggestions': [
                        {
                            'text': suggestion.text,
                            'confidence': suggestion.confidence,
                            'applied_text': suggestion.applied_text
                        }
                        for suggestion in request.applied_suggestions
                    ],
                    'p_job_context': {
                        'job_title': request.job_context.job_title,
                        'company': request.job_context.company
                    }
                }
            ).execute()
            
            logger.info(f"Successfully saved resume draft {draft_id} to Supabase")
            
        except Exception as db_error:
            logger.error(f"Failed to save draft to database: {db_error}")
            raise HTTPException(status_code=500, detail=f"Failed to save draft to database: {str(db_error)}")
        
        return SaveResumeDraftResponse(
            draft_id=draft_id,
            message="Resume draft saved successfully",
            applied_count=len(request.applied_suggestions)
        )
        
    except Exception as e:
        logger.exception("Error saving resume draft: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save resume draft: {str(e)}")


# Pydantic models for draft retrieval
class GetUserDraftsResponse(BaseModel):
    user_id: str
    drafts: List[dict]
    total_count: int

class GetDraftResponse(BaseModel):
    draft_id: str
    resume_text: str
    applied_suggestions: List[AppliedSuggestion]
    job_context: JobContext
    created_at: str
    word_count: int
    suggestions_count: int


@app.get("/user/{user_id}/drafts", response_model=GetUserDraftsResponse)
async def get_user_drafts(user_id: str):
    """
    Get all resume drafts for a specific user.
    
    Returns all saved resume drafts with metadata for the user.
    """
    try:
        if not supabase_client:
            raise HTTPException(status_code=500, detail="Supabase client not available")
        
        # Validate UUID format
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
        
        # Get user's drafts using the custom function
        rpc_response = supabase_client.rpc('get_user_drafts', {'p_user_id': user_id}).execute()
        
        if not rpc_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        drafts_data = rpc_response.data[0] if rpc_response.data else []
        
        # Convert to list if it's not already
        if isinstance(drafts_data, str):
            import json
            drafts_data = json.loads(drafts_data)
        elif not isinstance(drafts_data, list):
            drafts_data = []
        
        logger.info(f"Retrieved {len(drafts_data)} drafts for user {user_id}")
        
        return GetUserDraftsResponse(
            user_id=user_id,
            drafts=drafts_data,
            total_count=len(drafts_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving user drafts: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve drafts: {str(e)}")


@app.get("/user/{user_id}/draft/{draft_id}", response_model=GetDraftResponse)
async def get_user_draft(user_id: str, draft_id: str):
    """
    Get a specific resume draft by draft_id.
    
    Returns the full draft data including resume text and applied suggestions.
    """
    try:
        if not supabase_client:
            raise HTTPException(status_code=500, detail="Supabase client not available")
        
        # Validate UUID formats
        try:
            uuid.UUID(user_id)
            uuid.UUID(draft_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id or draft_id format. Must be valid UUIDs.")
        
        # Get specific draft using the custom function
        rpc_response = supabase_client.rpc(
            'get_user_draft',
            {'p_user_id': user_id, 'p_draft_id': draft_id}
        ).execute()
        
        if not rpc_response.data or not rpc_response.data[0]:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        draft_data = rpc_response.data[0]
        
        # Convert applied_suggestions to AppliedSuggestion objects
        applied_suggestions = []
        for suggestion in draft_data.get('applied_suggestions', []):
            applied_suggestions.append(AppliedSuggestion(
                text=suggestion.get('text', ''),
                confidence=suggestion.get('confidence', 'low'),
                applied_text=suggestion.get('applied_text', '')
            ))
        
        # Create job context
        job_context = JobContext(
            job_title=draft_data.get('job_context', {}).get('job_title', ''),
            company=draft_data.get('job_context', {}).get('company', '')
        )
        
        logger.info(f"Retrieved draft {draft_id} for user {user_id}")
        
        return GetDraftResponse(
            draft_id=draft_id,
            resume_text=draft_data.get('resume_text', ''),
            applied_suggestions=applied_suggestions,
            job_context=job_context,
            created_at=draft_data.get('created_at', ''),
            word_count=draft_data.get('word_count', 0),
            suggestions_count=draft_data.get('suggestions_count', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving draft: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve draft: {str(e)}")


@app.delete("/user/{user_id}/draft/{draft_id}")
async def delete_user_draft(user_id: str, draft_id: str):
    """
    Delete a specific resume draft.
    
    Removes the draft from the user's drafts array.
    """
    try:
        if not supabase_client:
            raise HTTPException(status_code=500, detail="Supabase client not available")
        
        # Validate UUID formats
        try:
            uuid.UUID(user_id)
            uuid.UUID(draft_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id or draft_id format. Must be valid UUIDs.")
        
        # Delete the draft using the custom function
        rpc_response = supabase_client.rpc(
            'delete_user_draft',
            {'p_user_id': user_id, 'p_draft_id': draft_id}
        ).execute()
        
        if not rpc_response.data or not rpc_response.data[0]:
            raise HTTPException(status_code=404, detail="Draft not found or could not be deleted")
        
        deleted = rpc_response.data[0]
        
        if deleted:
            logger.info(f"Successfully deleted draft {draft_id} for user {user_id}")
            return {"message": "Draft deleted successfully", "draft_id": draft_id}
        else:
            raise HTTPException(status_code=404, detail="Draft not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting draft: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete draft: {str(e)}")


# Pydantic models for application queueing
class QueueApplicationsRequest(BaseModel):
    user_id: str
    job_ids: List[str]

class QueuedApplication(BaseModel):
    application_id: str
    user_id: str
    job_id: str
    job_title: str
    company: str
    status: str
    queued_at: str

class QueueApplicationsResponse(BaseModel):
    message: str
    queued_count: int
    applications: List[QueuedApplication]


@app.post("/queue-applications", response_model=QueueApplicationsResponse)
async def queue_applications(request: QueueApplicationsRequest):
    """
    Queue multiple job applications for a user.
    
    This endpoint allows users to select multiple jobs and queue them for application.
    Each application is created with status 'pending' and includes metadata about
    when it was queued.
    
    Validation:
    - User must exist in the system
    - All job_ids must be valid UUIDs
    - All jobs must exist in the database
    - No duplicate applications (user_id, job_id combination)
    """
    try:
        if not supabase_client:
            raise HTTPException(status_code=500, detail="Supabase client not available")
        
        # Validate user_id format
        try:
            uuid.UUID(request.user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")
        
        # Validate all job_ids format
        for job_id in request.job_ids:
            try:
                uuid.UUID(job_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid job_id format: {job_id}. Must be a valid UUID.")
        
        logger.info(f"Queueing {len(request.job_ids)} applications for user {request.user_id}")
        
        # Check if user exists
        user_response = supabase_client.table('users').select('id').eq('id', request.user_id).execute()
        if not user_response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if all jobs exist and get their details
        job_details = {}
        for job_id in request.job_ids:
            job_response = supabase_client.table('jobs').select('id, title, company').eq('id', job_id).execute()
            if not job_response.data:
                raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
            job_details[job_id] = job_response.data[0]
        
        # Check for existing applications to avoid duplicates
        existing_apps_response = supabase_client.table('applications').select('job_id').eq('user_id', request.user_id).in_('job_id', request.job_ids).execute()
        existing_job_ids = {app['job_id'] for app in existing_apps_response.data} if existing_apps_response.data else set()
        
        # Filter out jobs that already have applications
        new_job_ids = [job_id for job_id in request.job_ids if job_id not in existing_job_ids]
        
        if not new_job_ids:
            raise HTTPException(status_code=409, detail="All selected jobs already have applications")
        
        # Create application records
        applications_to_create = []
        queued_applications = []
        
        for job_id in new_job_ids:
            job_info = job_details[job_id]
            application_id = str(uuid.uuid4())
            
            application_data = {
                'id': application_id,
                'user_id': request.user_id,
                'job_id': job_id,
                'status': 'draft',  # Use 'draft' instead of 'pending' to match database constraint
                'artifacts': {},
                'attempt_meta': {
                    'queued_at': 'now()',
                    'queued_by': 'user_selection',
                    'source': 'job_matching',
                    'status': 'queued'  # Add internal status for tracking
                }
            }
            
            applications_to_create.append(application_data)
            
            queued_applications.append(QueuedApplication(
                application_id=application_id,
                user_id=request.user_id,
                job_id=job_id,
                job_title=job_info['title'],
                company=job_info['company'],
                status='draft',  # Match the database constraint
                queued_at='now()'
            ))
        
        # Insert all applications in a single batch
        if applications_to_create:
            insert_response = supabase_client.table('applications').insert(applications_to_create).execute()
            
            if not insert_response.data:
                raise HTTPException(status_code=500, detail="Failed to create applications")
        
        logger.info(f"Successfully queued {len(queued_applications)} applications for user {request.user_id}")
        
        # Prepare response message
        skipped_count = len(request.job_ids) - len(new_job_ids)
        message = f"Queued {len(queued_applications)} applications"
        if skipped_count > 0:
            message += f" ({skipped_count} already existed)"
        
        return QueueApplicationsResponse(
            message=message,
            queued_count=len(queued_applications),
            applications=queued_applications
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error queueing applications: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to queue applications: {str(e)}")


@app.get("/")
def root():
    return {"message": "Hello World"}