#!/usr/bin/env python3
"""
Simulated Application Worker

This worker processes applications with status "pending" and simulates the application process.
It creates simulated application results and updates the application status to "applied".

Future Extensions:
- This module can be extended to call Playwright for automated form filling
- Can integrate with official job board APIs (with explicit user consent)
- Can add retry logic and error handling for failed applications
- Can implement rate limiting and scheduling

Usage:
    python workers/simulated_apply_worker.py run_once
"""

import os
import sys
import json
import uuid
import logging
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simulated_apply_worker')

class SimulatedApplyWorker:
    """
    Worker that processes pending applications and simulates the application process.
    
    This worker:
    1. Fetches applications with status "pending" from Supabase
    2. Creates simulated application results for each
    3. Updates the application status to "applied"
    4. Stores application artifacts in the database
    """
    
    def __init__(self):
        """Initialize the worker with Supabase connection."""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY in .env file"
            )
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Simulated Apply Worker initialized successfully")
    
    def fetch_pending_applications(self) -> List[Dict[str, Any]]:
        """
        Fetch all applications with status "pending" from the database.
        
        Returns:
            List of application records with their associated job and user data
        """
        try:
            # Query applications with status "pending" and include related data
            response = self.supabase.table('applications').select(
                """
                id,
                user_id,
                job_id,
                status,
                artifacts,
                attempt_meta,
                created_at,
                updated_at,
                jobs!inner(
                    id,
                    title,
                    company,
                    raw
                ),
                users!inner(
                    id,
                    email
                )
                """
            ).eq('status', 'pending').execute()
            
            applications = response.data
            logger.info(f"Found {len(applications)} pending applications")
            
            return applications
            
        except Exception as e:
            logger.error(f"Error fetching pending applications: {e}")
            raise
    
    def create_simulated_application_result(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a simulated application result for the given application.
        
        Args:
            application: Application record with job and user data
            
        Returns:
            Simulated application result with metadata
        """
        job_data = application.get('jobs', {})
        user_data = application.get('users', {})
        
        # Create simulated application result
        simulated_result = {
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "method": "simulated",
            "note": "Simulation successful (no external submission)",
            "simulation_metadata": {
                "worker_version": "1.0.0",
                "processing_time": datetime.now(timezone.utc).isoformat(),
                "job_title": job_data.get('title', 'Unknown'),
                "company": job_data.get('company', 'Unknown'),
                "user_email": user_data.get('email', 'Unknown')
            },
            "application_details": {
                "application_id": application['id'],
                "job_id": application['job_id'],
                "user_id": application['user_id'],
                "original_attempt_meta": application.get('attempt_meta', {}),
                "previous_artifacts": application.get('artifacts', {})
            }
        }
        
        logger.info(f"Created simulated result for application {application['id']}")
        return simulated_result
    
    def update_application_status(self, application_id: str, simulated_result: Dict[str, Any]) -> bool:
        """
        Update the application status to "applied" and store the simulated result.
        
        Args:
            application_id: ID of the application to update
            simulated_result: Simulated application result to store
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Prepare update data
            update_data = {
                'status': 'applied',
                'artifacts': simulated_result,
                'attempt_meta': {
                    **(simulated_result.get('application_details', {}).get('original_attempt_meta', {})),
                    'applied_at': simulated_result['applied_at'],
                    'application_method': 'simulated_worker',
                    'worker_version': simulated_result['simulation_metadata']['worker_version']
                },
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Update the application in Supabase
            response = self.supabase.table('applications').update(update_data).eq('id', application_id).execute()
            
            if response.data:
                logger.info(f"Successfully updated application {application_id} to 'applied' status")
                return True
            else:
                logger.warning(f"No data returned when updating application {application_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating application {application_id}: {e}")
            return False
    
    def process_application(self, application: Dict[str, Any]) -> bool:
        """
        Process a single application: create simulated result and update status.
        
        Args:
            application: Application record to process
            
        Returns:
            True if processing was successful, False otherwise
        """
        application_id = application['id']
        
        try:
            logger.info(f"Processing application {application_id}")
            
            # Create simulated application result
            simulated_result = self.create_simulated_application_result(application)
            
            # Update application status
            success = self.update_application_status(application_id, simulated_result)
            
            if success:
                logger.info(f"Successfully processed application {application_id}")
                return True
            else:
                logger.error(f"Failed to update application {application_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing application {application_id}: {e}")
            return False
    
    def run_once(self) -> Dict[str, Any]:
        """
        Run the worker once to process all pending applications.
        
        Returns:
            Dictionary with processing results and statistics
        """
        logger.info("Starting simulated application worker (run_once)")
        
        try:
            # Fetch pending applications
            pending_applications = self.fetch_pending_applications()
            
            if not pending_applications:
                logger.info("No pending applications found")
                return {
                    'status': 'success',
                    'processed': 0,
                    'failed': 0,
                    'message': 'No pending applications to process'
                }
            
            # Process each application
            processed_count = 0
            failed_count = 0
            failed_applications = []
            
            for application in pending_applications:
                success = self.process_application(application)
                
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
                    failed_applications.append(application['id'])
            
            # Prepare results
            results = {
                'status': 'success' if failed_count == 0 else 'partial_success',
                'processed': processed_count,
                'failed': failed_count,
                'total_found': len(pending_applications),
                'failed_application_ids': failed_applications,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Worker run completed: {processed_count} processed, {failed_count} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in worker run: {e}")
            return {
                'status': 'error',
                'processed': 0,
                'failed': 0,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Simulated Application Worker')
    parser.add_argument(
        'command',
        choices=['run_once'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    if args.command == 'run_once':
        try:
            # Initialize worker
            worker = SimulatedApplyWorker()
            
            # Run worker once
            results = worker.run_once()
            
            # Print results
            print("\n" + "="*60)
            print("SIMULATED APPLICATION WORKER RESULTS")
            print("="*60)
            print(json.dumps(results, indent=2))
            print("="*60)
            
            # Exit with appropriate code
            if results['status'] == 'error':
                sys.exit(1)
            elif results['status'] == 'partial_success':
                sys.exit(2)  # Partial success
            else:
                sys.exit(0)  # Full success
                
        except Exception as e:
            logger.error(f"Worker failed to initialize or run: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()