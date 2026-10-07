#!/usr/bin/env python3
import os, time, random, logging, uuid
from datetime import datetime
from dotenv import load_dotenv
import jobspy
from supabase import create_client, Client

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CITIES = [
    # Week 1 (5 cities per day = 35 total cities)
    ("Nashville", "TN"),
    ("Dallas", "TX"),
    ("Charlotte", "NC"),
    ("Denver", "CO"),
    ("Phoenix", "AZ"),
    ("Houston", "TX"),
    ("San Antonio", "TX"),
    ("Austin", "TX"),
    ("Atlanta", "GA"),
    ("Miami", "FL"),
    ("Tampa", "FL"),
    ("Orlando", "FL"),
    ("Boston", "MA"),
    ("New York", "NY"),
    ("Philadelphia", "PA"),
    ("Washington", "DC"),
    ("Baltimore", "MD"),
    ("Chicago", "IL"),
    ("Detroit", "MI"),
    ("Minneapolis", "MN"),
    ("Kansas City", "MO"),
    ("St. Louis", "MO"),
    ("Nashville", "TN"),  # Will repeat weekly
    ("Memphis", "TN"),
    ("New Orleans", "LA"),
    ("Los Angeles", "CA"),
    ("San Diego", "CA"),
    ("San Francisco", "CA"),
    ("Seattle", "WA"),
    ("Portland", "OR"),
    ("Las Vegas", "NV"),
    ("Salt Lake City", "UT"),
    ("Indianapolis", "IN"),
    ("Columbus", "OH"),
    ("Cleveland", "OH"),
    ("Pittsburgh", "PA"),
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

def is_registered_nurse(title):
    """Filter to keep only Registered Nurse roles (RN, Charge Nurse, etc.)"""
    if not title or title == 'Unknown':
        return False

    title_lower = str(title).lower()

    # Keywords that indicate this IS a registered nurse role
    rn_keywords = [
        'registered nurse',
        'rn',
        'charge nurse',
        'clinical nurse',
        'nurse coordinator',
        'nurse manager',
        'case manager',  # RN case managers
        'nurse specialist',
        'nurse educator',
        'infection control nurse',
        'occupational health nurse',
    ]

    # Keywords that indicate this is NOT a registered nurse
    exclude_keywords = [
        'cna',
        'certified nursing assistant',
        'patient care technician',
        'pct',
        'paramedic',
        'emt',
        'lpn',
        'lvn',
        'licensed practical nurse',
        'licensed vocational nurse',
        'phlebotomist',
        'medical assistant',
        'ma',
        'nursing assistant',
        'healthcare assistant',
        'home health aide',
        'hha',
    ]

    # If it contains any exclude keywords, it's not an RN
    for exclude in exclude_keywords:
        if exclude in title_lower:
            return False

    # If it contains any RN keywords, it is an RN
    for keyword in rn_keywords:
        if keyword in title_lower:
            return True

    return False

def normalize_salary(min_amt, max_amt, interval):
    """Convert salary to hourly rate (using 2080 hours/year standard)"""
    if min_amt is None or max_amt is None:
        return None, None

    try:
        min_amt = float(min_amt)
        max_amt = float(max_amt)
    except (ValueError, TypeError):
        return None, None

    interval = (interval or '').lower().strip()

    if interval in ('hourly', 'hour'):
        hourly_min, hourly_max = min_amt, max_amt
    elif interval in ('annual', 'yearly', 'year'):
        hourly_min, hourly_max = min_amt / 2080, max_amt / 2080
    elif interval == 'monthly':
        hourly_min, hourly_max = min_amt * 12 / 2080, max_amt * 12 / 2080
    else:
        # Default to hourly if interval is unclear
        hourly_min, hourly_max = min_amt, max_amt

    # Filter out obvious outliers/errors: salaries outside reasonable nursing range
    # Registered nurses typically earn $20-$200/hr
    # Outliers like $1995/hr or $5/hr are data entry errors
    MIN_REASONABLE = 20.0  # $20/hr minimum
    MAX_REASONABLE = 200.0  # $200/hr maximum

    if hourly_min < MIN_REASONABLE or hourly_max > MAX_REASONABLE:
        # If either end is unreasonable, reject the entire record
        return None, None

    return hourly_min, hourly_max

def scrape_city(city, state):
    logger.info(f'[{datetime.now().strftime("%Y-%m-%d %H:%M")}] Scraping {city}, {state}...')
    try:
        time.sleep(2 + random.uniform(0, 2))
        logger.info(f'  Calling jobspy.scrape_jobs for {city}, {state}...')
        jobs = jobspy.scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term='nurse OR RN OR "registered nurse"',
            location=f'{city}, {state}',
            results_wanted=75,
            hours_old=720,
            country_indeed='USA'
        )
        logger.info(f'  JobSpy returned successfully')

        # If we got no jobs or all unknowns, try Indeed only
        if hasattr(jobs, 'height'):
            initial_count = jobs.height
        elif hasattr(jobs, '__len__'):
            initial_count = len(jobs)
        else:
            initial_count = 0

        if initial_count == 0:
            logger.info(f'  No jobs from both sources, trying Indeed only...')
            jobs = jobspy.scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term='nurse OR RN OR "registered nurse"',
                location=f'{city}, {state}',
                results_wanted=75,
                hours_old=720,
                country_indeed='USA'
            )
            logger.info(f'  Indeed-only search returned')

        # Check if jobs were found (handle DataFrame/object types)
        jobs_count = 0
        try:
            # If it's a DataFrame-like object with 'height' attribute (Polars)
            if hasattr(jobs, 'height'):
                jobs_count = jobs.height
            # If it's a list or has __len__
            elif hasattr(jobs, '__len__'):
                jobs_count = len(jobs)
        except:
            jobs_count = 0

        if jobs_count > 0:
            logger.info(f'  Found {jobs_count} jobs, inserting...')

            # Convert pandas/polars DataFrame to list of dicts
            if hasattr(jobs, 'to_dict'):
                # pandas DataFrame
                jobs_list = jobs.to_dict('records')
            elif hasattr(jobs, 'to_dicts'):
                # Polars DataFrame
                jobs_list = jobs.to_dicts()
            else:
                # Already a list or iterable
                jobs_list = list(jobs)

            for job in jobs_list:
                try:
                    # Safe field access - works with dicts and Polars Rows
                    def get_field(key, default=None):
                        try:
                            val = job.get(key) if hasattr(job, 'get') else job[key]
                            # Handle NaN values from pandas
                            if val is not None and str(val) == 'nan':
                                return default
                            return val if val is not None else default
                        except:
                            return default

                    title = get_field('title', 'Unknown')

                    # Filter to Registered Nurse roles only
                    if not is_registered_nurse(title):
                        continue

                    # Safe field access
                    min_amount = get_field('min_amount')
                    max_amount = get_field('max_amount')
                    interval = get_field('interval', 'hourly')

                    min_h, max_h = normalize_salary(
                        float(min_amount) if min_amount else None,
                        float(max_amount) if max_amount else None,
                        str(interval) if interval else 'hourly'
                    )

                    job_id = get_field('id', str(title)[:30] if title else 'unknown')

                    # JobSpy uses 'job_url' field
                    url = get_field('job_url')
                    if not url:
                        url = f"https://jobspy.com/job/{uuid.uuid4()}"

                    # Get posted_at date from JobSpy if available
                    posted_at = get_field('date_posted')
                    if not posted_at:
                        posted_at = datetime.now().isoformat()
                    else:
                        # Ensure it's ISO format string
                        if not isinstance(posted_at, str):
                            posted_at = str(posted_at)

                    job_dict = {
                        'source': get_field('site', 'jobspy'),
                        'source_job_id': str(job_id)[:100],
                        'url': str(url)[:500],
                        'title': str(title)[:255],
                        'company': str(get_field('company', 'Unknown'))[:255],
                        'facility_name': str(get_field('company', 'Unknown'))[:255],
                        'city': city,
                        'state': state,
                        'employment_type': str(get_field('job_type', ''))[:50],
                        'description': str(get_field('description', ''))[:2000],
                        'salary_min_hourly': min_h,
                        'salary_max_hourly': max_h,
                        'salary_period_original': str(interval) if interval else 'hourly',
                        'is_active': True,
                        'posted_at': posted_at,
                        'scraped_at': datetime.now().isoformat(),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                    }
                    job_clean = {k: v for k, v in job_dict.items() if v is not None}
                    supabase.table('jobs').upsert(job_clean).execute()
                except Exception as e:
                    logger.warning(f'  Error inserting job: {e}')
            logger.info(f'  ✓ Inserted {jobs_count} jobs for {city}, {state}')
        else:
            logger.info(f'  No jobs found')
    except Exception as e:
        logger.error(f'  Error: {e}')

# Calculate which 5 cities to scrape today based on day of week
# With 35 cities and 7 days = 5 cities per day
today = datetime.now().weekday()  # 0=Monday, 6=Sunday
cities_per_day = 5
start_idx = (today * cities_per_day) % len(CITIES)
cities_to_scrape = []

for i in range(cities_per_day):
    idx = (start_idx + i) % len(CITIES)
    cities_to_scrape.append(CITIES[idx])

logger.info(f'Daily Scraper - Day {today} ({cities_per_day} cities)')
logger.info(f'Cities to scrape: {", ".join([f"{c[0]}, {c[1]}" for c in cities_to_scrape])}')

for city, state in cities_to_scrape:
    scrape_city(city, state)

logger.info('Done.')
