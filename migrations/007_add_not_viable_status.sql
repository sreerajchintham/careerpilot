-- Migration: 007_add_not_viable_status.sql
-- Description: Add 'not_viable' status for AI-rejected applications
-- Created: 2025-10-17

-- Add 'not_viable' to the allowed statuses for applications
-- This status indicates the AI analyzed the application and determined it's not a good match

ALTER TABLE applications 
DROP CONSTRAINT IF EXISTS applications_status_check;

ALTER TABLE applications 
ADD CONSTRAINT applications_status_check 
CHECK (status IN (
    'draft',              -- Queued by user, not yet processed by AI
    'not_viable',         -- AI analyzed and rejected (poor match, NEW)
    'materials_ready',    -- AI generated materials, awaiting manual submission
    'submitted',          -- Actually submitted to employer
    'under_review',       -- Employer is reviewing
    'interview',          -- Interview stage
    'rejected',           -- Application rejected by employer (after submission)
    'accepted'            -- Offer received
));

-- Add comment explaining the new status
COMMENT ON COLUMN applications.status IS 
'Application status: 
- draft: Queued, awaiting AI processing
- not_viable: AI rejected (low match score, not recommended)
- materials_ready: AI generated materials, ready for manual submission
- submitted: Actually applied
- under_review: Employer reviewing
- interview: Interview scheduled
- rejected: Rejected by employer
- accepted: Offer received';

-- Update existing skipped applications that are still in draft
-- These are applications the AI has already analyzed and skipped
UPDATE applications 
SET 
    status = 'not_viable',
    attempt_meta = COALESCE(attempt_meta, '{}'::jsonb) || jsonb_build_object(
        'rejection_reason', 'AI determined poor match during processing',
        'rejected_at', NOW()
    )
WHERE status = 'draft' 
AND updated_at < created_at + interval '5 minutes'  -- Has been processed
AND artifacts IS NULL;  -- But no materials were generated

-- Add index for filtering not_viable applications
CREATE INDEX IF NOT EXISTS idx_applications_status_not_viable 
ON applications(status) 
WHERE status = 'not_viable';

-- Summary
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 007 complete: Added not_viable status';
    RAISE NOTICE '   - Updated status constraint to include not_viable';
    RAISE NOTICE '   - Migrated existing skipped applications to not_viable';
    RAISE NOTICE '   - Added index for not_viable status';
    RAISE NOTICE '   - This status indicates AI rejected the application';
END $$;

