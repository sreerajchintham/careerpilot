-- Migration: 006_add_materials_ready_status.sql
-- Description: Add 'materials_ready' status to applications table
-- Created: 2025-10-17

-- Add 'materials_ready' to the allowed statuses for applications
-- This status indicates AI has generated application materials (cover letter, analysis)
-- but the application has NOT been submitted yet (browser automation pending)

ALTER TABLE applications 
DROP CONSTRAINT IF EXISTS applications_status_check;

ALTER TABLE applications 
ADD CONSTRAINT applications_status_check 
CHECK (status IN (
    'draft',              -- Queued by user, not yet processed
    'materials_ready',    -- AI materials generated, awaiting submission (NEW)
    'submitted',          -- Actually submitted to employer
    'under_review',       -- Employer is reviewing
    'interview',          -- Interview stage
    'rejected',           -- Application rejected
    'accepted'            -- Offer received
));

-- Add comment explaining the new status
COMMENT ON COLUMN applications.status IS 'Application status: draft (queued), materials_ready (AI generated materials, not submitted), submitted (actually applied), under_review, interview, rejected, accepted';

-- Update any existing 'pending' or incorrectly marked applications
-- This is optional - only run if you have existing data with wrong statuses
UPDATE applications 
SET status = 'materials_ready' 
WHERE status NOT IN ('draft', 'materials_ready', 'submitted', 'under_review', 'interview', 'rejected', 'accepted')
AND artifacts IS NOT NULL;

-- Add index for faster filtering by status
CREATE INDEX IF NOT EXISTS idx_applications_status_materials_ready 
ON applications(status) 
WHERE status = 'materials_ready';

-- Summary
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 006 complete: Added materials_ready status';
    RAISE NOTICE '   - Updated status constraint to include materials_ready';
    RAISE NOTICE '   - Added index for materials_ready status';
    RAISE NOTICE '   - This status indicates AI materials are ready but NOT submitted';
END $$;

