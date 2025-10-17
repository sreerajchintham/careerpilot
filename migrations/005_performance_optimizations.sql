-- Migration: 005_performance_optimizations.sql
-- Description: Add pgvector extension and performance indexes for embeddings and queries
-- This migration adds:
-- 1. pgvector extension for efficient vector similarity search
-- 2. Performance indexes for common queries
-- 3. Optimized indexes for job matching
-- 4. Additional useful indexes

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add vector columns to jobs and resumes tables
-- Note: We're keeping JSONB embeddings for now for backward compatibility
-- but adding dedicated vector columns for performance

-- Add vector column to jobs table if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='jobs' AND column_name='embedding'
    ) THEN
        ALTER TABLE jobs ADD COLUMN embedding vector(768);
    END IF;
END $$;

-- Add vector column to resumes table if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='resumes' AND column_name='embedding_vector'
    ) THEN
        ALTER TABLE resumes ADD COLUMN embedding_vector vector(768);
    END IF;
END $$;

-- Step 3: Migrate existing embeddings from JSONB to vector columns
-- For jobs: extract from raw->'embedding'
UPDATE jobs 
SET embedding = (raw->>'embedding')::vector(768)
WHERE raw->>'embedding' IS NOT NULL 
  AND embedding IS NULL;

-- For resumes: extract from parsed->'embedding'
UPDATE resumes 
SET embedding_vector = (parsed->>'embedding')::vector(768)
WHERE parsed->>'embedding' IS NOT NULL 
  AND embedding_vector IS NULL;

-- Step 4: Create HNSW indexes for vector similarity search
-- HNSW (Hierarchical Navigable Small World) is the most efficient index for cosine similarity

-- Index for jobs (used in job matching)
CREATE INDEX IF NOT EXISTS idx_jobs_embedding_hnsw 
ON jobs USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Index for resumes (used in reverse matching)
CREATE INDEX IF NOT EXISTS idx_resumes_embedding_hnsw 
ON resumes USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Step 5: Additional performance indexes for common queries

-- Index for job searches by title (used in scraper)
CREATE INDEX IF NOT EXISTS idx_jobs_title_lower 
ON jobs (LOWER(title));

-- Index for job searches by company
CREATE INDEX IF NOT EXISTS idx_jobs_company_lower 
ON jobs (LOWER(company));

-- Index for job searches by location
CREATE INDEX IF NOT EXISTS idx_jobs_location_lower 
ON jobs (LOWER(location));

-- Composite index for source and created_at (used in scraper dropdown)
CREATE INDEX IF NOT EXISTS idx_jobs_source_created 
ON jobs (source, created_at DESC);

-- GIN index for JSONB raw data (enables fast JSON searches)
CREATE INDEX IF NOT EXISTS idx_jobs_raw_gin 
ON jobs USING GIN (raw);

-- Index for finding jobs by URL (deduplication)
CREATE INDEX IF NOT EXISTS idx_jobs_raw_url 
ON jobs ((raw->>'url'));

-- Step 6: Application-specific indexes

-- Composite index for user applications by status
CREATE INDEX IF NOT EXISTS idx_applications_user_status 
ON applications (user_id, status, created_at DESC);

-- Index for recent applications (dashboard)
CREATE INDEX IF NOT EXISTS idx_applications_recent 
ON applications (user_id, created_at DESC);

-- GIN index for application artifacts (searching logs, errors)
CREATE INDEX IF NOT EXISTS idx_applications_artifacts_gin 
ON applications USING GIN (artifacts);

-- GIN index for attempt metadata
CREATE INDEX IF NOT EXISTS idx_applications_attempt_meta_gin 
ON applications USING GIN (attempt_meta);

-- Step 7: Resume-specific indexes

-- Index for current resumes (most common query)
CREATE INDEX IF NOT EXISTS idx_resumes_user_current 
ON resumes (user_id, is_current, created_at DESC);

-- GIN index for parsed resume data (searching skills, etc.)
CREATE INDEX IF NOT EXISTS idx_resumes_parsed_gin 
ON resumes USING GIN (parsed);

-- Step 8: User profile indexes

-- GIN index for user profiles (searching skills, experience)
CREATE INDEX IF NOT EXISTS idx_users_profile_gin 
ON users USING GIN (profile);

-- Step 9: Create materialized view for fast dashboard stats
-- This pre-computes common aggregations

CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_stats AS
SELECT 
    u.id as user_id,
    COUNT(DISTINCT a.id) as total_applications,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'draft') as draft_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'submitted') as submitted_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'under_review') as under_review_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'interview') as interview_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'rejected') as rejected_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.status = 'accepted') as accepted_count,
    MAX(a.created_at) as last_application_date,
    COUNT(DISTINCT r.id) as total_resumes,
    MAX(r.created_at) as last_resume_upload
FROM users u
LEFT JOIN applications a ON u.id = a.user_id
LEFT JOIN resumes r ON u.id = r.user_id
GROUP BY u.id;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_stats_user 
ON dashboard_stats (user_id);

-- Step 10: Create function to refresh stats (call periodically or after updates)
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dashboard_stats;
END;
$$ LANGUAGE plpgsql;

-- Step 11: Add helpful comments
COMMENT ON COLUMN jobs.embedding IS 'Vector embedding for semantic job matching (768 dimensions, computed by Gemini AI)';
COMMENT ON COLUMN resumes.embedding_vector IS 'Vector embedding for semantic resume matching (768 dimensions, computed by Gemini AI)';
COMMENT ON INDEX idx_jobs_embedding_hnsw IS 'HNSW index for fast cosine similarity search on job embeddings';
COMMENT ON INDEX idx_resumes_embedding_hnsw IS 'HNSW index for fast cosine similarity search on resume embeddings';
COMMENT ON MATERIALIZED VIEW dashboard_stats IS 'Pre-computed dashboard statistics for fast loading';

-- Step 12: Analyze tables to update query planner statistics
ANALYZE jobs;
ANALYZE resumes;
ANALYZE applications;
ANALYZE users;

-- Migration complete!
-- Performance improvements expected:
-- - 10-100x faster vector similarity search with HNSW indexes
-- - Faster job listing and filtering with text indexes
-- - Faster dashboard loading with materialized view
-- - Better query planning with updated statistics

