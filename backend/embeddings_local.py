#!/usr/bin/env python3
"""
Local Embeddings Generator for CareerPilot Agent

This script computes embeddings for job descriptions using sentence-transformers
and stores them in Supabase or locally for semantic search and job matching.

Model: all-MiniLM-L6-v2 (384-dimensional embeddings)
- Download size: ~90MB
- Memory usage: ~200-300MB during inference
- Speed: ~1000 sentences/second on CPU

Requirements:
- sentence-transformers
- supabase-py (optional, for database storage)
- numpy
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError as e:
    logger.error(f"Missing required dependencies: {e}")
    logger.error("Install with: pip install sentence-transformers numpy")
    sys.exit(1)

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase-py not available. Will use local file storage only.")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not available. Using system environment variables.")


class JobEmbeddingsGenerator:
    """
    Generates embeddings for job descriptions using sentence-transformers.
    
    Memory Considerations:
    - Model download: ~90MB
    - Model in memory: ~200-300MB
    - Embeddings: 384 dimensions × 4 bytes = 1.5KB per job
    - For 1000 jobs: ~1.5MB of embeddings
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", storage_type: str = "local"):
        """
        Initialize the embeddings generator.
        
        Args:
            model_name: Sentence transformer model to use
            storage_type: "local" or "supabase" for storing embeddings
        """
        self.model_name = model_name
        self.storage_type = storage_type
        self.model = None
        self.supabase_client = None
        
        # Initialize model
        self._load_model()
        
        # Initialize storage
        if storage_type == "supabase":
            self._init_supabase()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        logger.info(f"Loading model: {self.model_name}")
        logger.info("This may take a few minutes on first run (downloading ~90MB)...")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Model loaded successfully!")
            logger.info(f"Model dimensions: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _init_supabase(self):
        """Initialize Supabase client if available."""
        if not SUPABASE_AVAILABLE:
            logger.error("Supabase not available. Install with: pip install supabase")
            raise ImportError("supabase-py is required for database storage")
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials in environment variables")
            logger.error("Set SUPABASE_URL and SUPABASE_ANON_KEY")
            raise ValueError("Missing Supabase credentials")
        
        try:
            self.supabase_client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def load_jobs_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load jobs from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            logger.info(f"Loaded {len(jobs)} jobs from {file_path}")
            return jobs
        except Exception as e:
            logger.error(f"Failed to load jobs from {file_path}: {e}")
            raise
    
    def load_jobs_from_supabase(self) -> List[Dict[str, Any]]:
        """Load jobs from Supabase database."""
        if not self.supabase_client:
            raise ValueError("Supabase client not initialized")
        
        try:
            response = self.supabase_client.table('jobs').select('*').execute()
            jobs = response.data
            logger.info(f"Loaded {len(jobs)} jobs from Supabase")
            return jobs
        except Exception as e:
            logger.error(f"Failed to load jobs from Supabase: {e}")
            raise
    
    def prepare_job_text(self, job: Dict[str, Any]) -> str:
        """
        Prepare job text for embedding by combining relevant fields.
        
        Args:
            job: Job dictionary with title, company, description, etc.
            
        Returns:
            Combined text string for embedding
        """
        # Extract text fields
        title = job.get('title', '')
        company = job.get('company', '')
        location = job.get('location', '')
        
        # Get description from raw field if available
        raw_data = job.get('raw', {})
        description = raw_data.get('description', '') if isinstance(raw_data, dict) else ''
        
        # Combine requirements and nice-to-have
        requirements = raw_data.get('requirements', []) if isinstance(raw_data, dict) else []
        nice_to_have = raw_data.get('nice_to_have', []) if isinstance(raw_data, dict) else []
        
        # Create comprehensive text for embedding
        text_parts = [
            f"Title: {title}",
            f"Company: {company}",
            f"Location: {location}",
            f"Description: {description}",
        ]
        
        if requirements:
            text_parts.append(f"Requirements: {' '.join(requirements)}")
        
        if nice_to_have:
            text_parts.append(f"Nice to have: {' '.join(nice_to_have)}")
        
        return " ".join(text_parts)
    
    def compute_embeddings(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compute embeddings for a list of jobs.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of jobs with embeddings added
        """
        logger.info(f"Computing embeddings for {len(jobs)} jobs...")
        
        # Prepare texts for embedding
        texts = [self.prepare_job_text(job) for job in jobs]
        
        # Compute embeddings in batches to manage memory
        batch_size = 32  # Adjust based on available memory
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            # Compute embeddings for this batch
            batch_embeddings = self.model.encode(batch_texts, convert_to_tensor=False)
            all_embeddings.extend(batch_embeddings.tolist())
        
        # Add embeddings to jobs
        jobs_with_embeddings = []
        for job, embedding in zip(jobs, all_embeddings):
            job_copy = job.copy()
            
            # Add embedding to raw field
            if 'raw' not in job_copy:
                job_copy['raw'] = {}
            elif not isinstance(job_copy['raw'], dict):
                job_copy['raw'] = {}
            
            job_copy['raw']['embedding'] = embedding
            jobs_with_embeddings.append(job_copy)
        
        logger.info("✅ Embeddings computed successfully!")
        return jobs_with_embeddings
    
    def save_embeddings_locally(self, jobs_with_embeddings: List[Dict[str, Any]], 
                               output_file: str = "jobs_vectors.json"):
        """Save jobs with embeddings to local JSON file."""
        output_path = Path(output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(jobs_with_embeddings, f, indent=2, ensure_ascii=False)
            
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✅ Saved {len(jobs_with_embeddings)} jobs with embeddings to {output_path}")
            logger.info(f"File size: {file_size:.2f} MB")
            
        except Exception as e:
            logger.error(f"Failed to save embeddings to {output_path}: {e}")
            raise
    
    def save_embeddings_to_supabase(self, jobs_with_embeddings: List[Dict[str, Any]]):
        """Update jobs in Supabase with computed embeddings."""
        if not self.supabase_client:
            raise ValueError("Supabase client not initialized")
        
        logger.info(f"Updating {len(jobs_with_embeddings)} jobs in Supabase...")
        
        try:
            # Update jobs in batches
            batch_size = 10  # Supabase batch limit
            updated_count = 0
            
            for i in range(0, len(jobs_with_embeddings), batch_size):
                batch = jobs_with_embeddings[i:i + batch_size]
                
                # Prepare updates (only update the raw field with embeddings)
                updates = []
                for job in batch:
                    # Use PATCH to only update the raw field, not replace the entire row
                    job_id = job['id']
                    self.supabase_client.table('jobs').update({
                        'raw': job['raw']
                    }).eq('id', job_id).execute()
                
                # No batch upsert needed since we're updating one at a time
                updated_count += len(batch)
                logger.info(f"Updated {updated_count}/{len(jobs_with_embeddings)} jobs")
            
            logger.info("✅ All jobs updated in Supabase!")
            
        except Exception as e:
            logger.error(f"Failed to update jobs in Supabase: {e}")
            raise
    
    def process_jobs(self, input_source: str = "file", input_path: str = "sample_jobs.json"):
        """
        Main processing function to compute and store embeddings.
        
        Args:
            input_source: "file" or "supabase"
            input_path: Path to JSON file (if input_source is "file")
        """
        logger.info("🚀 Starting job embeddings generation...")
        
        # Load jobs
        if input_source == "file":
            jobs = self.load_jobs_from_file(input_path)
        elif input_source == "supabase":
            jobs = self.load_jobs_from_supabase()
        else:
            raise ValueError("input_source must be 'file' or 'supabase'")
        
        if not jobs:
            logger.warning("No jobs found to process")
            return
        
        # Compute embeddings
        jobs_with_embeddings = self.compute_embeddings(jobs)
        
        # Store embeddings
        if self.storage_type == "local":
            self.save_embeddings_locally(jobs_with_embeddings)
        elif self.storage_type == "supabase":
            self.save_embeddings_to_supabase(jobs_with_embeddings)
        
        logger.info("🎉 Embeddings generation completed!")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate embeddings for job descriptions")
    parser.add_argument("--input", choices=["file", "supabase"], default="file",
                       help="Input source: file or supabase")
    parser.add_argument("--input-file", default="sample_jobs.json",
                       help="Path to input JSON file (if input=file)")
    parser.add_argument("--storage", choices=["local", "supabase"], default="local",
                       help="Storage destination: local or supabase")
    parser.add_argument("--output-file", default="jobs_vectors.json",
                       help="Output file path (if storage=local)")
    parser.add_argument("--model", default="all-MiniLM-L6-v2",
                       help="Sentence transformer model name")
    
    args = parser.parse_args()
    
    # Create embeddings generator
    generator = JobEmbeddingsGenerator(
        model_name=args.model,
        storage_type=args.storage
    )
    
    # Process jobs
    generator.process_jobs(
        input_source=args.input,
        input_path=args.input_file
    )


if __name__ == "__main__":
    main()
