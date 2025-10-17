# Resume Drafting System - Test Plan

## Pre-requisites

1. **Backend Running**: Ensure FastAPI backend is running on port 8000
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend Running**: Ensure Next.js frontend is running
   ```bash
   cd frontend
   npm run dev
   ```

3. **Database Migration**: Ensure `004_add_resumes_table.sql` is applied
   - Go to Supabase Dashboard → SQL Editor
   - Run the migration script

4. **Test Data**:
   - At least one resume uploaded
   - At least one job in the database
   - User logged in

## Test Cases

### Test 1: Page Load
**Steps**:
1. Navigate to `/dashboard/drafts`
2. Observe page loads

**Expected Results**:
- ✅ Dark futuristic theme displayed
- ✅ "RESUME DRAFTING" header with gradient
- ✅ Empty drafts list or existing drafts shown
- ✅ "NEW" button visible
- ✅ No console errors

### Test 2: Auto-load Resume
**Steps**:
1. Open drafts page
2. Click "NEW" button

**Expected Results**:
- ✅ Draft editor opens
- ✅ Resume text auto-populated (if resume exists)
- ✅ Edit mode activated
- ✅ "SAVE" button visible

### Test 3: Job Selection
**Steps**:
1. Create new draft or edit existing
2. Scroll to "AI SUGGESTIONS" section
3. Click job dropdown

**Expected Results**:
- ✅ Dropdown populates with jobs
- ✅ Format: "Title at Company"
- ✅ Can select a job
- ✅ "GET SUGGESTIONS" button becomes enabled

### Test 4: Generate Suggestions
**Steps**:
1. Select a job from dropdown
2. Click "GET SUGGESTIONS"
3. Wait for response

**Expected Results**:
- ✅ Button shows "GENERATING..." with spinner
- ✅ Success toast appears
- ✅ Suggestions list populates
- ✅ Each suggestion shows confidence level (HIGH/MED/LOW)
- ✅ Color-coded badges (green/yellow/orange)

### Test 5: Preview Changes
**Steps**:
1. Generate suggestions (Test 4)
2. Click "PREVIEW CHANGES" button

**Expected Results**:
- ✅ ResumeDiffModal opens
- ✅ Left pane shows original resume
- ✅ Right pane shows modified resume
- ✅ Bottom panel shows suggestions with checkboxes
- ✅ Can check/uncheck suggestions
- ✅ Preview updates when toggling suggestions

### Test 6: Save from Modal
**Steps**:
1. Open preview modal (Test 5)
2. Select some suggestions
3. Click "Save as Draft"

**Expected Results**:
- ✅ "Saving..." indicator appears
- ✅ Success message displays
- ✅ Modal closes after 2 seconds
- ✅ Draft appears in sidebar
- ✅ API call to `/save-resume-draft` succeeds (check Network tab)

### Test 7: Apply Suggestions Inline
**Steps**:
1. Generate suggestions
2. Check some suggestions
3. Click "APPLY X SELECTED SUGGESTIONS"

**Expected Results**:
- ✅ Suggestions appended to resume text
- ✅ Text area updates
- ✅ Success toast appears
- ✅ Selected suggestions cleared

### Test 8: Save Draft
**Steps**:
1. Edit resume text or apply suggestions
2. Click "SAVE" button

**Expected Results**:
- ✅ Success toast appears
- ✅ Draft appears/updates in sidebar
- ✅ Edit mode exits
- ✅ Draft ID generated or updated

### Test 9: Load Draft
**Steps**:
1. Create and save a draft (Test 8)
2. Click on draft in sidebar

**Expected Results**:
- ✅ Draft content loads in editor
- ✅ View mode activated (not edit mode)
- ✅ Draft highlighted in sidebar
- ✅ Content matches saved version

### Test 10: Delete Draft
**Steps**:
1. Create a draft
2. Click trash icon next to draft

**Expected Results**:
- ✅ Draft disappears from list
- ✅ Success toast appears
- ✅ If currently selected, editor clears
- ✅ Database record deleted

## API Endpoint Tests

### Test 11: GET `/user/{user_id}/resume`
```bash
curl http://localhost:8000/user/{USER_ID}/resume
```
**Expected**:
- 200 OK
- JSON with resume object including `text` and `parsed` fields

