#!/usr/bin/env python3
"""
Worker Process Manager

Manages the Gemini Apply Worker as a background process with:
- Health monitoring
- Automatic restart on failure
- Status tracking
- Graceful shutdown
- Process lifecycle management

Usage:
    python workers/worker_manager.py start
    python workers/worker_manager.py stop
    python workers/worker_manager.py restart
    python workers/worker_manager.py status
"""

import os
import sys
import time
import signal
import psutil
import logging
import subprocess
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'worker_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('worker_manager')

# Paths
BASE_DIR = Path(__file__).parent.parent
PID_FILE = BASE_DIR / 'worker.pid'
STATUS_FILE = BASE_DIR / 'worker_status.json'
LOG_DIR = BASE_DIR / 'logs'

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)


class WorkerManager:
    """Manages the Gemini Apply Worker process."""
    
    def __init__(self):
        self.pid_file = PID_FILE
        self.status_file = STATUS_FILE
        self.worker_script = BASE_DIR / 'workers' / 'gemini_apply_worker.py'
        
    def is_running(self) -> bool:
        """Check if worker is currently running."""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process with this PID exists
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                # Verify it's our worker process
                if 'gemini_apply_worker' in ' '.join(proc.cmdline()):
                    return True
            
            # PID file exists but process doesn't - clean up
            self.pid_file.unlink()
            return False
            
        except Exception as e:
            logger.warning(f"Error checking worker status: {e}")
            return False
    
    def get_pid(self) -> Optional[int]:
        """Get the PID of the running worker."""
        if not self.pid_file.exists():
            return None
        
        try:
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        except Exception:
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current worker status."""
        is_running = self.is_running()
        pid = self.get_pid() if is_running else None
        
        status = {
            'running': is_running,
            'pid': pid,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Add process info if running
        if is_running and pid:
            try:
                proc = psutil.Process(pid)
                status.update({
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_mb': proc.memory_info().rss / 1024 / 1024,
                    'started_at': datetime.fromtimestamp(proc.create_time()).isoformat(),
                    'status': proc.status()
                })
            except Exception as e:
                logger.warning(f"Error getting process info: {e}")
        
        # Load last run status if available
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    last_run = json.load(f)
                    status['last_run'] = last_run
            except Exception:
                pass
        
        return status
    
    def save_status(self, status_data: Dict[str, Any]):
        """Save worker status to file."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving status: {e}")
    
    def start(self, headless: bool = True, interval: int = 300) -> bool:
        """Start the worker in continuous mode."""
        if self.is_running():
            logger.warning("Worker is already running")
            return False
        
        logger.info("Starting Gemini Apply Worker...")
        
        try:
            # Build command
            cmd = [
                sys.executable,
                str(self.worker_script),
                'run_continuous',
                '--interval', str(interval)
            ]
            
            if headless:
                cmd.append('--headless')
            
            # Start worker as background process
            log_file = LOG_DIR / 'worker.log'
            with open(log_file, 'a') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=f,
                    cwd=BASE_DIR,
                    start_new_session=True  # Detach from parent
                )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment to ensure it started
            time.sleep(2)
            
            if self.is_running():
                logger.info(f"✅ Worker started successfully (PID: {process.pid})")
                logger.info(f"Logs: {log_file}")
                return True
            else:
                logger.error("Worker failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            return False
    
    def stop(self, force: bool = False) -> bool:
        """Stop the worker process."""
        if not self.is_running():
            logger.warning("Worker is not running")
            return False
        
        pid = self.get_pid()
        if not pid:
            return False
        
        logger.info(f"Stopping worker (PID: {pid})...")
        
        try:
            proc = psutil.Process(pid)
            
            if force:
                # Force kill
                proc.kill()
                logger.info("Worker force killed")
            else:
                # Graceful shutdown
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                    logger.info("Worker stopped gracefully")
                except psutil.TimeoutExpired:
                    logger.warning("Worker didn't stop gracefully, forcing...")
                    proc.kill()
            
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")
            return False
    
    def restart(self, headless: bool = True, interval: int = 300) -> bool:
        """Restart the worker."""
        logger.info("Restarting worker...")
        
        if self.is_running():
            if not self.stop():
                logger.error("Failed to stop worker for restart")
                return False
            
            # Wait for clean shutdown
            time.sleep(2)
        
        return self.start(headless=headless, interval=interval)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on worker."""
        status = self.get_status()
        
        health = {
            'healthy': False,
            'status': status,
            'checks': {}
        }
        
        # Check 1: Process running
        health['checks']['process_running'] = status['running']
        
        if status['running'] and status.get('pid'):
            try:
                proc = psutil.Process(status['pid'])
                
                # Check 2: CPU usage not maxed out
                cpu = proc.cpu_percent(interval=0.5)
                health['checks']['cpu_normal'] = cpu < 95
                
                # Check 3: Memory usage reasonable
                memory_mb = proc.memory_info().rss / 1024 / 1024
                health['checks']['memory_normal'] = memory_mb < 1024  # < 1GB
                
                # Check 4: Process responsive (not zombie)
                health['checks']['responsive'] = proc.status() != psutil.STATUS_ZOMBIE
                
                # Overall health
                health['healthy'] = all(health['checks'].values())
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                health['error'] = str(e)
        
        return health
    
    def monitor(self, interval: int = 60, auto_restart: bool = True):
        """Monitor worker and restart if unhealthy."""
        logger.info(f"Starting worker monitor (interval: {interval}s, auto_restart: {auto_restart})")
        
        try:
            while True:
                health = self.health_check()
                
                if not health['healthy']:
                    logger.warning(f"Worker unhealthy: {health}")
                    
                    if auto_restart:
                        logger.info("Attempting auto-restart...")
                        if self.restart():
                            logger.info("✅ Worker restarted successfully")
                        else:
                            logger.error("❌ Failed to restart worker")
                
                else:
                    logger.info(f"✅ Worker healthy: {health['status']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Worker Process Manager')
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'restart', 'status', 'monitor'],
        help='Command to execute'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default: True)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Worker run interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--monitor-interval',
        type=int,
        default=60,
        help='Monitor check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--no-auto-restart',
        action='store_true',
        help='Disable automatic restart in monitor mode'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force stop (kill instead of terminate)'
    )
    
    args = parser.parse_args()
    manager = WorkerManager()
    
    if args.command == 'start':
        success = manager.start(headless=args.headless, interval=args.interval)
        sys.exit(0 if success else 1)
        
    elif args.command == 'stop':
        success = manager.stop(force=args.force)
        sys.exit(0 if success else 1)
        
    elif args.command == 'restart':
        success = manager.restart(headless=args.headless, interval=args.interval)
        sys.exit(0 if success else 1)
        
    elif args.command == 'status':
        status = manager.get_status()
        print("\n" + "="*70)
        print("WORKER STATUS")
        print("="*70)
        print(json.dumps(status, indent=2))
        print("="*70 + "\n")
        sys.exit(0 if status['running'] else 1)
        
    elif args.command == 'monitor':
        manager.monitor(
            interval=args.monitor_interval,
            auto_restart=not args.no_auto_restart
        )


if __name__ == "__main__":
    main()

