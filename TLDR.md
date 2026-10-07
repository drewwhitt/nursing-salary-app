# Nurse Explorer - Quick Summary (Layman's Terms)

## What Is This?

A tool that automatically collects real nursing job postings from the internet, extracts salary information, and shows you statistics about how much registered nurses (RNs) are being paid in different cities across the USA.

## Why Build This?

Drew wanted to create a data-driven resource to help nurses see real job market trends. Instead of guessing what nursing jobs pay in different cities, this app shows actual postings with actual salaries so nurses can make informed decisions about where to work and what to expect in terms of pay.

## How Does It Work?

### Step 1: Scraping (Automatic Daily)
Every day at 3:45 AM, the app searches LinkedIn and Indeed for nursing job postings in 5 different cities. Over a week, it cycles through 35 major US cities so you get updated data for all of them.

### Step 2: Filtering
The app is smart about what it includes:
- ✅ Only registered nurse (RN) roles — includes charge nurses, clinical nurses, nurse coordinators, case managers
- ❌ Excludes non-nursing roles — no CNAs, paramedics, LPNs, medical assistants, or nursing aides
- ❌ Excludes obviously wrong data — if a job listing says $1995/hour (clearly a typo), it gets thrown out

### Step 3: Salary Standardization
Different job postings list salaries differently:
- Some say "$55/hour"
- Some say "$114,400/year"
- Some say "$9,500/month"

The app converts ALL of these to hourly rates so they're comparable. It uses the standard 2080 hours per year (40 hours × 52 weeks).

### Step 4: Storage
All the cleaned-up job data gets saved in a database (Supabase) so it doesn't get lost.

### Step 5: Analysis & Display
Two dashboards let you explore the data:

**Dashboard 1: Job Listings** (`app_demo.py`)
- Browse all nursing jobs that were scraped
- Filter by city, salary range, job type
- See full job details and descriptions
- Compare salaries against Bureau of Labor Statistics benchmarks

**Dashboard 2: Statistics** (`stats_dashboard.py`)
- See average (mean) salary per city
- See median salary per city (the middle value)
- See salary range (highest and lowest)
- See how many jobs were found in each city
- Download the data as a spreadsheet

## Key Decisions Made

### 1. What Cities to Cover?
Started with 5, but realized that's too limiting. Expanded to 35 major US cities and added them on a rotating schedule so all 35 get updated data once per week.

**Best cities for nursing salaries (from early data):**
- Texas cities (Houston, San Antonio, Austin) offer solid pay
- Florida cities (Miami, Tampa, Orlando) competitive but vary
- Major metros (NYC, SF, Boston) generally pay more but cost of living also high

### 2. Where to Get Job Data?
Tried several options:
- **LinkedIn** ✅ — Quality professional postings
- **Indeed** ✅ — Good variety, aggregates from many sources
- ~~Glassdoor~~ ❌ — Lower quality for nursing roles
- ~~ZipRecruiter~~ ❌ — Not compatible with current tools
- Company career pages directly — Theoretically best but too complex to implement right now (would need custom scrapers for each healthcare system)

### 3. How to Handle Bad Data?
Real-world data is messy. Solutions:
- **Unknown titles** → Rejected entirely
- **Salaries outside reasonable range** ($20-$200/hr) → Rejected (catches typos)
- **Duplicate listings** → Prevented automatically (each job URL is unique)
- **Non-RN roles** → Filtered out using keyword matching

### 4. When Should It Update?
Automatic daily updates at 3:45 AM via Windows Task Scheduler. This way:
- Data stays fresh without Drew manually running it
- Scraping happens during off-peak hours (fewer network issues)
- All 35 cities get updated data once per week

## What You Can Do With It Now

1. **See nursing salary trends** — Check what RNs earn in different cities
2. **Compare cities** — Understand if paying higher pay justifies moving
3. **Track over time** — As more weeks of data accumulate, see salary trends
4. **Download data** — Export statistics to Excel for further analysis

## What It Can't Do Yet (Future Ideas)

- Doesn't account for cost of living (NYC pays more but costs more to live there)
- Doesn't track which healthcare system/employer pays best
- Doesn't show shift differentials or specialty bonuses (only base salary)
- Doesn't compare nursing specialties (ICU vs ER vs surgical, etc.)
- Doesn't predict future salary trends (yet)

## Files You Actually Care About

**To run the scraper manually:**
```
python scraper_rolling_daily.py
```

**To see job listings:**
```
streamlit run app_demo.py
```

**To see salary statistics:**
```
streamlit run stats_dashboard.py
```

**To check database status:**
```
python check_db.py
```

Everything else runs automatically or is background stuff.

## The Bottom Line

Drew built a daily automated system that pulls real nursing job data, cleans it up, and displays it in two dashboards. It's useful for nurses trying to understand job market salary trends, and for Drew to validate the concept before potentially building it into a bigger business product.

**Current status:** Working and running daily. Data quality is good. Ready to expand with more features or other nursing roles (LPNs, CNAs, etc.) if needed.