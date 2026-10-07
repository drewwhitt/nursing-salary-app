# 🏥 Nursing Job & Compensation Explorer

A data-driven platform to help nursing students understand where they can achieve the best quality of life after graduation. Aggregates job postings, salary data, cost of living, state taxes, and licensing requirements across 30+ US cities.

## 🎯 Problem Statement

Nursing graduates face a critical decision: where should I take my first job? They need more than just salary information—they need to understand:

- **What employers are actually offering** (salary, shift type, bonuses)
- **What I'll actually keep** (after federal taxes, state taxes, FICA)
- **What it costs to live there** (housing, food, transportation, healthcare)
- **How difficult is it to get licensed** (compact state? endorsement fees? timeline?)
- **How many realistic opportunities exist** for new graduates

This platform aggregates these data sources into one unified, comparative view.

## 🗺️ Current Geographic Coverage

**30 Priority Cities** (ranked by nursing job density + market opportunity):

| Rank | City | State | Est. New-Grad Jobs |
|------|------|-------|--------------------|
| 1 | Nashville | TN | 250+ |
| 2 | Dallas | TX | 400+ |
| 3 | Charlotte | NC | 200+ |
| 4 | Denver | CO | 180+ |
| 5 | Phoenix | AZ | 220+ |
| 6 | Houston | TX | 500+ |
| 7 | Atlanta | GA | 320+ |
| 8 | Austin | TX | 150+ |
| 9 | Indianapolis | IN | 140+ |
| 10 | Chicago | IL | 280+ |

...and 20 more cities from major metros to secondary markets.

See [`CITIES.md`](./CITIES.md) for full list and rationale.

## 🏗️ Architecture

```
JOB SOURCES (JobSpy aggregation)
├── Indeed
├── LinkedIn
├── Glassdoor
└── ZipRecruiter

    ↓

VIVIAN HEALTH (Healthcare-specific)
(BeautifulSoup/Selenium scraping)

    ↓

NORMALIZATION LAYER
├── Salary conversion (hourly/annual/monthly → hourly)
├── New-grad keyword detection
├── Shift differential extraction
├── Sign-on bonus parsing
└── Job description summarization

    ↓

DEDUPLICATION (by URL)

    ↓

POSTGRESQL / SUPABASE
├── jobs table
├── employers table
├── wages_benchmark table (BLS, DOL, Glassdoor)
├── cost_of_living table
├── tax_rates table
├── nursing_licenses table
└── users table (freemium auth)

    ↓

ANALYTICS LAYER
├── Tax calculation (federal + state)
├── Take-home pay estimation
├── COL-adjusted salary comparison
├── New-grad scoring
└── City comparisons

    ↓

FRONTEND (MVP: Streamlit → Production: React)
```

## 🛠️ Technology Stack

### Backend
- **Language**: Python 3.10+
- **Scraping**: `jobspy`, `beautifulsoup4`, `selenium`
- **Data Processing**: `polars`, `pandas`, `numpy`
- **Database**: Supabase (PostgreSQL)
- **Scheduling**: GitHub Actions (weekly cron)

### Frontend (MVP)
- **Framework**: Streamlit
- **Visualization**: Plotly
- **Auth**: In-app (freemium model)

### Frontend (Production, v2+)
- **Framework**: React 18+
- **UI Library**: TailwindCSS / shadcn/ui
- **State**: React Query / Zustand
- **Auth**: Supabase Auth

## 📊 Database Schema

### Core Tables
- **jobs**: Job postings with normalized salary, location, experience level, new-grad keywords
- **employers**: Aggregated employer data (company, facility, health system, residency program status)
- **wages_benchmark**: Official wage benchmarks (BLS, DOL, Glassdoor, ZipRecruiter)
- **cost_of_living**: Monthly/annual living costs by city (housing, food, transportation, etc.)
- **tax_rates**: Federal and state tax brackets, standard deductions (2026+)
- **nursing_licenses**: State licensing requirements (compact status, endorsement fees, processing times)
- **users**: Freemium user accounts with preferences
- **saved_jobs**: User job bookmarks (premium feature)

See [`schema.sql`](./schema.sql) for full DDL.

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repo-url>
cd nursing_platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Supabase Setup
- Create a Supabase project at https://supabase.com
- Run [`schema.sql`](./schema.sql) in the Supabase SQL editor
- Get your Supabase URL and API key

### 3. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

### 4. Run the Scraper (One-Time)
```bash
python scraper.py
```

This will:
- Scrape JobSpy (Indeed, LinkedIn, Glassdoor, ZipRecruiter) for all 30 cities
- Scrape Vivian Health for healthcare-specific jobs
- Normalize all salary data to hourly format
- Extract new-grad keywords, bonuses, shift differentials
- Deduplicate by URL
- Insert into Supabase

