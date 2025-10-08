#!/usr/bin/env python3
"""
Upload existing embeddings to Supabase
"""

import json
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_embeddings_to_supabase():
    """Upload embeddings from jobs_vectors.json to Supabase"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Load embeddings from local file
    try:
        with open('jobs_vectors.json', 'r') as f:
            jobs_with_embeddings = json.load(f)
        print(f"📄 Loaded {len(jobs_with_embeddings)} jobs with embeddings")
    except FileNotFoundError:
        print("❌ jobs_vectors.json not found. Run embeddings_local.py first.")
        return
    
    # Upload to Supabase
    print("🚀 Uploading embeddings to Supabase...")
    
    try:
        # Update jobs in batches
        batch_size = 10
        updated_count = 0
        
        for i in range(0, len(jobs_with_embeddings), batch_size):
            batch = jobs_with_embeddings[i:i + batch_size]
            
            # Prepare updates - we need to match by title and company since we don't have IDs
            updates = []
            for job in batch:
                # Find matching job in Supabase by title and company
                response = supabase.table('jobs').select('id, source, title, company, location, posted_at').eq('title', job['title']).eq('company', job['company']).execute()
                
                if response.data:
                    existing_job = response.data[0]
                    job_id = existing_job['id']
                    
                    # Update the raw field with embedding AND preserve all original job data
                    # Merge the existing raw data with the new embedding
                    existing_raw = existing_job.get('raw', {})
                    new_raw = job.get('raw', {})
                    
                    # Preserve all original data and add embedding
                    merged_raw = {**existing_raw, **new_raw}
                    
                    updates.append({
                        'id': job_id,
                        'source': existing_job['source'],
                        'title': existing_job['title'],
                        'company': existing_job['company'],
                        'location': existing_job['location'],
                        'posted_at': existing_job['posted_at'],
                        'raw': merged_raw
                    })
            
            if updates:
                # Update batch
                response = supabase.table('jobs').upsert(updates).execute()
                updated_count += len(updates)
                print(f"✅ Updated {updated_count}/{len(jobs_with_embeddings)} jobs")
            else:
                print(f"⚠️  No matching jobs found for batch {i//batch_size + 1}")
        
        print(f"🎉 Successfully uploaded embeddings for {updated_count} jobs!")
        
    except Exception as e:
        print(f"❌ Error uploading embeddings: {e}")

if __name__ == "__main__":
    upload_embeddings_to_supabase()
