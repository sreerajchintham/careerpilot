# Job Matching API Documentation

## Overview

The `/match-jobs` endpoint provides semantic job matching using embeddings and skill analysis. It compares resume text against job postings to find the best matches based on both semantic similarity and skill overlap.

## Endpoint

```
POST /match-jobs
```

## Request Format

```json
{
  "user_id": "string",
  "text": "string",
  "top_n": 5,
  "embedding": [0.1, 0.2, ...] // Optional
}
```

### Parameters

- **`user_id`** (required): Unique identifier for the user
- **`text`** (required): Resume text content to match against jobs
- **`top_n`** (optional, default: 5): Number of top matches to return
- **`embedding`** (optional): Pre-computed embedding vector. If not provided and `OPENAI_API_KEY` is set, will compute using OpenAI

## Response Format

```json
{
  "matches": [
    {
      "job_id": "uuid",
      "title": "Senior Software Engineer",
      "company": "TechCorp Inc.",
      "score": 0.847,
      "top_keywords": ["Python", "React", "AWS"],
      "missing_skills": ["Kubernetes", "Docker"]
    }
  ],
  "total_jobs_searched": 10,
  "user_skills": ["Python", "JavaScript", "React"]
}
```

### Response Fields

- **`matches`**: Array of job matches, sorted by similarity score (highest first)
- **`total_jobs_searched`**: Total number of jobs with embeddings that were compared
- **`user_skills`**: Skills extracted from the resume text

### Match Object Fields

- **`job_id`**: Unique identifier of the job
- **`title`**: Job title
- **`company`**: Company name
- **`score`**: Similarity score (0.0 to 1.0, higher is better)
- **`top_keywords`**: Skills that match between user and job
- **`missing_skills`**: Skills required by job but not in user profile

## How It Works

### 1. Resume Processing
- Extracts skills from resume text using regex heuristics
- Computes embedding using OpenAI (if available) or uses provided embedding

### 2. Job Matching
- Queries all jobs with embeddings from Supabase
- Computes cosine similarity between resume and job embeddings
- Analyzes skill overlap between user and job requirements

### 3. Skill Analysis
- **Top Keywords**: Skills present in both user profile and job requirements
- **Missing Skills**: Skills required by job but not found in user profile

## Example Usage

### Using Provided Embedding

```python
import requests

payload = {
    "user_id": "user-123",
    "text": "Python developer with React experience...",
    "top_n": 3,
    "embedding": [0.1, 0.2, ...]  # 384 dimensions for all-MiniLM-L6-v2
}

response = requests.post("http://localhost:8001/match-jobs", json=payload)
result = response.json()
```

### Using OpenAI Embeddings

```python
import requests

payload = {
    "user_id": "user-123",
    "text": "Python developer with React experience...",
    "top_n": 3
    # No embedding needed - will use OpenAI if OPENAI_API_KEY is set
}

response = requests.post("http://localhost:8001/match-jobs", json=payload)
result = response.json()
```

## Configuration

### Environment Variables

```bash
# Required for Supabase integration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Optional for OpenAI embeddings
OPENAI_API_KEY=your-openai-key
```

### Dependencies

```bash
pip install fastapi uvicorn supabase openai numpy pydantic
```

## Production Considerations

### Performance Optimization

1. **Use pgvector Extension**:
   ```sql
   -- Enable pgvector extension
   CREATE EXTENSION vector;
   
   -- Add vector column
   ALTER TABLE jobs ADD COLUMN embedding_vector vector(384);
   
   -- Create index for similarity search
   CREATE INDEX ON jobs USING ivfflat (embedding_vector vector_cosine_ops);
   
   -- Query with similarity
   SELECT *, 1 - (embedding_vector <=> %s) as similarity 
   FROM jobs 
   ORDER BY similarity DESC 
   LIMIT %s;
   ```

2. **Caching**:
   - Cache computed embeddings for frequently searched profiles
   - Use Redis for embedding cache
   - Implement TTL for cache entries

3. **Rate Limiting**:
   - Implement rate limiting per user/IP
   - Consider API quotas for OpenAI usage

### Security

1. **Authentication**:
   - Add JWT token validation
   - Implement user authorization
   - Validate user_id ownership

2. **Input Validation**:
   - Sanitize resume text input
   - Validate embedding dimensions
   - Limit text length

### Monitoring

1. **Logging**:
   - Log matching requests and performance
   - Track embedding computation time
   - Monitor API usage patterns

2. **Metrics**:
   - Track similarity score distributions
   - Monitor job match success rates
   - Measure API response times

## Error Handling

### Common Errors

- **400 Bad Request**: Missing required fields or invalid embedding dimensions
- **500 Internal Server Error**: Supabase connection issues or OpenAI API errors

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Testing

Run the test script to verify functionality:

```bash
cd backend
python test_job_matching.py
```

## Limitations

1. **Skill Extraction**: Current implementation uses regex heuristics. Consider using NER models for better accuracy.

2. **Embedding Models**: Different embedding models may produce different results. Ensure consistency between job and resume embeddings.

3. **Language Support**: Currently optimized for English text. Consider multilingual models for global applications.

4. **Real-time Updates**: Job embeddings are computed offline. Consider real-time embedding updates for new jobs.

## Future Enhancements

1. **Advanced Skill Matching**:
   - Use skill ontologies for better matching
   - Implement skill similarity scoring
   - Add skill level assessment

2. **Personalization**:
   - Learn from user application history
   - Implement collaborative filtering
   - Add preference-based ranking

3. **Multi-modal Matching**:
   - Include location preferences
   - Consider salary expectations
   - Add company culture matching

4. **Analytics Dashboard**:
   - Track matching accuracy
   - Monitor user engagement
   - A/B test different algorithms
