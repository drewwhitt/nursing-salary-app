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
        # Delete all records - use is not null filter to match everything
        result = supabase.table('jobs').delete().is_('job_id', 'not', 'null').execute()
        print(f"✓ Successfully deleted all jobs from database")
        print("\nNow run: python3 scraper_rolling_daily.py")
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("Cancelled.")
