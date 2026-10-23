# Nurse Explorer - Project Context for Claude

## Project Overview

Nurse Explorer is a nursing job salary aggregation and analytics platform built by Drew. It scrapes real registered nurse (RN) job listings from LinkedIn and Indeed, normalizes salary data, and provides analytics dashboards to track nursing compensation across 35 major US cities.

**Status:** MVP complete with daily automated scraping, statistics module, and interactive dashboards.

## Problem Being Solved

Drew wants to build a data-driven resource for registered nurses to understand job market compensation trends across different cities. The app aggregates real job postings, filters for legitimate RN roles only, and provides actionable salary analytics.

## Tech Stack

- **Backend:** Supabase (PostgreSQL) for data storage
- **Scraping:** JobSpy library (pulls from LinkedIn + Indeed)
- **Data Processing:** Python with pandas/statistics
- **Frontend:** Streamlit (two apps: job listings + stats dashboard)
- **Automation:** Windows Task Scheduler (daily scraping at 8:00 PM Central, PC wakes from sleep and returns to sleep after the run if it was not in use)
- **Deployment:** GitHub repo for version control, local execution on Windows machine

## Key Features Implemented

### 1. Rolling Daily Scraper (`scraper_rolling_daily.py`)
- Scrapes 5 cities per day (35 total, one complete rotation per week)
- Sources: LinkedIn + Indeed (pulls from company career pages)
- Requests 100 results per source per city (`RESULTS_PER_SEARCH`)
- Only pulls postings from the last 14 days (`HOURS_OLD = 336`)
- Each run archives postings older than 14 days (`STALE_AFTER_DAYS`)
- Automatically filters to RN roles only (no CNAs, paramedics, LPNs, etc.); whole-word RN match
- Normalizes all salaries to hourly rates ($20-$200/hr range)
- Removes salary outliers (typos like $1995/hr are rejected)
- Prevents duplicates via URL unique constraint in database
- Known gap: JobSpy calls have no timeout. `SCRAPE_TIMEOUT_SECONDS` in `.env` is not read by the code. A stalled board request can hang a run; the scheduled task's 1-hour limit is the only cap.

### 2. Job Listings Dashboard (`app_demo.py`)
- Streamlit app displaying all scraped jobs
- Filters by city, salary range, employment type
- Shows job details: title, company, salary range, job description
- Integrates BLS wage benchmarks for reference
- Takes-home pay calculator

### 3. Statistics Module (`calculate_stats.py`)
- Reusable Python module for salary aggregation
- Calculates per-city: mean, median, min, max, std deviation
- Groups jobs by city and source
- Can be run standalone or imported into other scripts

### 4. Analytics Dashboard (`stats_dashboard.py`)
- Interactive Streamlit dashboard using stats module
- Three tabs: Salary Comparison, Job Distribution, City Details
- Charts: median vs mean by city, job counts, detailed tables
- CSV download of statistics
- Real-time calculation from database

### 5. Database Tools
- `check_db.py` — View database status, job counts per city/source
- `cleanup_old_data.py` — Remove old/invalid data entries

## Database Schema

**jobs table** key fields:
- `job_id` — Unique identifier
- `title`, `company` — Job details (RN-filtered)
- `city`, `state` — Location
- `salary_min_hourly`, `salary_max_hourly` — Normalized hourly rates
- `source` — Where scraped (linkedin, indeed)
- `posted_at`, `scraped_at` — Timestamps
- `url` — Job posting link (unique constraint prevents duplicates)
- Additional fields: employment_type, description, is_active, etc.

**Data Quality:**
- Only RN roles (registered nurses, charge nurses, clinical nurses, nurse coordinators, case managers, etc.)
- Salary range: $20-$200/hr (outliers removed)
- Last 7 days of postings only
- 59+ jobs currently in database across multiple cities

## Cities Covered (35 total)

Rotating weekly schedule (5 cities per day):
- **Day 0 (Mon):** Nashville, Dallas, Charlotte, Denver, Phoenix
- **Day 1 (Tue):** Houston, San Antonio, Austin, Atlanta, Miami
- **Day 2 (Wed):** Tampa, Orlando, Boston, New York, Philadelphia
- **Day 3 (Thu):** Washington DC, Baltimore, Chicago, Detroit, Minneapolis
- **Day 4 (Fri):** Kansas City, St. Louis, Memphis, New Orleans, Los Angeles
- **Day 5 (Sat):** San Diego, San Francisco, Seattle, Portland, Las Vegas
- **Day 6 (Sun):** Salt Lake City, Indianapolis, Columbus, Cleveland, Pittsburgh

## Key Design Decisions

### RN Filtering
**Include:** Registered Nurse, RN, Charge Nurse, Clinical Nurse, Nurse Coordinator, Nurse Manager, Case Manager (RN), Nurse Specialist, Nurse Educator, Infection Control Nurse, Occupational Health Nurse

**Exclude:** CNA, Certified Nursing Assistant, Patient Care Technician, PCT, Paramedic, EMT, LPN, LVN, Licensed Practical Nurse, Licensed Vocational Nurse, Phlebotomist, Medical Assistant, MA, Nursing Assistant, Healthcare Assistant, Home Health Aide, HHA

### Salary Normalization
- **Hourly:** Used as-is
- **Annual:** Divided by 2080 (standard 40-hour work week, 52 weeks)
- **Monthly:** Multiplied by 12, then divided by 2080
- **Invalid range:** $20-$200/hr (rejects obvious typos)
- **Method:** Average of min/max for each job, then aggregate per city

