# Local Embeddings Generation

This document explains how to use the local embeddings system for semantic job matching in CareerPilot Agent.

## Overview

The `embeddings_local.py` script generates vector embeddings for job descriptions using the `all-MiniLM-L6-v2` model from sentence-transformers. These embeddings enable semantic search and similarity matching between user profiles and job postings.

## Model Information

**Model**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Download Size**: ~90MB
- **Memory Usage**: ~200-300MB during inference
- **Speed**: ~1000 sentences/second on CPU
- **Quality**: Good balance of speed and accuracy for general text

## Memory and Storage Considerations

### Download Requirements
- **Initial Download**: ~90MB for the model
- **Internet Required**: First run only (model is cached locally)

### Memory Usage
- **Model in Memory**: ~200-300MB
- **Per Job Embedding**: 384 dimensions × 4 bytes = 1.5KB
- **1000 Jobs**: ~1.5MB of embeddings
- **10,000 Jobs**: ~15MB of embeddings

### Storage Options
1. **Local File**: `jobs_vectors.json` (~1.5MB per 1000 jobs)
2. **Supabase Database**: Stored in `jobs.raw->embedding` field

## Installation

```bash
# Install required dependencies
pip install sentence-transformers numpy supabase python-dotenv

# Or install from requirements.txt
pip install -r requirements.txt
```

## Usage

### 1. Generate Embeddings from Sample Jobs (Local Storage)

```bash
cd backend
python embeddings_local.py --input file --input-file sample_jobs.json --storage local
```

### 2. Generate Embeddings from Supabase (Database Storage)

```bash
# Make sure you have .env file with Supabase credentials
python embeddings_local.py --input supabase --storage supabase
```

### 3. Command Line Options

```bash
python embeddings_local.py --help
```

**Options:**
- `--input`: Input source (`file` or `supabase`)
- `--input-file`: Path to JSON file (default: `sample_jobs.json`)
- `--storage`: Storage destination (`local` or `supabase`)
- `--output-file`: Output file path (default: `jobs_vectors.json`)
- `--model`: Model name (default: `all-MiniLM-L6-v2`)

## Environment Setup

### For Supabase Storage

Create `.env` file in `backend/` directory:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

## Example Output

### Local File Storage
```json
[
  {
    "id": "uuid-here",
    "title": "Senior Software Engineer",
    "company": "TechCorp Inc.",
    "location": "San Francisco, CA",
    "raw": {
      "description": "Job description...",
      "requirements": ["Python", "React", "AWS"],
      "embedding": [0.123, -0.456, 0.789, ...] // 384 dimensions
    }
  }
]
```

### Supabase Storage
Embeddings are stored in the `jobs.raw->embedding` field as a JSON array.

## Performance Tips

### Memory Optimization
- **Batch Processing**: Script processes jobs in batches of 32
- **CPU Usage**: Model runs on CPU by default
- **GPU Support**: Add `device='cuda'` for GPU acceleration (if available)

### Large Datasets
For 10,000+ jobs:
1. Use batch processing (already implemented)
2. Consider using a more powerful model for better quality
3. Monitor memory usage and adjust batch size

## Integration with Job Matching

### Using Embeddings for Similarity

```python
import numpy as np
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# User profile text
user_text = "Python developer with React experience"

# Job embedding (from database)
job_embedding = np.array(job['raw']['embedding'])

# Compute user embedding
user_embedding = model.encode([user_text])[0]

# Calculate cosine similarity
similarity = np.dot(user_embedding, job_embedding) / (
    np.linalg.norm(user_embedding) * np.linalg.norm(job_embedding)
)

print(f"Similarity score: {similarity:.3f}")
```

### Database Query for Similar Jobs

```sql
-- Find jobs similar to a user profile
-- (This would be implemented in your application logic)
SELECT 
    id, 
    title, 
    company,
    raw->>'embedding' as embedding
FROM jobs 
WHERE raw ? 'embedding'
ORDER BY similarity_score DESC
LIMIT 10;
```

## Troubleshooting

### Common Issues

1. **"Model not found" error**:
   - First run downloads the model (~90MB)
   - Ensure internet connection
   - Check disk space

2. **Memory errors**:
   - Reduce batch size in the script
   - Close other applications
   - Use a machine with more RAM

3. **Supabase connection errors**:
   - Verify `.env` file exists
   - Check Supabase credentials
   - Ensure database is accessible

4. **Slow performance**:
   - Normal for first run (model download)
   - Consider GPU acceleration
   - Reduce batch size if memory constrained

### Performance Benchmarks

**Test Environment**: MacBook Pro M1, 16GB RAM
- **Model Loading**: ~5 seconds
- **100 Jobs**: ~10 seconds
- **1000 Jobs**: ~60 seconds
- **Memory Peak**: ~400MB

## Alternative Models

If you need different performance characteristics:

```python
# Faster, smaller model
model = SentenceTransformer('all-MiniLM-L12-v2')  # 384 dims, slower but better

# Larger, more accurate model
model = SentenceTransformer('all-mpnet-base-v2')  # 768 dims, much slower but better quality

# Multilingual support
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
```

## Next Steps

1. **Run the script** to generate embeddings for your jobs
2. **Integrate with FastAPI** to serve similarity queries
3. **Build job matching** endpoints using the embeddings
4. **Add user profile embeddings** for personalized matching
5. **Implement real-time updates** when new jobs are added
