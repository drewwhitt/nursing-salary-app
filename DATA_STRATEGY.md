# Data Strategy: Robust, Reliable Nursing Job & Compensation Data

## Overview

This document outlines the multi-layered data strategy for the Nursing Compensation Explorer platform. The goal: **reliable, validated data that nursing students can trust**.

## Data Sources Hierarchy

### **Tier 1: Authoritative Benchmarks (Ground Truth)**

These are official, government-backed sources that validate all other data.

#### 1.1 BLS Wage Data (Bureau of Labor Statistics)
- **Coverage**: RN wages (OES 29-1141) by state and metro area
- **Update Frequency**: Quarterly
- **Source**: https://www.bls.gov/oes/
- **What it provides**:
  - Median hourly wages
  - 10th, 25th, 75th, 90th percentile wages
  - By state and major metro areas
- **Why we use it**: Government survey data, authoritative, consistent methodology
- **Table**: `wages_benchmark` (source = 'BLS')
- **Status**: ✅ Pre-populated in `scraper_robust.py`

#### 1.2 DOL Prevailing Wage Database
- **Coverage**: County-level prevailing wage rates for healthcare
- **Update Frequency**: Annual
- **Source**: https://sam.gov/content/dol-prevailing-wage
- **What it provides**:
  - Minimum wage rates for federal contracts (many hospitals are federal contractors)
  - County-level granularity
- **Why we use it**: Regulatory baseline, especially for hospital networks
- **Table**: `wages_benchmark` (source = 'DOL')
- **Status**: 🔄 To be added (Phase 2)

---

### **Tier 2: Primary Job Posting Data**

Jobs posted directly by hospitals (higher quality than job boards).

#### 2.1 ATS API Scraping (Recommended)

Instead of scraping job board UIs, we scrape hospital career pages directly via their Applicant Tracking System APIs.

**ATS Platforms Identified in Your 30 Cities**:

| ATS Platform | Hospitals/Systems | Coverage |
|---|---|---|
| **Workday** | Cleveland Clinic, Emory, UCSF, Stanford, UC San Diego, Mayo, UMN Health, Allina, Swedish, Providence, Jackson, UT Health, UWisconsin Health, UNC/Wake Forest | ~15 systems, ~40% of job volume |
| **iCIMS** | OHSU, Lurie Children's, Novant Health, Grady, Ascension, Baptist Health Miami, Children's National, Cincinnati Children's, Ascension Wisconsin | ~9 systems, ~20% of job volume |
| **Greenhouse** | Vanderbilt, Duke, UPenn Health, others | ~5 systems, ~15% of job volume |
| **Custom Platforms** | Mayo Clinic, Johns Hopkins, Houston Methodist, UCSF, Cleveland Clinic, Valley Health, Denver Health, Cincinnati Children's, IU Health, Froedtert | ~10 systems, ~25% of job volume |

**Advantages**:
- Direct from source (no middleman)
- Structured JSON/XML APIs (no HTML parsing fragility)
- More complete metadata (department, specialty, experience level)
- Real-time updates

**How It Works**:
```
Hospital Career Page
    ↓
ATS API Endpoint
    ↓
Our Scraper (scraper_robust.py)
    ↓
Normalized Jobs Table
```

**Implementation Status**:
- ✅ `health_systems.json` maps all 30 cities to top hospital systems + ATS platform
- 🔄 ATS-specific scrapers in `scraper_robust.py` (Greenhouse, Workday, iCIMS)
- 🔄 Needs: API authentication for some platforms (may require registration)

---

#### 2.2 JobSpy Aggregation (Fallback)

Aggregates major job boards (Indeed, LinkedIn, Glassdoor, ZipRecruiter) for jobs not caught by ATS scraping.

**Why it's a fallback**:
- Covers jobs posted to boards but not hospital career pages
- Catches smaller regional hospitals, staffing agencies
- More resilient (if one source breaks, others continue)

**Advantages**:
- Well-maintained open-source library
- Normalized output across sources

**Limitations**:
- Depends on job boards not blocking our scraper
- May catch non-RN roles ("nurse" keyword match includes CNAs, LPNs, etc.)
- Less structured data than direct ATS

**Implementation Status**: ✅ Already in both `scraper.py` and `scraper_robust.py`

---

