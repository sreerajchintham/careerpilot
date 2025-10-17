#!/usr/bin/env python3
"""
Gemini AI Embeddings Generator for CareerPilot

This script computes embeddings for job descriptions using Google's Gemini AI
embedding models and stores them in Supabase for semantic search and job matching.

Model: text-embedding-004 (768-dimensional embeddings)
- High-quality embeddings optimized for retrieval tasks
- Better semantic understanding than local models
- API-based, no local model download needed

Requirements:
- google-generativeai
- supabase-py
- numpy (optional, for similarity calculations)
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError as e:
    logger.error(f"Missing required dependency: {e}")
    logger.error("Install with: pip install google-generativeai")
    sys.exit(1)

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.error("supabase-py is required for this script")
    logger.error("Install with: pip install supabase")
    sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not available. Using system environment variables.")


class GeminiEmbeddingsGenerator:
    """
    Generate embeddings using Google Gemini AI embedding models.
    """
    
    def __init__(
        self,
        model_name: str = "models/text-embedding-004",
        batch_size: int = 100,  # Gemini supports batch processing
        rate_limit_delay: float = 0.5  # Delay between API calls
    ):
        """
        Initialize the Gemini embeddings generator.
        
        Args:
            model_name: Gemini embedding model to use
            batch_size: Number of texts to process in one batch
            rate_limit_delay: Delay between API calls (seconds)
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        logger.info(f"✅ Gemini AI configured with model: {model_name}")
        
        # Initialize Supabase client
        if SUPABASE_AVAILABLE:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if supabase_url and supabase_key:
                self.supabase_client: Client = create_client(supabase_url, supabase_key)
                logger.info("✅ Supabase client initialized")
            else:
                raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY are required")
        else:
            raise ValueError("Supabase is required for this script")
    
    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generate embedding for a single text using Gemini AI.
        
        Args:
            text: Text to embed
            task_type: Type of embedding task (retrieval_document or retrieval_query)
        
        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            task_type: Type of embedding task
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = self.generate_embedding(text, task_type)
                embeddings.append(embedding)
                
                # Rate limiting
                if i < len(texts) - 1:
                    time.sleep(self.rate_limit_delay)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated embeddings for {i + 1}/{len(texts)} texts")
            
            except Exception as e:
                logger.error(f"Error generating embedding for text {i}: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 768)  # text-embedding-004 is 768-dimensional
        
        return embeddings
    
    def create_job_text(self, job: Dict[str, Any]) -> str:
        """
        Create a rich text representation of a job for embedding.
        
        Args:
            job: Job dictionary with title, company, description, etc.
        
        Returns:
            Formatted text string
        """
        parts = []
        
        # Title and company
        if job.get('title'):
            parts.append(f"Job Title: {job['title']}")
        
        if job.get('company'):
            parts.append(f"Company: {job['company']}")
        
        if job.get('location'):
            parts.append(f"Location: {job['location']}")
        
        # Description from raw data
        if job.get('raw'):
            raw = job['raw']
            
            if raw.get('description'):
                desc = raw['description']
                # Limit description length
                if len(desc) > 1500:
                    desc = desc[:1500] + "..."
                parts.append(f"Description: {desc}")
            
            if raw.get('requirements'):
                reqs = raw['requirements']
                if isinstance(reqs, list):
                    parts.append(f"Requirements: {', '.join(reqs)}")
                elif isinstance(reqs, str):
                    parts.append(f"Requirements: {reqs}")
            
            if raw.get('job_type'):
                parts.append(f"Job Type: {raw['job_type']}")
            
            if raw.get('salary'):
                parts.append(f"Salary: {raw['salary']}")
        
        return "\n".join(parts)
    
    def load_jobs_from_supabase(self) -> List[Dict[str, Any]]:
        """
        Load all jobs from Supabase.
        
        Returns:
            List of job dictionaries
        """
        try:
            response = self.supabase_client.table('jobs').select('*').execute()
            jobs = response.data
            logger.info(f"Loaded {len(jobs)} jobs from Supabase")
            return jobs
        except Exception as e:
            logger.error(f"Error loading jobs from Supabase: {e}")
            raise
    
    def save_embeddings_to_supabase(self, jobs_with_embeddings: List[Dict[str, Any]]):
        """
        Save embeddings back to Supabase by updating the raw field.
        
        Args:
            jobs_with_embeddings: List of jobs with embeddings added
        """
        try:
            # Update jobs in batches
            batch_size = 10
            updated_count = 0
            
            for i in range(0, len(jobs_with_embeddings), batch_size):
                batch = jobs_with_embeddings[i:i + batch_size]
                
                # Update each job individually
                for job in batch:
                    job_id = job['id']
                    self.supabase_client.table('jobs').update({
                        'raw': job['raw']
                    }).eq('id', job_id).execute()
                
                updated_count += len(batch)
                logger.info(f"Updated {updated_count}/{len(jobs_with_embeddings)} jobs")
            
            logger.info("✅ All jobs updated in Supabase!")
            
        except Exception as e:
            logger.error(f"Failed to update jobs in Supabase: {e}")
            raise
    
    def process_jobs(self, input_source: str = "supabase"):
        """
        Main processing function to compute and store embeddings.
        
        Args:
            input_source: Where to load jobs from (only "supabase" supported)
        """
        logger.info("🚀 Starting Gemini AI job embeddings generation...")
        
        # Load jobs
        if input_source == "supabase":
            jobs = self.load_jobs_from_supabase()
        else:
            raise ValueError(f"Unsupported input source: {input_source}")
        
        if not jobs:
            logger.warning("No jobs found to process")
            return
        
        # Create text representations
        logger.info("Creating text representations for jobs...")
        job_texts = []
        for job in jobs:
            text = self.create_job_text(job)
            job_texts.append(text)
        
        # Generate embeddings
        logger.info(f"Computing Gemini AI embeddings for {len(jobs)} jobs...")
        logger.info(f"Using model: {self.model_name}")
        logger.info(f"This may take a few minutes depending on the number of jobs...")
        
        embeddings = self.generate_embeddings_batch(job_texts)
        
        logger.info("✅ Embeddings computed successfully!")
        
        # Add embeddings to jobs
        for i, job in enumerate(jobs):
            if 'raw' not in job:
                job['raw'] = {}
            job['raw']['embedding'] = embeddings[i]
        
        # Save to Supabase
        logger.info(f"Updating {len(jobs)} jobs in Supabase...")
        self.save_embeddings_to_supabase(jobs)
        
        logger.info("🎉 Gemini AI embeddings generation completed!")


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings using Gemini AI')
    parser.add_argument(
        '--input',
        type=str,
        choices=['supabase'],
        default='supabase',
        help='Input source for jobs (default: supabase)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='models/text-embedding-004',
        help='Gemini embedding model to use (default: text-embedding-004)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing (default: 100)'
    )
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=0.5,
        help='Delay between API calls in seconds (default: 0.5)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = GeminiEmbeddingsGenerator(
            model_name=args.model,
            batch_size=args.batch_size,
            rate_limit_delay=args.rate_limit
        )
        
        # Process jobs
        generator.process_jobs(input_source=args.input)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

