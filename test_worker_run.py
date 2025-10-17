#!/usr/bin/env python3
"""Test script to manually run the worker once"""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from workers.gemini_apply_worker import GeminiApplyWorker
from dotenv import load_dotenv

load_dotenv()

async def test_worker():
    print("🚀 Testing Gemini Apply Worker...")
    worker = GeminiApplyWorker()
    result = await worker.run_once()
    print(f'\n✅ Worker Result:')
    print(f'  Status: {result["status"]}')
    print(f'  Processed: {result["processed"]}')
    print(f'  Failed: {result["failed"]}')
    print(f'  Skipped: {result["skipped"]}')
    print(f'  Total: {result["total"]}')
    
    if result.get('results'):
        print(f'\n📝 Application Results:')
        for r in result['results']:
            print(f"  - App {r['application_id']}: {r['status']} ({r.get('note', '')})")

if __name__ == "__main__":
    asyncio.run(test_worker())