### **Tier 3: Validation & Deduplication**

#### 3.1 Salary Normalization
All salary data converted to hourly format for comparison:
- Annual → ÷ 2,080 hours/year
- Monthly → × 12 months, then ÷ 2,080
- Hourly → kept as-is

#### 3.2 New-Grad Detection
Jobs classified as new-grad friendly if description contains:
- "new grad", "new graduate", "graduate nurse"
- "nurse residency", "residency program"
- "0 years experience", "entry level"
- "nurse fellowship", "graduate nurse program"

#### 3.3 Bonus & Differential Extraction
- Sign-on bonuses (e.g., "$5,000 sign-on bonus")
- Shift differentials (e.g., "$5/hr night shift differential")
- Parsed from job descriptions via regex

#### 3.4 Deduplication by URL
- Jobs deduplicated by URL (primary key)
- Prevents double-counting same job from multiple sources
- Keeps first occurrence (usually most complete)

---

## Data Quality Checks

### Validation Against BLS Benchmarks

After scraping and normalizing, we validate the data:

```python
def validate_against_bls(city, state, scraped_data):
    """
    Compare scraped salaries against BLS benchmark.
    Flag outliers.
    """
    bls_median = get_bls_median(city, state)
    scraped_median = calculate_median_salary(scraped_data)
    
    variance = abs(scraped_median - bls_median) / bls_median
    
    if variance > 0.25:  # >25% difference
        logger.warning(f"Large variance in {city}: BLS=${bls_median:.2f}, Scraped=${scraped_median:.2f}")
        # Flag for manual review
```

**Why this matters**:
- If your scraped data shows Nashville RNs at $65/hr but BLS says $37/hr median, something is wrong
- Helps catch:
  - Specialty roles only (ER/ICU pay more)
  - Duplicates (same job listed twice)
  - Data quality issues

---

## Database Schema

### `jobs` Table
Core job postings with normalized salary, location, experience level, keywords.

**Key Fields**:
```
source                  -- 'ats_greenhouse', 'ats_workday', 'jobspy_indeed', etc.
source_job_id           -- Original ID from source system
url                     -- Unique identifier
title, company, city, state
salary_min_hourly       -- Normalized hourly minimum
salary_max_hourly       -- Normalized hourly maximum
salary_period_original  -- Original format (annual/monthly/hourly) for reference
shift_differential_hourly
sign_on_bonus
description             -- Full text
description_summary     -- AI-generated 2-3 sentence summary
new_grad_keywords       -- Boolean: is this job new-grad friendly?
posted_at, scraped_at
is_active               -- Soft delete (marked inactive, not actually deleted)
```

### `wages_benchmark` Table
Official wage data for validation.

```
source                  -- 'BLS', 'DOL'
occupation              -- 'Registered Nurse'
state, metro_name, county
year                    -- 2025, 2026
median_hourly, p10_hourly, p25_hourly, p75_hourly, p90_hourly
```

### `employers` Table
Aggregated employer/hospital data.

```
company_name, facility_name, city, state, health_system
residency_program       -- Boolean
total_jobs_posted       -- Count of active jobs
avg_salary_hourly       -- Average of posted jobs
```

---

## Scraper Architecture

### `scraper_robust.py`

**Execution Order**:

```
1. Fetch BLS benchmarks
   └─ Insert into wages_benchmark table
   
2. Scrape ATS platforms
   ├─ Greenhouse JSON API
   ├─ Workday career pages
   ├─ iCIMS pages
   └─ Custom platforms (BeautifulSoup)
   
3. Scrape JobSpy fallback
   └─ Indeed, LinkedIn, Glassdoor, ZipRecruiter aggregation
   
4. Normalize & Deduplicate
   ├─ Convert all salaries to hourly
   ├─ Detect new-grad keywords
   ├─ Extract bonuses & differentials
   ├─ Generate summaries
   └─ Deduplicate by URL
   
5. Validate Against BLS
   └─ Flag outliers for review
   
6. Insert into Supabase
   └─ Upsert jobs (update if exists, insert if new)
```

**Run Frequency**:
- **Weekly via GitHub Actions**: Monday 2 AM UTC
- **Manual**: `python scraper_robust.py` anytime

**Data Retention**:
- Jobs older than 30 days marked as `is_active = FALSE`
- After 90 days, consider archiving to separate table (for trend analysis)

