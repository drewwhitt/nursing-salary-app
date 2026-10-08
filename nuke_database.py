#!/usr/bin/env python3
"""
Nuclear option: Delete ALL jobs from the database
Run this to start fresh, then run scraper_rolling_daily.py to rebuild
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("WARNING: This will DELETE ALL jobs from the database!")
print("=" * 80)
response = input("\nType 'DELETE ALL' to confirm: ")

if response == "DELETE ALL":
    print("\nDeleting all jobs...")
    try:
        # First, get all job IDs, then delete them
        # Supabase doesn't have a simple "delete all" so we'll get a count first
        jobs = supabase.table('jobs').select('job_id').execute()
        if jobs.data:
            print(f"Found {len(jobs.data)} jobs to delete...")
            # Delete by filtering on a condition that matches all rows
            result = supabase.table('jobs').delete().gte('created_at', '1900-01-01').execute()
            print(f"✓ Successfully deleted all jobs from database")
        else:
            print("✓ Database already empty")
        print("\nNow run: python3 scraper_rolling_daily.py")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("Cancelled.")
