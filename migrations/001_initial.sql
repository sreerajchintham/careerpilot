-- Migration: 001_initial.sql
-- Description: Initial database schema for CareerPilot Agent
-- Created: 2025-01-06

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table - stores user profiles and parsed resume data
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    profile JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Skills table - normalized skills for better matching
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    category TEXT, -- e.g., 'programming', 'framework', 'tool', 'soft_skill'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs table - stores job postings from various sources
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL, -- e.g., 'linkedin', 'indeed', 'company_website'
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    posted_at TIMESTAMPTZ,
    raw JSONB DEFAULT '{}', -- full job posting data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Job matches table - stores matching scores between users and jobs
CREATE TABLE job_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    score NUMERIC(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    match_details JSONB DEFAULT '{}', -- breakdown of why it matched
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

-- Applications table - tracks user applications to jobs
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'under_review', 'interview', 'rejected', 'accepted')),
    artifacts JSONB DEFAULT '{}', -- cover letter, resume version, etc.
    attempt_meta JSONB DEFAULT '{}', -- metadata about application attempts
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

-- Indexes for better query performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_posted_at ON jobs(posted_at);
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_job_matches_user_id ON job_matches(user_id);
CREATE INDEX idx_job_matches_job_id ON job_matches(job_id);
CREATE INDEX idx_job_matches_score ON job_matches(score DESC);
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_applications_status ON applications(status);

-- Triggers to automatically update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some common skills
INSERT INTO skills (name, category) VALUES
    ('Python', 'programming'),
    ('JavaScript', 'programming'),
    ('TypeScript', 'programming'),
    ('Java', 'programming'),
    ('C++', 'programming'),
    ('React', 'framework'),
    ('Node.js', 'framework'),
    ('Django', 'framework'),
    ('Flask', 'framework'),
    ('Express.js', 'framework'),
    ('PostgreSQL', 'database'),
    ('MongoDB', 'database'),
    ('MySQL', 'database'),
    ('Redis', 'database'),
    ('Docker', 'tool'),
    ('Kubernetes', 'tool'),
    ('AWS', 'cloud'),
    ('Azure', 'cloud'),
    ('GCP', 'cloud'),
    ('Git', 'tool'),
    ('Linux', 'system'),
    ('Agile', 'methodology'),
    ('Scrum', 'methodology'),
    ('Machine Learning', 'domain'),
    ('Data Science', 'domain'),
    ('DevOps', 'domain'),
    ('Frontend Development', 'role'),
    ('Backend Development', 'role'),
    ('Full Stack Development', 'role'),
    ('Software Engineering', 'role')
ON CONFLICT (name) DO NOTHING;
