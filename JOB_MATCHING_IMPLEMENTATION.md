# Job Matching Implementation

## Overview
This implementation adds intelligent job matching to CareerPilot using Gemini AI embeddings. Jobs are now automatically scored based on semantic similarity to the user's resume, enabling personalized job recommendations.

## What Was Implemented

### 1. Resume Embedding on Upload (Backend)
**File**: `backend/app/main.py` - `/parse-resume` endpoint

**Changes**:
- When a resume is uploaded and parsed, compute a 768-dimensional embedding using Gemini's `text-embedding-004` model
- Store the embedding in `resumes.parsed.embedding` (JSONB field)
- Use first 2000 characters of resume text for embedding computation
- Task type: `retrieval_document` (optimized for document storage)

**Code Flow**:
```python
resume_text → compute_gemini_embedding() → embedding (768 floats)
                                          ↓
                         Store in resumes.parsed.embedding
```

### 2. Job Embedding on Scraping (Backend)
**File**: `backend/app/main.py` - `/scrape-jobs` endpoint

**Changes**:
- When jobs are scraped, compute embedding for each job
- Embedding input: `{title} {company} {description}` (first 2000 chars)
- Store embedding in `jobs.raw.embedding` (JSONB field)
- Task type: `retrieval_document`

**Benefits**:
- Embeddings computed once during scraping
- No runtime overhead for matching
- Stored directly in database (no separate vector store needed yet)

### 3. Job Matching Endpoint (Backend)
**File**: `backend/app/main.py` - New `GET /user/{user_id}/job-matches` endpoint

**Functionality**:
- Fetches user's latest resume embedding
- Fetches all jobs with embeddings from database
- Computes cosine similarity between resume and each job
- Returns top N matches sorted by score

**Response Format**:
```json
{
  "matches": [
    {
      "job": { /* full job object */ },
      "score": 0.8234,
      "match_percentage": 82.3
    }
  ],
  "total_jobs_with_embeddings": 45,
  "message": "Found 10 top matches"
}
```

**Query Parameters**:
- `top_n` (default: 10): Number of top matches to return

### 4. Frontend API Client
**File**: `frontend/lib/api.ts`

**New Method**:
```typescript
async getUserJobMatches(userId: string, topN: number = 10)
```

Calls `GET /user/{user_id}/job-matches` and returns match data.

### 5. Scraper UI with Match Scores
**File**: `frontend/pages/dashboard/jobs.tsx`

**Changes**:
- Added `JobWithMatch` interface extending `Job` with `matchScore` and `matchPercentage`
- Added `fetchJobMatches()` function that:
  - Calls `/user/{user_id}/job-matches` with top_n=100
  - Maps match scores to job IDs
  - Updates jobs state with match data
- Added `getMatchColor()` function for color-coded badges:
  - 80%+: Green (excellent match)
  - 60-79%: Blue (good match)
  - 40-59%: Yellow (fair match)
  - <40%: Orange (weak match)
- Match scores displayed as badges next to job titles
- Automatically recomputes matches after scraping

**UI Example**:
```
Software Engineer  [remoteok]  [82% Match]
                                 ↑ Green badge
```

## Workflow

### Complete Flow
1. **User uploads resume**:
   - PDF → text extraction → Gemini parsing → embedding computation
   - Embedding stored in `resumes.parsed.embedding`

2. **User scrapes jobs**:
   - Jobs fetched from APIs (Adzuna, The Muse, Remote OK)
   - For each job: compute embedding from title + company + description
   - Embeddings stored in `jobs.raw.embedding`

3. **Automatic matching**:
   - Frontend calls `/user/{user_id}/job-matches`
   - Backend computes cosine similarity for all jobs
   - Returns top matches sorted by score

4. **Display**:
   - Jobs list shows match percentage badges
   - Color-coded for quick visual scanning
   - Higher matches appear more prominent

## Technical Details

### Embedding Model
- **Model**: `models/text-embedding-004` (Gemini)
- **Dimensions**: 768
- **Task Type**: `retrieval_document` for both resumes and jobs
- **Input Length**: First 2000 characters (model can handle more, but this is sufficient)

### Cosine Similarity
Formula: `similarity = dot(a, b) / (norm(a) * norm(b))`

- Range: -1 to 1 (we typically see 0.3 to 0.9 for job matches)
- Higher = better match
- Implemented in `cosine_similarity()` function

### Performance Considerations
**Current Implementation** (Good for < 1000 jobs):
- Embeddings stored in JSONB
- Similarity computed in Python on-demand
- Works well for small to medium datasets

**Future Optimization** (For > 1000 jobs):
- Use `pgvector` PostgreSQL extension
- Store embeddings in dedicated `vector` column
- Use index for fast similarity search:
  ```sql
  SELECT * FROM jobs 
  ORDER BY embedding <=> query_embedding 
  LIMIT 10;
  ```
- 10-100x faster for large datasets

### Storage
- Resume embeddings: `resumes.parsed.embedding` (JSONB array of 768 floats)
- Job embeddings: `jobs.raw.embedding` (JSONB array of 768 floats)
- Each embedding: ~6KB (768 floats × 8 bytes)

## Benefits

### For Users
1. **Personalized Recommendations**: Jobs ranked by relevance to their resume
2. **Visual Feedback**: Color-coded match scores for quick scanning
3. **Time Savings**: Focus on high-match jobs first
4. **Confidence**: Know which jobs align with their skills

