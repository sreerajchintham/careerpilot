-- Migration: 002_add_drafts_to_users.sql
-- Description: Add drafts column to users table for resume draft storage
-- Created: 2025-01-06

-- Add drafts column to users table
-- This will store an array of resume drafts as JSONB
ALTER TABLE users ADD COLUMN drafts JSONB DEFAULT '[]'::jsonb;

-- Add index on drafts for better query performance
CREATE INDEX idx_users_drafts ON users USING GIN (drafts);

-- Add comment to explain the drafts structure
COMMENT ON COLUMN users.drafts IS 'Array of resume drafts stored as JSONB. Each draft contains: {draft_id, resume_text, applied_suggestions, job_context, created_at, word_count, suggestions_count}';

-- Create a function to add a new draft to a user's drafts array
CREATE OR REPLACE FUNCTION add_user_draft(
    p_user_id UUID,
    p_draft_id UUID,
    p_resume_text TEXT,
    p_applied_suggestions JSONB,
    p_job_context JSONB
)
RETURNS VOID AS $$
DECLARE
    new_draft JSONB;
BEGIN
    -- Create the new draft object
    new_draft := jsonb_build_object(
        'draft_id', p_draft_id,
        'resume_text', p_resume_text,
        'applied_suggestions', p_applied_suggestions,
        'job_context', p_job_context,
        'created_at', NOW(),
        'word_count', array_length(string_to_array(p_resume_text, ' '), 1),
        'suggestions_count', jsonb_array_length(p_applied_suggestions)
    );
    
    -- Add the draft to the user's drafts array
    UPDATE users 
    SET drafts = drafts || new_draft
    WHERE id = p_user_id;
    
    -- Update the updated_at timestamp
    UPDATE users 
    SET updated_at = NOW() 
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get a specific draft by draft_id
CREATE OR REPLACE FUNCTION get_user_draft(
    p_user_id UUID,
    p_draft_id UUID
)
RETURNS JSONB AS $$
DECLARE
    draft JSONB;
BEGIN
    -- Extract the draft from the drafts array
    SELECT jsonb_array_elements(drafts) INTO draft
    FROM users 
    WHERE id = p_user_id 
    AND jsonb_array_elements(drafts)->>'draft_id' = p_draft_id::text;
    
    RETURN draft;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get all drafts for a user
CREATE OR REPLACE FUNCTION get_user_drafts(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    user_drafts JSONB;
BEGIN
    SELECT drafts INTO user_drafts
    FROM users 
    WHERE id = p_user_id;
    
    RETURN COALESCE(user_drafts, '[]'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Create a function to delete a specific draft
CREATE OR REPLACE FUNCTION delete_user_draft(
    p_user_id UUID,
    p_draft_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    updated_rows INTEGER;
BEGIN
    -- Remove the draft from the drafts array
    UPDATE users 
    SET drafts = (
        SELECT jsonb_agg(draft)
        FROM jsonb_array_elements(drafts) AS draft
        WHERE draft->>'draft_id' != p_draft_id::text
    )
    WHERE id = p_user_id;
    
    GET DIAGNOSTICS updated_rows = ROW_COUNT;
    
    -- Update the updated_at timestamp if a draft was removed
    IF updated_rows > 0 THEN
        UPDATE users 
        SET updated_at = NOW() 
        WHERE id = p_user_id;
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add some example data for testing (optional)
-- This creates a test user with a sample draft
INSERT INTO users (id, email, profile) VALUES 
(
    '550e8400-e29b-41d4-a716-446655440000',
    'test@example.com',
    '{"name": "Test User", "phone": "(555) 123-4567"}'
) ON CONFLICT (email) DO NOTHING;

-- Add a sample draft to the test user
SELECT add_user_draft(
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    '123e4567-e89b-12d3-a456-426614174000'::UUID,
    'Test User\nSoftware Engineer\nPython, JavaScript, React\n\nExperience:\n- Developed web applications\n- Improved performance by 25%',
    '[{"text": "Add or emphasize: Quantify achievements", "confidence": "high", "applied_text": "Improved performance by 25%"}]'::jsonb,
    '{"job_title": "Backend Engineer", "company": "Test Corp"}'::jsonb
);
