# Resume Persistence & Profile Preview Implementation

## Overview
This implementation adds complete resume persistence and profile display functionality to CareerPilot, enabling users to upload resumes that are automatically saved, parsed, and displayed on the home dashboard.

## What Was Implemented

### 1. Database Schema (P0 - Completed)
**File**: `migrations/004_add_resumes_table.sql`

Created a new `resumes` table with:
- `id` (UUID primary key)
- `user_id` (FK to users table)
- `original_url` (storage path for PDF - TODO)
- `text` (full extracted resume text)
- `html_preview` (rendered HTML - TODO)
- `parsed` (JSONB with all parsed fields from Gemini)
- `is_current` (boolean flag)
- `created_at` (timestamp)

**Features**:
- Automatic trigger to ensure only one "current" resume per user
- Indexes for fast lookups by user_id and is_current flag
- Cascade delete on user removal

**Migration Instructions**:
Run via Supabase Dashboard SQL Editor or using the provided `run_migration_004.py` script.

### 2. Backend Endpoints (P0 - Completed)
**File**: `backend/app/main.py`

#### Enhanced `/parse-resume` POST endpoint
- **Before**: Only returned parsed data
- **After**: Now persists resume to database
  - Creates user record if email is found in parsed data
  - Updates user profile with parsed fields
  - Inserts resume row in `resumes` table
  - Links resume to user via email matching

**Key Logic**:
```python
# Extract with pdfplumber → Parse with Gemini AI
# If email found in parsed data:
#   - Check if user exists by email
#   - Create user if missing
#   - Update user.profile with parsed data
#   - Insert resume row (is_current=TRUE triggers the function)
```

#### New `GET /user/{user_id}/profile` endpoint
Returns:
```json
{
  "user": {
    "id": "...",
    "email": "...",
    "profile": { /* parsed fields */ },
    "created_at": "..."
  },
  "latest_resume_id": "..."
}
```

#### New `GET /user/{user_id}/resume` endpoint
Returns:
```json
{
  "resume": {
    "id": "...",
    "user_id": "...",
    "original_url": null,
    "text": "full resume text...",
    "html_preview": null,
    "parsed": { /* all 9 Gemini fields */ },
    "is_current": true,
    "created_at": "..."
  }
}
```

### 3. Frontend API Client (P0 - Completed)
**File**: `frontend/lib/api.ts`

Added two new methods:
- `getUserProfile(userId: string)`: Fetches user profile + latest resume ID
- `getLatestResume(userId: string)`: Fetches full resume details

### 4. Home Dashboard Profile Display (P0 - Completed)
**File**: `frontend/pages/dashboard/index.tsx`

**New Features**:
- Fetches profile and resume on page load
- Displays profile card with:
  - Name, Email, Phone
  - Current Title, Location
  - Top 6 skills (with "+X more" indicator)
  - Edit link to resume page
- Displays resume preview card with:
  - Last updated date
  - Professional summary (line-clamped to 4 lines)
  - First 500 chars of resume text in monospace preview
  - View Full link
- Empty state with "Upload Resume" CTA if no profile exists
- Responsive grid layout (stacks on mobile, side-by-side on desktop)

## Workflow

### Happy Path
1. User uploads PDF via `/dashboard/resume`
2. Backend extracts text with pdfplumber
3. Gemini AI parses 9 fields (name, email, phone, skills, etc.)
4. If email found:
   - User record created/updated with profile
   - Resume row inserted with `is_current=TRUE`
5. Home dashboard automatically fetches and displays:
   - Profile info in left card
   - Resume preview in right card

### Edge Cases Handled
- **No email in resume**: Resume saved but not linked to user (uses placeholder UUID)
- **User doesn't exist**: Auto-created with email from parsed data
- **Multiple resumes**: Trigger ensures only latest is marked `is_current`
- **No profile yet**: Shows empty state with upload CTA

## What's Still TODO (P1/P2)

### P1 - Next Priorities
1. **PDF Storage**: Upload original PDF to Supabase Storage
   - Save path in `resumes.original_url`
   - Enable download/view of original formatting
