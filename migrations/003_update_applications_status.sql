-- Migration: 003_update_applications_status.sql
-- Description: Update applications table to include 'pending' and 'applied' statuses
-- Created: 2025-01-06

-- Drop the existing check constraint
ALTER TABLE applications DROP CONSTRAINT IF EXISTS applications_status_check;

-- Add the updated check constraint with new statuses
ALTER TABLE applications ADD CONSTRAINT applications_status_check 
CHECK (status IN ('draft', 'pending', 'submitted', 'under_review', 'interview', 'rejected', 'accepted', 'applied'));

-- Add comment to explain the status workflow
COMMENT ON COLUMN applications.status IS 'Application status workflow: draft -> pending -> applied -> submitted -> under_review -> interview -> accepted/rejected';

-- Update any existing 'pending' status applications to 'draft' if they exist
-- (This shouldn't be necessary since we just added 'pending' support)
-- UPDATE applications SET status = 'draft' WHERE status = 'pending';

-- Add index on status for better query performance
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

-- Add index on user_id and status for worker queries
CREATE INDEX IF NOT EXISTS idx_applications_user_status ON applications(user_id, status);
