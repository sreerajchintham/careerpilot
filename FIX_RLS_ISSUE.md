# 🔐 FIX: Row-Level Security (RLS) Policy Violation

## 🐛 The Error

```
APIError: {'message': 'new row violates row-level security policy for table "applications"', 'code': '42501'}
```

## 🔍 Root Cause

The backend is using the **anon key** which is restricted by Supabase's Row-Level Security (RLS) policies. The backend needs the **service role key** to bypass RLS and perform admin operations.

## ✅ Solution: Get and Set Service Role Key

### **Step 1: Get Your Service Role Key from Supabase**

1. Go to your Supabase project dashboard
2. Click on **Settings** (gear icon in sidebar)
3. Click on **API** in the left menu
4. Scroll down to **Project API keys**
5. Copy the **`service_role`** key (it's the secret one, marked as "secret")

⚠️ **IMPORTANT**: Never commit this key to git! It has full database access.

### **Step 2: Update Your .env File**

Open `backend/.env` and replace the placeholder:

**Before:**
```bash
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

**After:**
```bash
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxicHZudG1neXpvdWN2cGJmdnhhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTc3NTE2NCwiZXhwIjoyMDc1MzUxMTY0fQ.YOUR_ACTUAL_SERVICE_ROLE_KEY_HERE
```

### **Step 3: Restart the Backend**

```bash
cd backend
# Kill the existing process
pkill -f "uvicorn app.main:app"

# Start fresh
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
✅ Supabase client initialized with service role key (full access)
```

Instead of:
```
⚠️  Supabase client initialized with anon key (limited by RLS)
```

## 🎯 What Changed in the Code

**File: `backend/app/main.py` (Lines 49-64)**

**Before:**
```python
supabase_key = os.getenv('SUPABASE_ANON_KEY')  # ❌ Limited by RLS
```

**After:**
```python
# Use service role key for backend operations (bypasses RLS)
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
    logger.info("✅ Supabase client initialized with service role key (full access)")
else:
    logger.warning("⚠️  Supabase client initialized with anon key (limited by RLS)")
```

## 📊 Key Differences

| Key Type | Purpose | RLS | Use Case |
|----------|---------|-----|----------|
| **Anon Key** | Public, client-side | ✅ Enforced | Frontend, user queries |
| **Service Role Key** | Secret, server-side | ❌ Bypassed | Backend, admin operations |

## 🔒 Security Best Practices

1. **Never expose service role key to frontend**
2. **Never commit it to git** (add to .gitignore)
3. **Use anon key for frontend** (already done in `frontend/.env.local`)
4. **Use service role key only in backend** (secured on server)

## ✅ Verification

After restarting the backend with the correct key:

1. Go to **Job Scraping page**
2. Click **"Queue for Application"**
3. Should now work! ✅

Check backend logs:
```
✅ Supabase client initialized with service role key (full access)
Queueing 1 applications for user ...
POST /queue-applications HTTP/1.1" 200 OK  ✅
```

## 🎯 Why This Happened

The backend was trying to **insert** rows into the `applications` table, but:
- Using **anon key** = user-level permissions
- RLS policies require proper authentication
- Backend needs **admin access** = service role key

Now the backend has full access to perform all database operations! 🎉