2. **HTML Preview Generation**: Server-side HTML rendering
   - Option 1: Simple HTML from text
   - Option 2: pdf2htmlEX for layout preservation
   - Option 3: Frontend PDF.js viewer
3. **Job Matching Integration**: Compute embeddings on resume save
   - Call Gemini embedding API for `resumes.text`
   - Store in separate `embeddings` table or in `resumes.raw`
   - Auto-match against job embeddings after scraping

### P2 - Future Enhancements
1. **Editable Resume Builder**: In-app WYSIWYG editor
   - TipTap/ProseMirror for structured editing
   - Export tailored versions per job application
2. **Profile Edit Form**: Dedicated UI to update profile fields
   - POST endpoint to save changes
   - Validation and error handling
3. **Resume History**: View/restore previous versions
   - List all resumes where `user_id` matches
   - Toggle `is_current` flag

## Testing

### Manual Testing Steps
1. **Upload a resume**:
   - Go to `/dashboard/resume`
   - Upload a PDF with email visible
   - Verify "Resume parsed successfully" message shows all 9 fields
   - Check browser console for no errors

2. **Check persistence**:
   - Run query in Supabase Dashboard:
     ```sql
     SELECT * FROM resumes ORDER BY created_at DESC LIMIT 1;
     ```
   - Verify `text`, `parsed`, and `is_current=true`

3. **View on home dashboard**:
   - Navigate to `/dashboard`
   - Verify profile card shows parsed info
   - Verify resume preview shows summary and text snippet
   - Click "Edit →" and "View Full →" links

4. **Empty state**:
   - Use a different user with no resume
   - Verify "NO PROFILE YET" empty state
   - Click "Upload Resume" button

### Backend API Testing
```bash
# Test profile endpoint
curl http://localhost:8000/user/{USER_ID}/profile

# Test resume endpoint
curl http://localhost:8000/user/{USER_ID}/resume
```

## Database Migration Instructions

### Option 1: Supabase Dashboard (Recommended)
1. Go to your Supabase project
2. Navigate to **SQL Editor**
3. Copy contents of `migrations/004_add_resumes_table.sql`
4. Paste and click **Run**
5. Verify in **Table Editor** that `resumes` table exists

### Option 2: Using run_migration_004.py
```bash
cd /path/to/careerpilot
python run_migration_004.py
# Follow the printed instructions
```

### Option 3: Direct psql (if you have DB URL)
```bash
psql "$SUPABASE_DB_URL" -f migrations/004_add_resumes_table.sql
```

## Architecture Notes

### Why Email-Based User Linking?
Since `/parse-resume` doesn't have auth context (it's a file upload), we use the email extracted from the resume to find/create the user. This works well for:
- First-time uploads (creates user)
- Subsequent uploads (updates profile)
- Multi-device uploads (same user identified by email)

**Future**: Add user_id as query param or auth header for explicit linking.

### Why Separate Profile and Resume?
- `users.profile` (JSONB): Quick access to latest parsed fields
- `resumes` table: Full history of all uploaded resumes
- This allows versioning while keeping profile lookup fast

### Trigger vs Application Logic?
The `set_current_resume()` trigger ensures data integrity at the database level, preventing race conditions if multiple uploads happen simultaneously.

## Related Files
- `backend/app/main.py`: All API endpoints
- `frontend/lib/api.ts`: API client functions
- `frontend/pages/dashboard/index.tsx`: Home dashboard
- `frontend/pages/dashboard/resume.tsx`: Upload page
- `migrations/004_add_resumes_table.sql`: Database schema
- `run_migration_004.py`: Migration helper script

## Summary of Changes
- ✅ Created `resumes` table with trigger
- ✅ Enhanced `/parse-resume` to persist data
- ✅ Added `/user/{id}/profile` endpoint
- ✅ Added `/user/{id}/resume` endpoint
- ✅ Updated frontend API client
- ✅ Redesigned home dashboard with profile & resume preview
- ✅ Added empty state for new users
- ✅ Maintained dark futuristic theme
- ✅ Responsive layout (mobile + desktop)

**Total Files Modified**: 5
**Total Lines Added**: ~300
**New Database Tables**: 1

All P0 priorities from the brainstorm are now complete! 🎉

