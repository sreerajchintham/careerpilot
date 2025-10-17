-- Migration: 004_add_resumes_table.sql
-- Description: Add resumes table to store original PDF, parsed data, and preview

CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_url TEXT, -- storage path to original PDF
    text TEXT, -- extracted text
    html_preview TEXT, -- optional rendered HTML for preview
    parsed JSONB DEFAULT '{}', -- parsed fields from Gemini
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_current ON resumes(user_id, is_current);

-- Ensure one current resume per user by clearing previous flags
CREATE OR REPLACE FUNCTION set_current_resume()
RETURNS TRIGGER AS $$
BEGIN
    -- Set all other resumes for the user to is_current=false
    IF NEW.is_current = TRUE THEN
        UPDATE resumes SET is_current = FALSE 
        WHERE user_id = NEW.user_id AND id <> NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_current_resume ON resumes;
CREATE TRIGGER trg_set_current_resume
BEFORE INSERT OR UPDATE ON resumes
FOR EACH ROW
EXECUTE FUNCTION set_current_resume();

