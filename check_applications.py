import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

# Check applications
response = supabase.table('applications').select('id, status, created_at, updated_at, attempt_meta').order('created_at', desc=True).limit(10).execute()

print("\n📋 Recent Applications:")
print("=" * 80)
for app in response.data:
    print(f"ID: {app['id']}")
    print(f"Status: {app['status']}")
    print(f"Created: {app['created_at']}")
    print(f"Updated: {app['updated_at']}")
    print(f"Attempt Meta: {app.get('attempt_meta', 'None')}")
    print("-" * 80)

# Count by status
status_response = supabase.table('applications').select('status').execute()
from collections import Counter
status_counts = Counter([a['status'] for a in status_response.data])
print(f"\n📊 Status Counts:")
for status, count in status_counts.items():
    print(f"  {status}: {count}")
