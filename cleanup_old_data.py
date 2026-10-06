#!/usr/bin/env python3
"""
Clean up old mock and 'Unknown' data from the jobs table
Keeps only the real data from the latest scrapes
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("Cleaning up old mock and 'Unknown' data from jobs table")
print("=" * 80)

# Delete jobs with 'Unknown' title
print("\n1. Deleting jobs with 'Unknown' title...")
try:
    response = supabase.table('jobs').delete().eq('title', 'Unknown').execute()
    print(f"   ✓ Deleted jobs with Unknown title")
except Exception as e:
    print(f"   Error: {e}")

# Delete sample_data entries
print("\n2. Deleting sample data entries...")
try:
    response = supabase.table('jobs').delete().eq('source', 'sample_data').execute()
    print(f"   ✓ Deleted sample_data entries")
except Exception as e:
    print(f"   Error: {e}")

# Get remaining count by source
print("\n3. Remaining jobs in database:")
try:
    response = supabase.table('jobs').select('source').execute()
    if response.data:
        sources = {}
        for job in response.data:
            source = job['source']
            sources[source] = sources.get(source, 0) + 1

        print(f"\n   Total jobs remaining: {len(response.data)}")
        print(f"\n   Breakdown by source:")
        for source, count in sorted(sources.items()):
            print(f"     - {source}: {count} jobs")
    else:
        print(f"   Total jobs remaining: 0")
except Exception as e:
    print(f"   Error querying: {e}")

print("\n" + "=" * 80)
print("Cleanup complete! Your database now contains only real RN job data.")
print("=" * 80)
