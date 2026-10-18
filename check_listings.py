#!/usr/bin/env python3
"""
Re-checks active job postings for the cities scraped two days ago.

Each city is scraped on one weekday (see cities.py). Its postings are re-checked two days later,
so the job boards only get one check per city per week instead of one per day.
A posting is closed only when the job page clearly says so (404/410 or "no longer available").
Blocked, rate-limited, or failed requests leave the posting active, so a block never hides a live job.
"""
import os, time, random, logging
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
from supabase import create_client
from cities import cities_scraped_on

load_dotenv()
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CHECK_DELAY_DAYS = 2   # re-check a city's postings this many days after its scrape
REQUEST_TIMEOUT = 15   # seconds per job page
CLOSED_PHRASES = (
    'no longer available',
    'no longer accepting',
    'this job has expired',
    'job has expired',
    'job is no longer',
    'job not found',
    'this job is closed',
)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}


def check_url(url):
    """Returns 'open', 'closed', or 'unknown' for a job URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        logger.warning(f'  Could not reach {url}: {e}')
        return 'unknown'

    if resp.status_code in (404, 410):
        return 'closed'
    if resp.status_code != 200:
        # 403, 429, 5xx, etc. Boards block automated checks, so don't treat these as closed.
        return 'unknown'

    page = resp.text.lower()
    if any(phrase in page for phrase in CLOSED_PHRASES):
        return 'closed'
    return 'open'


def check_city(city, state):
    """Re-checks every active posting for one city. Returns counts of each result."""
    counts = {'open': 0, 'closed': 0, 'unknown': 0}
    try:
        result = (
            supabase.table('jobs')
            .select('job_id, url')
            .eq('city', city).eq('state', state).eq('is_active', True)
            .execute()
        )
    except Exception as e:
        logger.error(f'  Could not load postings for {city}, {state}: {e}')
        return counts

    for job in result.data or []:
        status = check_url(job['url'])
        counts[status] += 1

        if status == 'closed':
            try:
                supabase.table('jobs').update({
                    'is_active': False,
                    'archived_at': datetime.now().isoformat(),
                }).eq('job_id', job['job_id']).execute()
            except Exception as e:
                logger.error(f'  Could not close posting {job["job_id"]}: {e}')

        # Pause between job-page requests so the boards don't see a burst.
        time.sleep(random.uniform(2, 4))

    return counts


def check_listings_for_day(today=None):
    """Re-checks the cities that were scraped CHECK_DELAY_DAYS ago. Safe to call every day."""
    today = datetime.now() if today is None else today
    scrape_day = (today - timedelta(days=CHECK_DELAY_DAYS)).weekday()
    cities = cities_scraped_on(scrape_day)
    logger.info(f'Listing check - cities scraped on weekday {scrape_day}: {", ".join(f"{c}, {s}" for c, s in cities)}')

    for city, state in cities:
        counts = check_city(city, state)
        logger.info(f'  {city}, {state}: {counts["open"]} open, {counts["closed"]} closed, {counts["unknown"]} unknown')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    check_listings_for_day()
