# 🚀 CareerPilot Frontend-Backend Integration Setup

## 📋 **Complete Setup Guide**

### **Prerequisites**
- Node.js 18+ installed
- Python 3.8+ installed
- Supabase account and project
- Google Gemini API key

---

## 🔧 **Backend Setup**

### **1. Install Backend Dependencies**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Note**: If you encounter dependency conflicts with httpx, the requirements.txt has been configured to use compatible versions. If you still see conflicts, you can ignore the `supafunc` warning as it doesn't affect functionality.

### **2. Configure Environment Variables**
Create `backend/.env` file:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Google Gemini Configuration (required for AI agent)
GEMINI_API_KEY=your_gemini_api_key

# Worker Configuration
WORKER_HEADLESS=false
WORKER_MAX_APPLICATIONS_PER_RUN=5
WORKER_INTERVAL=3600
WORKER_RATE_LIMIT=10

# Application Settings
AUTO_APPLY_ENABLED=false
REQUIRE_MANUAL_REVIEW=true
MIN_MATCH_SCORE=70
```

### **3. Run Database Migrations**
```bash
cd backend
python run_migration.py
```

### **4. Start Backend Server**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🎨 **Frontend Setup**

### **1. Install Frontend Dependencies**
```bash
cd frontend
npm install
```

### **2. Configure Environment Variables**
Create `frontend/.env.local` file:
```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### **3. Start Frontend Development Server**
```bash
cd frontend
npm run dev
```

---

## 🗄️ **Database Setup**

### **1. Enable Supabase Auth**
In your Supabase dashboard:
1. Go to Authentication → Settings
2. Enable Email authentication
3. Configure site URL: `http://localhost:3000`

### **2. Set up Row Level Security (RLS)**
Run these SQL commands in Supabase SQL Editor:

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_matches ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid() = id);

-- Applications are user-specific
CREATE POLICY "Users can view own applications" ON applications
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own applications" ON applications
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own applications" ON applications
  FOR UPDATE USING (auth.uid() = user_id);

-- Job matches are user-specific
CREATE POLICY "Users can view own job matches" ON job_matches
  FOR SELECT USING (auth.uid() = user_id);

-- Jobs are public (read-only for users)
CREATE POLICY "Anyone can view jobs" ON jobs
  FOR SELECT USING (true);
```

---

## 🚀 **Getting Started**

### **1. Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### **2. Create Your Account**
1. Go to http://localhost:3000
2. Click "Create Account" on the login page
3. Enter your email and password
4. Check your email for verification link
5. Verify your account

### **3. Complete Your Profile**
1. Go to Dashboard → Resume Upload
2. Upload your resume (PDF)
3. Edit your profile information
4. Add skills and experience

### **4. Start Job Hunting**
1. Go to Dashboard → Job Scraping
2. Configure search parameters
3. Click "Start Scraping" to find jobs
4. Review found jobs and queue applications
5. Go to Dashboard → Applications to manage your applications
6. Use the AI worker to process applications

---

## 🔄 **Complete Workflow**

### **1. Job Discovery**
```bash
# Backend: Fetch jobs from APIs
cd backend
python workers/api_job_fetcher.py fetch --keywords "Software Engineer" --api all
```

### **2. Generate Embeddings**
```bash
# Backend: Generate embeddings for semantic search
python embeddings_gemini.py --input supabase
```

### **3. Frontend: Match Jobs**
1. Go to Dashboard → Job Scraping
2. View available jobs
3. Queue jobs for application

### **4. AI Processing**
```bash
# Backend: Process applications with AI
python workers/gemini_apply_worker.py run_once
```

### **5. Frontend: Manage Applications**
1. Go to Dashboard → Applications
2. View application status
3. Review AI-generated cover letters
4. Track application progress

---

## 🛠️ **Development Commands**

### **Backend**
```bash
# Start backend server
uvicorn app.main:app --reload

# Run job fetcher
python workers/api_job_fetcher.py fetch --keywords "Python Developer"

# Generate embeddings
python embeddings_gemini.py --input supabase

# Run AI worker
python workers/gemini_apply_worker.py run_once

# Run migrations
python run_migration.py
```

### **Frontend**
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Supabase Connection Error**
   - Check your SUPABASE_URL and SUPABASE_ANON_KEY
   - Ensure RLS policies are set up correctly

2. **Gemini API Error**
   - Verify your GEMINI_API_KEY is correct
   - Check API quota limits

3. **Frontend Build Errors**
   - Run `npm install` to ensure all dependencies are installed
   - Check for TypeScript errors

4. **Backend Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

### **Logs and Debugging**
- Backend logs: Check terminal where uvicorn is running
- Frontend logs: Check browser console
- Database logs: Check Supabase dashboard

---

## 📚 **API Endpoints**

### **Authentication**
- `POST /auth/signup` - Create account
- `POST /auth/signin` - Sign in
- `POST /auth/signout` - Sign out

### **Resume Management**
- `POST /upload-resume` - Upload PDF resume
- `POST /parse-resume` - Parse resume text
- `POST /save-resume-draft` - Save resume draft
- `GET /user/{user_id}/drafts` - Get user drafts

### **Job Management**
- `POST /match-jobs` - Find matching jobs
- `POST /queue-applications` - Queue jobs for application
- `GET /applications` - Get user applications

### **AI Features**
- `POST /propose-resume` - Get AI resume suggestions
- Worker processes applications automatically

---

## 🎯 **Next Steps**

1. **Customize Job Sources**: Add more job APIs
2. **Enhance AI Features**: Improve matching algorithms
3. **Add Notifications**: Email/SMS alerts for new jobs
4. **Analytics Dashboard**: Track application success rates
5. **Mobile App**: React Native version

---

## 📞 **Support**

If you encounter any issues:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Ensure all environment variables are set correctly
4. Verify database migrations have run successfully

**Happy job hunting! 🚀**
