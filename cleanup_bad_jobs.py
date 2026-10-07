#!/usr/bin/env python3
"""
Cleanup script to remove invalid jobs from the database:
- Non-RN roles (FNP, Physicians, etc.)
- Salary outliers (outside $20-$200/hr range)
- Malformed records
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Keywords that are NOT registered nurse positions
EXCLUDE_KEYWORDS = [
    'nurse practitioner', 'fnp', 'np',
    'physician', 'doctor', 'md',
    'physician assistant', 'pa',
    'dentist', 'pharmacist',
    'cna', 'certified nursing assistant',
    'patient care technician', 'pct',
    'paramedic', 'emt',
    'lpn', 'lvn', 'licensed practical nurse',
    'phlebotomist', 'medical assistant',
    'nursing assistant', 'healthcare assistant',
    'home health aide', 'hha',
]

def should_delete_job(title, min_sal, max_sal):
    """Determine if a job should be deleted"""

    # Check for non-RN titles
    if title:
        title_lower = str(title).lower()
        for exclude in EXCLUDE_KEYWORDS:
            if exclude in title_lower:
                return True, f"Non-RN role: {exclude}"

    # Check for salary outliers
    if min_sal and max_sal:
        if min_sal < 20 or max_sal > 200:
            return True, f"Salary outlier: ${min_sal}-${max_sal}/hr"
        if min_sal > max_sal:
            return True, f"Invalid range: min > max"

    return False, None

print("Fetching jobs from database...")
response = supabase.table('jobs').select('job_id, title, salary_min_hourly, salary_max_hourly').execute()
jobs = response.data

if not jobs:
    print("No jobs found.")
    exit()

print(f"Total jobs: {len(jobs)}")

# Find jobs to delete
to_delete = []
for job in jobs:
    should_delete, reason = should_delete_job(
        job.get('title'),
        job.get('salary_min_hourly'),
        job.get('salary_max_hourly')
    )
    if should_delete:
        to_delete.append({
            'id': job['job_id'],
            'title': job.get('title'),
            'reason': reason
        })

print(f"\nJobs to delete: {len(to_delete)}")

if to_delete:
    print("\nDeleting invalid jobs:")
    for job in to_delete:
        print(f"  - {job['title']}: {job['reason']}")
        supabase.table('jobs').delete().eq('job_id', job['id']).execute()

    print(f"\n✓ Deleted {len(to_delete)} invalid jobs")
else:
    print("No jobs to delete!")

print("\nCleanup complete!")