---

## Phase Rollout

### **Phase 1 (Week 1-2): MVP Data Foundation**
- ✅ BLS wage benchmarks (pre-populated)
- ✅ ATS API scrapers (Workday, iCIMS, Greenhouse, custom)
- ✅ JobSpy fallback aggregation
- ✅ Salary normalization & deduplication
- ✅ Streamlit MVP with salary/COL/tax calculations

### **Phase 2 (Week 3-4): Enhanced Validation**
- 🔄 DOL prevailing wage data
- 🔄 BLS validation checks
- 🔄 Historical trend tracking (weekly snapshots)
- 🔄 Data quality dashboard

### **Phase 3 (Post-launch): Expansion**
- 🔄 Additional ATS platforms (SmartRecruiters, Lever, Ashby)
- 🔄 Employer metadata enrichment (rating, residency programs)
- 🔄 County-level expansion (beyond 30 cities)
- 🔄 Employee-reported salary data (Glassdoor, separate flow)

---

## Known Limitations & Mitigations

| Limitation | Impact | Mitigation |
|---|---|---|
| ATS authentication | Some platforms may require credentials | Use public APIs first; register for access if needed |
| Job board blocking | JobSpy may be rate-limited or blocked | Implement exponential backoff; fallback to manual sampling |
| Custom platforms | Each hospital may have unique structure | Maintain `health_systems.json` mapping; custom BeautifulSoup rules per system |
| New-grad detection | Regex-based keyword matching imperfect | Future: NLP/ML model; for now, manual review of edge cases |
| Salary completeness | Not all jobs post salary ranges | Use BLS median as fill-in for missing data; flag incomplete listings |
| Geographic coverage | Only 30 cities in MVP | Systematic expansion after validation in phase 1 |

---

## Data Governance

### Update Frequency

| Source | Frequency | Trigger |
|---|---|---|
| BLS Wage Data | Quarterly | Manual (when BLS updates) |
| DOL Prevailing Wage | Annual | Manual (when DOL updates) |
| Job Postings (ATS + JobSpy) | Weekly | GitHub Actions (Monday 2 AM UTC) |
| Employer Aggregates | Weekly | Recalculated from job postings |

### Data Quality Monitoring

1. **Weekly Scraper Report**
   - Jobs scraped per city
   - Average salary by city vs. BLS
   - New-grad job count
   - Top employers

2. **Validation Checks**
   - Salary outliers (>25% variance from BLS)
   - Missing salary data (percentage)
   - Duplicate jobs (deduplicated count)

3. **Manual Spot Checks**
   - Sample 10 jobs per city
   - Verify salary accuracy
   - Verify new-grad classification
   - Check for spam/fake listings

---

## Tools & Dependencies

```
requirements.txt additions for robust scraper:
- jobspy==4.2.4           # Job board aggregation
- beautifulsoup4==4.12.3  # HTML parsing for custom platforms
- requests==2.31.0        # HTTP requests
- polars==0.20.31         # Data transformation (faster than pandas)
- supabase==2.4.3         # Database
```

---

## Success Criteria

✅ **MVP Launch (Week 4)**:
1. BLS benchmarks loaded and correct
2. ATS scraping working for 2-3 major platforms
3. JobSpy fallback catching jobs not on ATS
4. Salary data validated against BLS (variance <20%)
5. New-grad classification >80% accurate (spot checks)
6. Weekly scraper runs successfully

✅ **After 4 Weeks of Data Collection**:
1. Trend data showing salary/job count changes
2. Validation dashboard showing data quality metrics
3. No critical data quality issues
4. User feedback on accuracy and usefulness

---

## Questions & Next Steps

1. **ATS API Access**: Some platforms (Workday, iCIMS) may require registration. Should I register for test accounts?
2. **Custom Platform Reverse Engineering**: For hospitals with custom careers pages (Mayo, Hopkins, etc.), how deep should we go on HTML parsing?
3. **BLS Data Refresh**: Should I add code to auto-fetch latest BLS data quarterly, or update manually?
4. **Validation Thresholds**: If a city shows >25% variance from BLS, should we flag or auto-correct?

---

**Version**: 1.0  
**Last Updated**: 2026-10-06  
**Owner**: Drew (alwhittaker94@gmail.com)
