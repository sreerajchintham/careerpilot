#!/usr/bin/env python3
"""
Script to apply the 004_add_resumes_table.sql migration directly to Supabase.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

def run_migration():
    # Load environment variables
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        return
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Read migration file
    with open("migrations/004_add_resumes_table.sql", "r") as f:
        migration_sql = f.read()
    
    print("📋 Running migration 004_add_resumes_table.sql...")
    
    # Execute migration using RPC or direct SQL
    # Note: Supabase Python client doesn't have direct SQL execution
    # You'll need to run this via Supabase Dashboard SQL Editor or use psycopg2
    
    print("""
⚠️  The Python Supabase client doesn't support direct SQL execution.
Please run the migration in one of these ways:

1. Via Supabase Dashboard:
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor
   - Copy and paste the contents of migrations/004_add_resumes_table.sql
   - Click 'Run'

2. Via psql (if you have direct database access):
   psql "$SUPABASE_DB_URL" -f migrations/004_add_resumes_table.sql

3. The migration SQL is:
""")
    print(migration_sql)
    print("\n✅ After running the migration, the resumes table will be ready!")

if __name__ == "__main__":
    run_migration()

