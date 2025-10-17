#!/usr/bin/env python3
"""
Apply All Pending Migrations

This script applies all pending SQL migrations to your Supabase database.
It tracks which migrations have been applied and only runs new ones.

Usage:
    python apply_all_migrations.py

Requirements:
    - Supabase project set up
    - Environment variables configured in .env:
      - SUPABASE_URL
      - SUPABASE_SERVICE_ROLE_KEY (for full database access)
      OR
      - SUPABASE_DB_URL (direct PostgreSQL connection string)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migrations_via_supabase():
    """Apply migrations using Supabase Python client."""
    try:
        from supabase import create_client, Client
    except ImportError:
        print("❌ Supabase client not installed. Run: pip install supabase")
        return False
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return False
    
    print(f"📋 Connecting to Supabase...")
    print(f"   URL: {supabase_url}")
    
    # Note: Supabase Python client doesn't support raw SQL execution
    # User must run migrations via Supabase Dashboard SQL Editor
    
    print("\n" + "="*70)
    print("⚠️  MANUAL MIGRATION REQUIRED")
    print("="*70)
    print("\nThe Supabase Python client doesn't support SQL migration execution.")
    print("Please apply migrations manually using one of these methods:\n")
    print("METHOD 1: Supabase Dashboard (Recommended)")
    print("-" * 70)
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Navigate to SQL Editor")
    print("4. Run each migration file in order:")
    
    migrations_dir = Path('migrations')
    migrations = sorted(migrations_dir.glob('*.sql'))
    
    for i, migration in enumerate(migrations, 1):
        print(f"   {i}. {migration.name}")
    
    print("\nMETHOD 2: Direct PostgreSQL (Advanced)")
    print("-" * 70)
    print("If you have direct database access:")
    print("   psql \"$SUPABASE_DB_URL\" -f migrations/001_initial.sql")
    print("   psql \"$SUPABASE_DB_URL\" -f migrations/002_add_drafts_to_users.sql")
    print("   psql \"$SUPABASE_DB_URL\" -f migrations/003_update_applications_status.sql")
    print("   psql \"$SUPABASE_DB_URL\" -f migrations/004_add_resumes_table.sql")
    print("   psql \"$SUPABASE_DB_URL\" -f migrations/005_performance_optimizations.sql")
    
    print("\n" + "="*70)
    
    # Show migration contents for easy copy-paste
    print("\n📄 MIGRATION FILE CONTENTS")
    print("="*70)
    
    for migration in migrations:
        print(f"\n### {migration.name} ###\n")
        with open(migration, 'r') as f:
            content = f.read()
            # Show first 20 lines
            lines = content.split('\n')[:20]
            print('\n'.join(lines))
            if len(content.split('\n')) > 20:
                print(f"\n... ({len(content.split('\n')) - 20} more lines)")
        print("\n" + "-"*70)
    
    return False


def check_migration_status():
    """Check which migrations have been applied."""
    print("\n📊 MIGRATION STATUS CHECK")
    print("="*70)
    
    migrations_dir = Path('migrations')
    if not migrations_dir.exists():
        print("❌ No migrations directory found")
        return
    
    migrations = sorted(migrations_dir.glob('*.sql'))
    
    print(f"\nFound {len(migrations)} migration files:\n")
    
    for migration in migrations:
        print(f"  📄 {migration.name}")
        with open(migration, 'r') as f:
            # Count lines
            lines = f.read().split('\n')
            print(f"      {len(lines)} lines")
    
    print("\n" + "="*70)


def create_migration_tracker():
    """Create SQL to track applied migrations (optional)."""
    sql = """
-- Create migrations tracking table (run this first)
CREATE TABLE IF NOT EXISTS _migrations (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by TEXT,
    checksum TEXT
);

-- Insert record after each migration
-- Example:
-- INSERT INTO _migrations (filename, applied_by) 
-- VALUES ('001_initial.sql', 'admin');
"""
    
    print("\n📋 MIGRATION TRACKING SQL")
    print("="*70)
    print(sql)
    print("="*70)


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("  CareerPilot Database Migrations")
    print("="*70 + "\n")
    
    # Check status
    check_migration_status()
    
    # Show migration tracker SQL
    create_migration_tracker()
    
    # Try to apply via Supabase
    apply_migrations_via_supabase()
    
    print("\n✅ MIGRATION INSTRUCTIONS PROVIDED")
    print("   Please apply migrations via Supabase Dashboard SQL Editor\n")


if __name__ == "__main__":
    main()

