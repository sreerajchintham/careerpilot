# Database Setup Instructions

This guide will help you set up the database for CareerPilot Agent using Supabase.

## Prerequisites

1. **Supabase Account**: Create a free account at [supabase.com](https://supabase.com)
2. **Node.js**: Install Node.js (version 16 or higher)

## Step 1: Create Supabase Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose your organization
4. Enter project details:
   - **Name**: `careerpilot-agent`
   - **Database Password**: Choose a strong password
   - **Region**: Select closest to your location
5. Click "Create new project"
6. Wait for the project to be created (2-3 minutes)

## Step 2: Run Database Migration

1. In your Supabase dashboard, go to the **SQL Editor**
2. Click "New Query"
3. Copy the contents of `migrations/001_initial.sql`
4. Paste it into the SQL editor
5. Click "Run" to execute the migration
6. Verify that the tables were created in the **Table Editor**

## Step 3: Get Supabase Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (looks like: `https://your-project-id.supabase.co`)
   - **anon public** key (starts with `eyJ...`)

## Step 4: Set Up Environment Variables

1. In the `backend/` directory, copy the example environment file:
   ```bash
   cd backend
   cp env.example .env
   ```

2. Edit `.env` and replace the placeholder values:
   ```bash
   # Replace with your actual Supabase values
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## Step 5: Install Dependencies and Seed Data

1. Install Node.js dependencies:
   ```bash
   cd backend
   npm install
   ```

2. Run the seed script to populate the jobs table:
   ```bash
   npm run seed
   ```

   You should see output like:
   ```
   🚀 CareerPilot Job Seeding Script
   ==================================
   
   🔍 Verifying database connection...
   ✅ Database connection successful!
   🌱 Starting job seeding process...
   📄 Loaded 10 sample jobs from sample_jobs.json
   ✅ Successfully inserted jobs:
      - Senior Software Engineer - Full Stack at TechCorp Inc. (ID: ...)
      - Frontend Developer - React Specialist at StartupXYZ (ID: ...)
      ...
   🎉 Seeding completed! Inserted 10 jobs into the database.
   ```

## Step 6: Verify Setup

1. Go to your Supabase dashboard → **Table Editor**
2. Check that the following tables exist:
   - `users`
   - `skills` (should have 30 pre-populated skills)
   - `jobs` (should have 10 sample jobs)
   - `job_matches`
   - `applications`

## Troubleshooting

### Common Issues:

1. **"Missing Supabase credentials" error**:
   - Make sure you created the `.env` file in the `backend/` directory
   - Verify the environment variable names are correct
   - Check that the values don't have extra spaces or quotes

2. **"Database connection failed" error**:
   - Verify your Supabase URL and key are correct
   - Make sure you ran the migration first
   - Check that your Supabase project is active

3. **"Table doesn't exist" error**:
   - Run the migration file `migrations/001_initial.sql` in Supabase SQL Editor
   - Make sure the migration completed successfully

4. **Permission errors**:
   - The anon key should have read/write access to the tables
   - Check your Supabase RLS (Row Level Security) policies if you have any

### Getting Help:

- Check the [Supabase Documentation](https://supabase.com/docs)
- Visit the [Supabase Discord](https://discord.supabase.com) for community support
- Review the seed script logs for specific error messages

## Next Steps

Once the database is set up:

1. **Test the API**: Start your FastAPI server and test the endpoints
2. **Connect Frontend**: Update your frontend to use the database
3. **Add More Data**: Use the Supabase dashboard to add more jobs or users
4. **Set Up Authentication**: Configure user authentication if needed

## Database Schema Overview

- **users**: Store user profiles and parsed resume data
- **skills**: Normalized skills for better job matching
- **jobs**: Job postings from various sources
- **job_matches**: Matching scores between users and jobs
- **applications**: Track user applications to jobs

The schema includes proper indexes, foreign key constraints, and triggers for automatic timestamp updates.