### Data Sources
- **LinkedIn** — Professional network, quality postings
- **Indeed** — Large aggregator that pulls from company career pages
- ~~Glassdoor~~ (removed — lower quality for nursing)
- ~~ZipRecruiter~~ (not supported in JobSpy 1.2.0)

## Automation

**Windows Task Scheduler** (task name: `NursingJobScraper`):
- **Time:** 8:00 PM Central, daily. (Previously 7:00 AM, then 3:45 AM so the room light doesn't wake Drew overnight.)
- **Command:** `PowerShell.exe -ExecutionPolicy Bypass -File C:\Users\Drewhitt\nursing-salary-app\run_scraper_daily.ps1`
- **Wake/sleep:** Wake timer is on. The PC wakes from sleep for the run. `run_scraper_daily.ps1` does NOT put the PC back to sleep after the run (`$sleepAfterRun = $false`). The PC stays on once the run finishes. The idle-input check code is still in the script but is inactive while sleep is off. A powered-off PC cannot be woken by the task, so the PC must stay on or asleep for runs to happen.
- **Safety limits:** 1-hour execution limit, no overlapping runs (`IgnoreNew`), runs on battery, catches up on a missed run (`StartWhenAvailable`).
- **Logon:** Currently set to run only while logged in (`Interactive`). Logged-off runs need an admin change to `S4U` (see below). Until that is done, a run only happens if the user is logged on or the machine is awake with a session.
- **Log:** Every run appends to `scraper_log.txt` (start, success/failure, sleep).
- **Old launcher:** `run_scraper_daily.bat` still exists but the task no longer uses it.

Admin command to allow logged-off runs (run once in an elevated PowerShell):
```
$p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited; Set-ScheduledTask -TaskName NursingJobScraper -Principal $p
```

## Important Notes for Future Work

### What's Working Well
- Real job data being scraped (not mock/Unknown titles)
- Salary normalization working correctly
- RN filtering catching non-nursing roles effectively
- Database constraint preventing duplicates
- Stats module producing accurate aggregations
- Streamlit dashboards responsive and functional

### Known Limitations & Future Improvements
1. **Job Sources** — Currently LinkedIn + Indeed only. Could add:
   - Nursing-specific job boards (NurseRecruiter, Nurse.com)
   - Company career pages (HCA Healthcare, Mayo Clinic, Cleveland Clinic, etc.)
   - Government jobs (VA, military nursing)

2. **Data Enrichment** — Could add:
   - Cost of living adjustments by city
   - License requirements by state
   - Shift differentials (many jobs list these separately)
   - Specialization/unit premiums

3. **Analysis Features** — Could add:
   - Time series tracking (salary trends over time)
   - Comparative analysis (city-to-city, company-to-company)
   - Predictive modeling (market forecasts)
   - Integration with BLS official wage data

4. **Deployment** — Currently local only, could:
   - Deploy Streamlit apps to cloud (Streamlit Cloud, AWS, etc.)
   - Build REST API for data access
   - Add user authentication/accounts
   - Expand to mobile app

## File Structure

```
nursing-salary-app/
├── scraper_rolling_daily.py       # Main scraper (runs daily)
├── run_scraper_daily.ps1          # Scheduled-task launcher: logs, runs scraper, sleeps PC if unused
├── run_scraper_daily.bat          # Old launcher (no longer used by the task)
├── scraper_log.txt                # Run log written by the launcher
├── calculate_stats.py             # Stats calculation module
├── stats_dashboard.py             # Analytics dashboard
├── app_demo.py                    # Job listings dashboard
├── check_db.py                    # Database status check
├── cleanup_old_data.py            # Data cleanup utility
├── requirements.txt               # Python dependencies
├── .env                           # Supabase credentials (not in git)
├── .gitignore                     # Git exclusions
├── README.md                      # User-facing documentation
├── CLAUDE.md                      # This file
└── TLDR.md                        # Layman's summary
```

## Dependencies

Key Python packages:
- `python-jobspy` (1.2.0) — Job scraping from LinkedIn/Indeed
- `supabase` — Database client
- `streamlit` — Frontend dashboards
- `pandas` — Data manipulation
- `plotly` — Interactive charts
- `python-dotenv` — Environment config

See `requirements.txt` for complete list.

## How to Use

### For Development
```bash
# Clone repo
git clone https://github.com/drewwhitt/nursing-salary-app.git
cd nursing-salary-app

# Setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Create .env with Supabase credentials
# Add SUPABASE_URL and SUPABASE_API_KEY

# Run scraper
python scraper_rolling_daily.py

# View dashboards
streamlit run app_demo.py              # Job listings
streamlit run stats_dashboard.py       # Statistics

# Check database
python check_db.py
```

### For Production
- Runs automatically via Windows Task Scheduler at 8:00 PM daily (see Automation)
- Scrapes 5 cities per day on rotating schedule
- Data persists in Supabase, accessible to both dashboards
- To check the last run: read the tail of `scraper_log.txt`

## Contact & Questions

Project built by Drew (GitHub: @drewwhitt)
Email: andrewlouiswhittaker@gmail.com

For questions about implementation, data accuracy, or feature requests, reference this CLAUDE.md and the TLDR.md for context.