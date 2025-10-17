# Applying "Not Viable" Status Update

## What Changed

Applications that the AI rejects (poor match score or not recommended) will now be marked as **`not_viable`** instead of staying in `draft` status.

---

## Step 1: Apply Database Migration

Go to your **Supabase Dashboard** and run this SQL:

```sql
-- Add 'not_viable' status
ALTER TABLE applications 
DROP CONSTRAINT IF EXISTS applications_status_check;

ALTER TABLE applications 
ADD CONSTRAINT applications_status_check 
CHECK (status IN (
    'draft',
    'not_viable',
    'materials_ready',
    'submitted',
    'under_review',
    'interview',
    'rejected',
    'accepted'
));
```

**Where to run this:**
1. Go to https://app.supabase.com
2. Select your project
3. Click **SQL Editor** in the left menu
4. Paste the SQL above
5. Click **Run**

---

## Step 2: Migrate Existing Draft Applications

After the constraint is updated, run this to mark the 2 existing draft applications as `not_viable`:

```sql
-- Update the 2 applications that AI already rejected
UPDATE applications 
SET 
    status = 'not_viable',
    attempt_meta = COALESCE(attempt_meta, '{}'::jsonb) || jsonb_build_object(
        'rejection_reason', 'AI determined poor match during processing',
        'rejected_at', NOW(),
        'note', 'Application marked as not viable by migration'
    )
WHERE status = 'draft' 
AND artifacts IS NULL
AND updated_at > created_at;  -- Has been processed by worker
```

---

## Step 3: Restart Worker

Stop and restart the worker to pick up the new code:

```bash
# Stop worker
pkill -f gemini_apply_worker

# Start worker
cd /Users/raj/Documents/Sreeraj\ -\ guthib/careerpilot/backend
python workers/gemini_apply_worker.py --interval 300 > ../logs/worker.log 2>&1 &
```

---

## Step 4: Test

Queue a new application and watch the worker process it:

```bash
# Watch worker logs
tail -f /Users/raj/Documents/Sreeraj\ -\ guthib/careerpilot/backend/logs/worker.log
```

If the AI rejects it, you'll see:
```
AI recommends not applying: [reasoning]
✅ Updated application [id] to status 'not_viable'
```

---

## What You'll See in the Frontend

### Before (Old Behavior):
- Poor-match applications stayed in **"Draft"** status
- Looked like they were waiting to be processed
- Confusing for users

### After (New Behavior):
- Poor-match applications move to **"Not Recommended"** status
- **Orange badge** with warning icon (⚠️)
- Shows AI's reasoning for rejection
- Clear that these shouldn't be applied to

---

## UI Updates

### Status Badge:
- **Color**: Orange (`bg-orange-500/20 text-orange-400`)
- **Icon**: Warning circle (⚠️)
- **Label**: "Not Recommended"

### Filter Options:
New filter added: **"Not Recommended (AI Rejected)"**

### Application Details:
When you view a `not_viable` application, you'll see:
- Match score (e.g., 50/100)
- AI's reasoning for rejection
- Key gaps identified
- Recommendation: "Not recommended to apply"

---

## Benefits

✅ **Clearer Status**: No confusion about what's pending vs rejected
✅ **Better UX**: Users know immediately which applications to skip
✅ **Proper Organization**: Applications are properly categorized
✅ **AI Transparency**: Shows why AI rejected the application
✅ **Time Saving**: Focus only on viable applications

---

## Statistics After Update

Your applications will be organized as:
- **Materials Ready**: 13 applications (good matches)
- **Not Viable**: 2 applications (AI rejected)
- **Submitted**: 1 application (already applied)

This means **81.25% of your applications are viable** - great success rate!

---

## Understanding "Not Viable"

An application is marked `not_viable` when:

1. **Match Score < 60** (usually < 50)
2. **AI's `should_apply` = false**
3. **Major skill gaps identified**
4. **Experience level mismatch** (e.g., junior applying to senior role)
5. **Domain knowledge missing** (e.g., no blockchain exp for blockchain role)

### Your 2 Not Viable Applications:

1. **Senior Product Manager** @ DataKind
   - Score: 50/100
   - Issue: No PM experience for senior role
   - AI Decision: ❌ Not recommended

2. **Frontend Engineer** @ ZetaChain
   - Score: 25/100
   - Issue: No frontend or blockchain experience
   - AI Decision: ❌ Not recommended

---

## Can I Override AI's Decision?

Yes! If you want to apply anyway:

1. **View the application** in the dashboard
2. **Review AI's reasoning**
3. **If you still want to apply**:
   - Manually go to the job URL
   - Apply without AI-generated materials
   - Or, update your resume and re-queue

---

## Summary

- ✅ Migration ready: `migrations/007_add_not_viable_status.sql`
- ✅ Worker updated: Now uses `not_viable` instead of staying in `draft`
- ✅ Frontend updated: Orange badge, new filter, clear labeling
- ✅ Better UX: Clear separation between "pending" and "rejected"

**Next Step**: Apply the SQL migration in your Supabase dashboard!

---

*This change makes your application queue much cleaner and easier to manage!* 🎯