**Note**: First run may take 5-10 minutes. Subsequent runs (weekly via GitHub Actions) are incremental.

### 5. Run the Streamlit App (MVP)
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

## 📱 User Features

### Public (Freemium)
- ✅ Browse 30 cities
- ✅ View job listings by city
- ✅ Basic salary statistics
- ✅ Cost of living overview
- ✅ Licensing requirements
- ✅ Account signup/login

### Premium
- 🔒 Detailed salary comparisons with charts
- 🔒 Advanced job filtering (specialty, shift, experience level)
- 🔒 Side-by-side city comparisons
- 🔒 Personalized recommendations
- 🔒 Job alerts
- 🔒 Save jobs for later

## 🔄 Data Pipeline

### Weekly Scrape (GitHub Actions)
Every Monday at 2 AM UTC:

1. **JobSpy Aggregation**
   - Queries Indeed, LinkedIn, Glassdoor, ZipRecruiter for "registered nurse" jobs
   - Normalizes salary fields
   - Captures full job descriptions

2. **Vivian Health Scraping**
   - BeautifulSoup crawl of Vivian job listings
   - Healthcare-specific data extraction
   - Real-time pay transparency

3. **Normalization & Deduplication**
   - Convert all salaries to hourly
   - Detect new-grad keywords
   - Extract sign-on bonuses, shift differentials
   - Deduplicate by URL

4. **Supabase Insertion**
   - Upsert jobs (insert if new, update if exists)
   - Archive jobs older than 30 days
   - Maintain historical trend data

5. **Monitoring**
   - GitHub Actions logs
   - Supabase activity tracking
   - Optional: Email alerts on failures

## 🔮 Roadmap

### Phase 1 (MVP - Week 4)
- ✅ PostgreSQL schema (Supabase)
- ✅ JobSpy + Vivian scraping
- ✅ Salary normalization & deduplication
- ✅ GitHub Actions weekly schedule
- ✅ Streamlit UI (city explorer, job search, basic calculations)
- ✅ Freemium auth (signup/login)
- Tax calculation engine
- Cost of living integration
- Nursing license data

### Phase 2 (Expand Data - Months 2-3)
- Direct ATS ingestion (Greenhouse, Lever, Workday, SmartRecruiters)
- BLS wage benchmark integration
- DOL prevailing wage data
- MIT Living Wage Calculator integration
- State-by-state licensing details
- Enhance new-grad keyword detection with NLP

### Phase 3 (Production UI - Months 3-4)
- React frontend with TailwindCSS
- Advanced filtering & search
- Salary comparison charts
- Job alert subscriptions
- Saved jobs feature (premium)
- Personalized recommendations

### Phase 4 (Enhancement - Months 4+)
- Expand to 50+ metros + county-level data
- Employer reviews & ratings
- Real-time job notifications
- Mobile app (React Native)
- Healthcare economy insights
- Predictive job market trends

## 📈 Key Metrics

The platform tracks:

- **Nursing job density** by city (jobs per capita)
- **New-grad job availability** (jobs explicitly welcoming new graduates)
- **Salary distribution** (p25, median, p75, p90)
- **Cost of living index** (vs. national baseline)
- **Tax burden** (state income tax as % of salary)
- **Net disposable income** after taxes and living costs
- **Licensing friction** (endorsement costs, processing time)

## 🤝 Contributing

Contributions welcome! Areas for help:

- Additional data sources (hospital career pages, health system APIs)
- Frontend design/UX improvements
- Job description NLP (better new-grad detection)
- Geographic expansion (secondary metros, counties)
- Testing & performance optimization

## 📝 License

MIT License - See LICENSE file

## 👨‍💻 Development Notes

### Local Testing
```bash
# Run scraper with logging
python scraper.py

# Run Streamlit app
streamlit run app.py

# Clear Streamlit cache
streamlit cache clear
```

### Database Queries
```sql
-- Check latest jobs
SELECT city, state, COUNT(*) as job_count, 
  AVG(salary_max_hourly) as avg_max_salary
FROM jobs 
WHERE is_active = TRUE 
  AND posted_at > NOW() - INTERVAL '7 days'
GROUP BY city, state
ORDER BY job_count DESC;

-- Archive old jobs
SELECT archive_old_jobs();
```

### Debugging
- Check GitHub Actions logs for scraper failures
- View Supabase SQL editor for data integrity
- Use Streamlit's `st.write()` for debugging UI

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: alwhittaker94@gmail.com

---

**Note**: This is an MVP. Data completeness and freshness improve over time as the scraper aggregates more sources and captures historical trends.