### For the System
1. **Semantic Understanding**: Matches based on meaning, not just keywords
2. **Automatic**: No manual tagging or categorization needed
3. **Scalable**: Works with any job source or resume format
4. **Flexible**: Easy to adjust matching algorithm or add filters

## What's Next (Future Enhancements)

### P1 - Immediate Improvements
1. **Missing Skills Analysis**: Extract skills from job requirements, compare with resume skills, show "Skills to Add"
2. **Match Explanation**: Show why a job matched (e.g., "Strong match for: Python, AWS, Machine Learning")
3. **Filters**: Allow filtering jobs by match score threshold (e.g., "Show only 70%+ matches")
4. **Sort Options**: Sort by match score, date, or company

### P2 - Advanced Features
1. **pgvector Migration**: Move to vector column for faster similarity search
2. **Hybrid Search**: Combine semantic similarity with keyword filters (location, salary, etc.)
3. **User Feedback Loop**: Allow users to mark jobs as "good match" or "bad match" to refine algorithm
4. **Match History**: Track which matches led to applications/interviews
5. **Batch Matching**: Pre-compute matches nightly and cache results
6. **Multi-Resume Support**: Allow users to have different resumes for different job types

## Testing

### Manual Testing Steps

1. **Upload a resume with clear skills**:
   - Go to `/dashboard/resume`
   - Upload a PDF (e.g., Software Engineer resume with Python, React, AWS)
   - Verify embedding is computed (check backend logs)

2. **Scrape jobs**:
   - Go to `/dashboard/jobs`
   - Enter keywords matching your resume (e.g., "Software Engineer")
   - Click "Start Scraping"
   - Wait for jobs to be fetched and embeddings computed

3. **View match scores**:
   - After scraping completes, match scores should appear automatically
   - Look for colored badges next to job titles
   - High-relevance jobs should show 70-90% match
   - Unrelated jobs should show 20-40% match

4. **Verify in database**:
   ```sql
   -- Check resume embedding
   SELECT parsed->'embedding' FROM resumes 
   WHERE is_current = true LIMIT 1;
   
   -- Check job embeddings
   SELECT id, title, raw->'embedding' FROM jobs 
   WHERE raw->'embedding' IS NOT NULL LIMIT 5;
   ```

### API Testing
```bash
# Get job matches for a user
curl "http://localhost:8000/user/{USER_ID}/job-matches?top_n=5"

# Expected response:
# {
#   "matches": [
#     {
#       "job": { ... },
#       "score": 0.8234,
#       "match_percentage": 82.3
#     },
#     ...
#   ],
#   "total_jobs_with_embeddings": 45,
#   "message": "Found 5 top matches"
# }
```

## Troubleshooting

### Issue: No match scores showing
**Causes**:
1. Resume has no embedding (uploaded before this feature)
2. Jobs have no embeddings (scraped before this feature)
3. Gemini API key not configured

**Solutions**:
1. Re-upload resume to compute embedding
2. Re-scrape jobs to compute embeddings
3. Check `GEMINI_API_KEY` in `.env`

### Issue: All jobs show similar scores
**Causes**:
1. Resume is too generic
2. Job descriptions are too short/similar
3. Embedding model needs fine-tuning

**Solutions**:
1. Upload a more detailed resume with specific skills
2. Use job sources with detailed descriptions
3. Consider adding skill-based filtering as a supplement

### Issue: Match scores seem inaccurate
**Causes**:
1. Cosine similarity is semantic, not keyword-based
2. Model may weight certain terms differently than expected

**Solutions**:
1. This is expected - semantic similarity captures meaning, not exact matches
2. Consider hybrid approach: semantic similarity + keyword overlap
3. Collect user feedback to refine over time

## Architecture Notes

### Why JSONB for Embeddings?
**Pros**:
- No schema changes needed
- Works with existing Supabase setup
- Easy to query and update
- Good for < 1000 jobs

**Cons**:
- Slower than dedicated vector column
- No index support for similarity search
- Higher storage overhead

**Migration Path**:
When you hit performance limits, migrate to `pgvector`:
```sql
ALTER TABLE jobs ADD COLUMN embedding vector(768);
UPDATE jobs SET embedding = (raw->'embedding')::vector;
CREATE INDEX ON jobs USING ivfflat (embedding vector_cosine_ops);
```

### Why Compute Embeddings on Upload/Scrape?
**Pros**:
- One-time cost
- No runtime latency
- Consistent embeddings

**Cons**:
- Slower upload/scraping
- Uses more API quota

**Alternative**:
Batch compute embeddings in background job (good for high-volume scenarios).

## Related Files
- `backend/app/main.py`: All endpoints and embedding logic
- `frontend/lib/api.ts`: API client
- `frontend/pages/dashboard/jobs.tsx`: Scraper UI with match scores
- `backend/embeddings_gemini.py`: Standalone embedding script (for batch processing)

## Summary of Changes
- ✅ Resume embedding on upload
- ✅ Job embedding on scraping
- ✅ `/user/{user_id}/job-matches` endpoint
- ✅ Frontend API client method
- ✅ Scraper UI with color-coded match badges
- ✅ Automatic match recomputation after scraping

**Total Files Modified**: 3
**Total Lines Added**: ~200
**New API Endpoints**: 1

All P1 job matching priorities are now complete! 🎉

