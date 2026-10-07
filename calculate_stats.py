#!/usr/bin/env python3
"""
Calculate aggregate salary statistics per city
Returns mean, median, and other stats for nursing jobs
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import statistics

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_city_stats():
    """
    Get salary statistics for each city.
    Returns dict with city as key and stats dict as value.
    """
    # Fetch all jobs with salary and city data
    response = supabase.table('jobs').select(
        'city, state, salary_min_hourly, salary_max_hourly, title, company'
    ).execute()

    if not response.data:
        return {}

    # Group jobs by city
    city_data = {}
    for job in response.data:
        city = job['city']
        state = job['state']
        city_key = f"{city}, {state}"

        if city_key not in city_data:
            city_data[city_key] = {
                'jobs': [],
                'salaries': [],  # Store both min and max for averaging
                'job_count': 0,
            }

        city_data[city_key]['jobs'].append(job)
        city_data[city_key]['job_count'] += 1

        # Calculate average of min and max for this job
        if job['salary_min_hourly'] and job['salary_max_hourly']:
            avg_salary = (float(job['salary_min_hourly']) + float(job['salary_max_hourly'])) / 2
            city_data[city_key]['salaries'].append(avg_salary)

    # Calculate aggregate statistics
    stats = {}
    for city_key, data in city_data.items():
        salaries = data['salaries']

        if salaries:
            stats[city_key] = {
                'job_count': data['job_count'],
                'jobs_with_salary': len(salaries),
                'mean_hourly': round(statistics.mean(salaries), 2),
                'median_hourly': round(statistics.median(salaries), 2),
                'min_hourly': round(min(salaries), 2),
                'max_hourly': round(max(salaries), 2),
                'stdev_hourly': round(statistics.stdev(salaries), 2) if len(salaries) > 1 else 0,
            }
        else:
            stats[city_key] = {
                'job_count': data['job_count'],
                'jobs_with_salary': 0,
                'mean_hourly': None,
                'median_hourly': None,
                'min_hourly': None,
                'max_hourly': None,
                'stdev_hourly': None,
            }

    return stats


def get_overall_stats():
    """Get overall statistics across all cities."""
    response = supabase.table('jobs').select(
        'salary_min_hourly, salary_max_hourly'
    ).execute()

    if not response.data:
        return None

    salaries = []
    for job in response.data:
        if job['salary_min_hourly'] and job['salary_max_hourly']:
            avg_salary = (float(job['salary_min_hourly']) + float(job['salary_max_hourly'])) / 2
            salaries.append(avg_salary)

    if not salaries:
        return None

    return {
        'total_jobs': len(response.data),
        'jobs_with_salary': len(salaries),
        'mean_hourly': round(statistics.mean(salaries), 2),
        'median_hourly': round(statistics.median(salaries), 2),
        'min_hourly': round(min(salaries), 2),
        'max_hourly': round(max(salaries), 2),
        'stdev_hourly': round(statistics.stdev(salaries), 2) if len(salaries) > 1 else 0,
    }


if __name__ == '__main__':
    print("=" * 80)
    print("Nursing Job Salary Statistics")
    print("=" * 80)

    overall = get_overall_stats()
    if overall:
        print(f"\nOVERALL STATISTICS (All Cities)")
        print(f"  Total jobs: {overall['total_jobs']}")
        print(f"  Jobs with salary data: {overall['jobs_with_salary']}")
        print(f"  Mean hourly: ${overall['mean_hourly']:.2f}")
        print(f"  Median hourly: ${overall['median_hourly']:.2f}")
        print(f"  Range: ${overall['min_hourly']:.2f} - ${overall['max_hourly']:.2f}")
        print(f"  Std Dev: ${overall['stdev_hourly']:.2f}")

    city_stats = get_city_stats()

    if city_stats:
        print(f"\nPER-CITY STATISTICS")
        print(f"Total cities with data: {len(city_stats)}\n")

        # Sort by median salary (descending)
        sorted_cities = sorted(
            city_stats.items(),
            key=lambda x: x[1]['median_hourly'] if x[1]['median_hourly'] else 0,
            reverse=True
        )

        for city, stats in sorted_cities:
            print(f"{city}:")
            print(f"  Jobs: {stats['job_count']} ({stats['jobs_with_salary']} with salary data)")
            if stats['median_hourly']:
                print(f"  Median: ${stats['median_hourly']:.2f}/hr")
                print(f"  Mean: ${stats['mean_hourly']:.2f}/hr")
                print(f"  Range: ${stats['min_hourly']:.2f} - ${stats['max_hourly']:.2f}")
            else:
                print(f"  No salary data available")
            print()

    print("=" * 80)