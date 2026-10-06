# Nurse Explorer - Nursing Job Salary Platform

A data aggregation and analytics platform for registered nurse (RN) job postings and compensation data across major US cities.

## Features

- **Daily rolling scraper** — Scrapes 5 cities per day across LinkedIn and Indeed
- **RN-focused filtering** — Only captures registered nurse roles, excludes CNAs, paramedics, etc.
- **Salary normalization** — Converts all salaries to hourly rates ($20-$200/hr range, outliers removed)
- **Data analytics** — Mean, median, and distribution analysis per city
- **Interactive dashboard** — Streamlit-based visualization and exploration
- **35-city coverage** — Full weekly rotation across major US nursing markets

## Project Structure

```
nursing-salary-app/
├── scraper_rolling_daily.py    # Main scraper (runs daily via Task Scheduler)
├── calculate_stats.py          # Statistics calculation module
├── stats_dashboard.py          # Streamlit dashboard for data exploration
├── check_db.py                 # Check database status and job counts
├── cleanup_old_data.py         # Remove old/mock data from database
├── app_demo.py                 # Main Streamlit app (job listings display)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
└── README.md                   # This file
```

## Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create `.env` file with:
```
SUPABASE_URL=your_supabase_url
SUPABASE_API_KEY=your_supabase_api_key
```

## Usage

### Check Database Status
```bash
python check_db.py
```

### Run the Scraper
```bash
python scraper_rolling_daily.py
```
Scrapes 5 cities per day on a rolling schedule. Each city gets updated once per week.

### View Statistics
Quick terminal output:
```bash
python calculate_stats.py
```

Interactive dashboard:
```bash
streamlit run stats_dashboard.py
```

### View Job Listings
```bash
streamlit run app_demo.py
```

## Automation (Windows)

Use Windows Task Scheduler to run `scraper_rolling_daily.py` automatically:

1. Create a batch file `run_scraper_daily.bat`:
```batch
@echo off
cd /d C:\Users\Drewhitt\nursing-salary-app
call venv\Scripts\activate
python scraper_rolling_daily.py >> scraper_log.txt 2>&1
call venv\Scripts\deactivate
```

2. Schedule in Task Scheduler:
- Action: Start a program
- Program: `C:\Users\Drewhitt\nursing-salary-app\run_scraper_daily.bat`
- Schedule: Daily at 3:45 AM Chicago time

## Data Sources

- **LinkedIn** — Professional job postings
- **Indeed** — Aggregated job listings from company career pages

Salary data is normalized to hourly rates and filtered for validity ($20-$200/hr range).

## Database Schema

Key fields in `jobs` table:
- `job_id` — Unique job identifier
- `title` — Job title (filtered for RN roles only)
- `company` — Hiring company
- `city, state` — Location
- `salary_min_hourly, salary_max_hourly` — Normalized hourly rates
- `source` — Where the job was scraped (linkedin, indeed)
- `posted_at, scraped_at` — Timestamps

## Cities Covered

Weekly rotation across 35 major US cities:
Nashville, Dallas, Charlotte, Denver, Phoenix, Houston, San Antonio, Austin, Atlanta, Miami, Tampa, Orlando, Boston, New York, Philadelphia, Washington DC, Baltimore, Chicago, Detroit, Minneapolis, Kansas City, St. Louis, Memphis, New Orleans, Los Angeles, San Diego, San Francisco, Seattle, Portland, Las Vegas, Salt Lake City, Indianapolis, Columbus, Cleveland, Pittsburgh

## Notes

- Salary outliers (typos like $1995/hr) are automatically filtered
- Job duplicates are prevented via URL unique constraint in database
- Only active job postings from the last 7 days are included