### Test 12: POST `/propose-resume`
```bash
curl -X POST http://localhost:8000/propose-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "{JOB_ID}",
    "resume_text": "Sample resume text..."
  }'
```
**Expected**:
- 200 OK
- JSON with `suggestions` array
- Each suggestion has `text` and `confidence` fields

### Test 13: POST `/save-resume-draft`
```bash
curl -X POST http://localhost:8000/save-resume-draft \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "{USER_ID}",
    "resume_text": "Modified resume...",
    "applied_suggestions": []
  }'
```
**Expected**:
- 200 OK
- JSON with `draft_id` and success message

### Test 14: GET `/user/{user_id}/drafts`
```bash
curl http://localhost:8000/user/{USER_ID}/drafts
```
**Expected**:
- 200 OK
- JSON with `drafts` array

## Error Handling Tests

### Test 15: No Job Selected
**Steps**:
1. Open drafts page
2. Click "GET SUGGESTIONS" without selecting job

**Expected**:
- ✅ Error toast: "Please select a job and enter resume text"
- ✅ No API call made

### Test 16: Empty Resume Text
**Steps**:
1. Clear resume text
2. Select job
3. Click "GET SUGGESTIONS"

**Expected**:
- ✅ Error toast displayed
- ✅ No API call made

### Test 17: API Failure
**Steps**:
1. Stop backend server
2. Try to get suggestions

**Expected**:
- ✅ Error toast with failure message
- ✅ Loading state clears
- ✅ No crash or infinite loading

## Performance Tests

### Test 18: Large Resume
**Steps**:
1. Load resume with 3000+ words
2. Generate suggestions
3. Apply suggestions

**Expected**:
- ✅ No lag in UI
- ✅ Suggestions generate within 5 seconds
- ✅ Text area remains responsive

### Test 19: Multiple Drafts
**Steps**:
1. Create 10+ drafts
2. Navigate between them

**Expected**:
- ✅ Sidebar scrolls smoothly
- ✅ Loading is instant
- ✅ No memory leaks

## Integration Tests

### Test 20: Full Workflow
**Steps**:
1. Upload resume
2. Scrape jobs
3. Go to drafts
4. Create new draft (auto-loads resume)
5. Select job (from scraped list)
6. Generate suggestions
7. Preview changes in modal
8. Select suggestions
9. Save draft
10. Load saved draft
11. Apply more suggestions
12. Save again

**Expected**:
- ✅ All steps complete without errors
- ✅ Data persists correctly
- ✅ UI updates appropriately
- ✅ Toast notifications at each step

## Browser Compatibility

- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Mobile Responsiveness

- [ ] iPhone (portrait)
- [ ] iPhone (landscape)
- [ ] iPad (portrait)
- [ ] iPad (landscape)
- [ ] Android phone
- [ ] Android tablet

## Known Limitations

1. **PDF Generation**: Currently doesn't generate PDF from modified text
2. **Section-specific editing**: Appends suggestions rather than inserting intelligently
3. **Real-time collaboration**: Not supported
4. **Version history**: No git-like diff tracking

## Success Criteria

For the Resume Drafting System to be considered **PRODUCTION READY**:

- [ ] All Test Cases 1-20 pass
- [ ] No critical bugs or crashes
- [ ] Performance acceptable (< 3s for suggestion generation)
- [ ] Data persistence works reliably
- [ ] Error handling covers all edge cases
- [ ] UI/UX matches design system
- [ ] Mobile responsive
- [ ] Tested on 2+ browsers

## Bug Report Template

If you find issues, report them with:

```markdown
**Test Case**: #X - [Name]
**Steps to Reproduce**:
1. Step 1
2. Step 2

**Expected**: What should happen
**Actual**: What actually happened
**Console Errors**: [Paste any errors]
**Screenshots**: [If applicable]
**Browser**: Chrome 120 / Firefox 115 / etc.
**Priority**: Critical / High / Medium / Low
```

## Next Steps After Testing

1. Document any bugs found
2. Fix critical issues
3. Move to Priority 2: Fix Worker System
4. Iterate based on user feedback

