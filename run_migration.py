#!/usr/bin/env python3
"""
Migration runner for Supabase database.

This script helps you apply the migration to add the drafts column to the users table.
"""

import os
import subprocess
import sys

def run_migration():
    """Run the migration to add drafts column to users table."""
    
    print("🗄️ Running Supabase Migration")
    print("=" * 40)
    
    # Check if migration file exists
    migration_file = "migrations/002_add_drafts_to_users.sql"
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Found migration file: {migration_file}")
    
    # Read the migration content
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("✅ Migration file loaded successfully")
        print(f"📊 Migration size: {len(migration_sql)} characters")
        
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")
        return False
    
    print("\n🔧 Migration Instructions:")
    print("=" * 40)
    print("To apply this migration to your Supabase database:")
    print()
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to the SQL Editor")
    print("3. Copy and paste the migration SQL below")
    print("4. Click 'Run' to execute the migration")
    print()
    print("Alternatively, if you have psql configured:")
    print(f"   psql -h [your-host] -U [your-user] -d [your-db] -f {migration_file}")
    print()
    
    print("📋 Migration SQL:")
    print("=" * 40)
    print(migration_sql)
    print("=" * 40)
    
    print("\n✅ Migration SQL ready to apply!")
    print("\n🎯 What this migration does:")
    print("- Adds a 'drafts' JSONB column to the users table")
    print("- Creates indexes for better query performance")
    print("- Adds helper functions for draft management")
    print("- Includes sample data for testing")
    print()
    print("⚠️  Important:")
    print("- Backup your database before running this migration")
    print("- Test in a development environment first")
    print("- The migration includes sample data that you can remove")
    
    return True

def check_supabase_config():
    """Check if Supabase configuration is available."""
    
    print("\n🔍 Checking Supabase Configuration")
    print("=" * 40)
    
    # Check for .env file in backend directory
    env_file = "backend/.env"
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    found_vars = []
    
    if os.path.exists(env_file):
        print("✅ Found .env file")
        
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
                
            for var in required_vars:
                if var in env_content:
                    found_vars.append(var)
                    print(f"✅ Found {var}")
                else:
                    print(f"❌ Missing {var}")
                    
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print("❌ No .env file found")
        print("   Create a .env file with your Supabase credentials:")
        print("   SUPABASE_URL=your_supabase_url")
        print("   SUPABASE_ANON_KEY=your_supabase_anon_key")
    
    if len(found_vars) == len(required_vars):
        print("\n✅ Supabase configuration looks good!")
        return True
    else:
        print(f"\n⚠️  Missing {len(required_vars) - len(found_vars)} required environment variables")
        return False

def test_backend_connection():
    """Test if the backend is running and can connect to Supabase."""
    
    print("\n🔗 Testing Backend Connection")
    print("=" * 40)
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Backend is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running")
        print("   Start the backend with: uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Supabase Migration Helper")
    print("=" * 50)
    print("This script helps you apply the drafts migration to Supabase.")
    print()
    
    # Run migration preparation
    migration_ready = run_migration()
    
    if migration_ready:
        # Check configuration
        config_ok = check_supabase_config()
        
        # Test backend connection
        backend_ok = test_backend_connection()
        
        print("\n" + "=" * 50)
        print("📊 Pre-Migration Checklist:")
        print(f"   Migration Ready: {'✅' if migration_ready else '❌'}")
        print(f"   Config Complete: {'✅' if config_ok else '❌'}")
        print(f"   Backend Running: {'✅' if backend_ok else '❌'}")
        
        if migration_ready and config_ok and backend_ok:
            print("\n🎉 Ready to apply migration!")
            print("\n📋 Next Steps:")
            print("1. Apply the migration SQL to your Supabase database")
            print("2. Test the draft functionality with: python test_supabase_drafts.py")
            print("3. Use the frontend to save and manage drafts")
        else:
            print("\n⚠️  Please fix the issues above before applying the migration")
    
    print("\n💡 Need Help?")
    print("- Check the Supabase documentation for SQL Editor usage")
    print("- Review the migration SQL for any customizations needed")
    print("- Test the migration in a development environment first")
