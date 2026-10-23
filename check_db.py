#!/usr/bin/env python3
"""Check what's in the jobs table"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PAGE_SIZE = 1000


def fetch_all_jobs(columns):
    """Return every row of the jobs table, paging past Supabase's 1,000-row default limit."""
    rows = []
    start = 0
    while True:
        response = (
            supabase.table('jobs')
            .select(columns)
            .order('job_id')
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return rows


print("=" * 80)
print("Current Database Status")
print("=" * 80)

# Get all jobs grouped by source and title quality
jobs_data = fetch_all_jobs('job_id, title, company, source, salary_min_hourly, salary_max_hourly')

if jobs_data:
    total = len(jobs_data)

    # Categorize
    unknown_count = sum(1 for job in jobs_data if job['title'] == 'Unknown')
    sample_count = sum(1 for job in jobs_data if job['source'] == 'sample_data')
    real_count = total - unknown_count - sample_count

    print(f"\nTotal jobs: {total}")
    print(f"  - Unknown title: {unknown_count}")
    print(f"  - Sample data: {sample_count}")
    print(f"  - Real data: {real_count}")

    # Show by source
    sources = {}
    for job in jobs_data:
        source = job['source']
        if source not in sources:
            sources[source] = []
        sources[source].append(job)

    print(f"\nBreakdown by source:")
    for source in sorted(sources.keys()):
        jobs = sources[source]
        unknown_in_source = sum(1 for j in jobs if j['title'] == 'Unknown')
        print(f"  {source}: {len(jobs)} jobs ({unknown_in_source} with Unknown title)")

    # Show some real examples
    real_jobs = [j for j in jobs_data if j['title'] != 'Unknown' and j['source'] != 'sample_data']
    if real_jobs:
        print(f"\nSample of real RN jobs:")
        for job in real_jobs[:5]:
            salary_str = ""
            if job['salary_min_hourly'] and job['salary_max_hourly']:
                salary_str = f" (${job['salary_min_hourly']:.2f}-${job['salary_max_hourly']:.2f}/hr)"
            print(f"  ✓ {job['title']} at {job['company']}{salary_str}")
else:
    print("No jobs found in database")

print("\n" + "=" * 80)