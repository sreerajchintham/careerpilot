#!/usr/bin/env python3
"""
Check Database Schema - Diagnostic script to verify database structure
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv('backend/.env')

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 80)
print("DATABASE SCHEMA DIAGNOSTIC")
print("=" * 80)

# Check if users table exists and what columns it has
try:
    print("\n1️⃣  Checking 'users' table structure...")
    result = supabase.table('users').select('*').limit(1).execute()
    
    if result.data:
        print("✅ 'users' table exists")
        print("\n   Sample row keys:")
        for key in result.data[0].keys():
            print(f"   - {key}")
        
        # Check if drafts column exists
        if 'drafts' in result.data[0]:
            print("\n✅ 'drafts' column EXISTS in users table")
            print(f"   Value: {result.data[0]['drafts']}")
        else:
            print("\n❌ 'drafts' column MISSING from users table")
            print("\n   ⚠️  You need to run migration 002:")
            print("      migrations/002_add_drafts_to_users.sql")
    else:
        print("⚠️  'users' table is empty (no rows to check structure)")
except Exception as e:
    print(f"❌ Error checking users table: {e}")

# Check if RPC functions exist
print("\n2️⃣  Checking RPC functions...")

functions_to_check = [
    'add_user_draft',
    'get_user_drafts',
    'get_user_draft',
    'delete_user_draft'
]

for func_name in functions_to_check:
    try:
        # Try to call the function with dummy data
        # This will fail if function doesn't exist
        result = supabase.rpc(func_name, {}).execute()
        print(f"✅ '{func_name}' function exists")
    except Exception as e:
        if "function" in str(e).lower() and "does not exist" in str(e).lower():
            print(f"❌ '{func_name}' function MISSING")
        else:
            # Function exists but failed due to invalid params (expected)
            print(f"✅ '{func_name}' function exists (failed with: {type(e).__name__})")

# Check all tables
print("\n3️⃣  Checking all tables...")
tables = ['users', 'jobs', 'applications', 'resumes', 'skills', 'job_matches']

for table in tables:
    try:
        result = supabase.table(table).select('*').limit(1).execute()
        count_result = supabase.table(table).select('id', count='exact').execute()
        row_count = count_result.count if hasattr(count_result, 'count') else 'unknown'
        print(f"✅ '{table}' table exists ({row_count} rows)")
    except Exception as e:
        print(f"❌ '{table}' table MISSING or error: {e}")

# Summary and recommendations
print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

print("""
If 'drafts' column is MISSING:
  1. Go to Supabase Dashboard > SQL Editor
  2. Run: migrations/002_add_drafts_to_users.sql
  3. This will add the drafts column and RPC functions

If RPC functions are MISSING:
  - Same as above - migration 002 creates them

The code now has FALLBACK logic:
  - Tries RPC functions first (faster, cleaner)
  - Falls back to direct queries if RPC not available
  - Your app will work either way!
""")

print("=" * 80)

