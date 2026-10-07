-- Nursing Platform Database Schema (Supabase/PostgreSQL)
-- Run this on your Supabase instance

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Jobs table: core job postings from all sources
CREATE TABLE jobs (
  job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source TEXT NOT NULL, -- 'jobspy_indeed', 'jobspy_linkedin', 'vivian', 'glassdoor', etc.
  source_job_id TEXT NOT NULL, -- Original ID from source
  url TEXT UNIQUE NOT NULL,

  -- Job details
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  facility_name TEXT, -- Specific hospital/facility name
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  zip_code TEXT,

  -- Job type & experience
  employment_type TEXT, -- 'Full Time', 'Per Diem', 'Travel', 'Contract'
  shift TEXT, -- 'Days', 'Nights', 'Rotating', '12-hour'
  specialty TEXT, -- 'Med-Surg', 'ICU', 'ER', 'PACU', etc.
  experience_required_years INT DEFAULT 0, -- 0 = new grad eligible

  -- Compensation (normalized to hourly)
  salary_min_hourly DECIMAL(8, 2),
  salary_max_hourly DECIMAL(8, 2),
  salary_period_original TEXT, -- 'hourly', 'annual', 'monthly' (for reference)
  shift_differential_hourly DECIMAL(6, 2), -- e.g., $5/hr for nights
  sign_on_bonus INT, -- dollars
  relocation_bonus INT,

  -- Description & keywords
  description TEXT, -- Full job description (for NLP later)
  description_summary TEXT, -- 2-3 sentence AI summary
  new_grad_keywords BOOLEAN, -- TRUE if contains "new grad", "residency", etc.
  residency_program BOOLEAN, -- TRUE if explicitly mentioned

  -- Metadata
  posted_at TIMESTAMP NOT NULL,
  scraped_at TIMESTAMP DEFAULT NOW(),
  archived_at TIMESTAMP, -- Jobs >30 days old
  is_active BOOLEAN DEFAULT TRUE,

  -- Indexes for performance
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_city_state ON jobs(city, state);
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_new_grad ON jobs(new_grad_keywords);
CREATE INDEX idx_jobs_active ON jobs(is_active);
CREATE INDEX idx_jobs_specialty ON jobs(specialty);
CREATE INDEX idx_jobs_posted_at ON jobs(posted_at);

-- Employers table: aggregated employer data
CREATE TABLE employers (
  employer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_name TEXT NOT NULL,
  facility_name TEXT,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  health_system TEXT, -- e.g., "HCA", "Ascension", "Vanderbilt"
  website TEXT,

  residency_program BOOLEAN DEFAULT FALSE,
  total_jobs_posted INT DEFAULT 0,
  avg_salary_hourly DECIMAL(8, 2),

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_employers_city_state ON employers(city, state);
CREATE INDEX idx_employers_health_system ON employers(health_system);

-- Wages benchmark table: official wage data by source
CREATE TABLE wages_benchmark (
  wage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source TEXT NOT NULL, -- 'BLS', 'DOL', 'Glassdoor', 'ZipRecruiter'
  occupation TEXT DEFAULT 'Registered Nurse',

  -- Geography
  state TEXT,
  metro_name TEXT,
  county TEXT,

  -- Data
  year INT NOT NULL,
  median_hourly DECIMAL(8, 2),
  p10_hourly DECIMAL(8, 2),
  p25_hourly DECIMAL(8, 2),
  p75_hourly DECIMAL(8, 2),
  p90_hourly DECIMAL(8, 2),

  -- Metadata
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wages_state_year ON wages_benchmark(state, year);
CREATE INDEX idx_wages_metro ON wages_benchmark(metro_name, year);

-- ============================================================================
-- PHASE 2: TAX & COST OF LIVING
-- ============================================================================

-- Tax rates by state & year
CREATE TABLE tax_rates (
  tax_rate_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  state TEXT NOT NULL,
  year INT NOT NULL,

  -- Federal (same for all states)
  federal_standard_deduction INT,
  federal_rate_10_threshold INT,
  federal_rate_12_threshold INT,
  federal_rate_22_threshold INT,

  -- State
  state_income_tax_rate DECIMAL(5, 3), -- 0.000 to 1.000
  state_standard_deduction INT,

  -- Special
  has_local_income_tax BOOLEAN DEFAULT FALSE,
  local_income_tax_rate DECIMAL(5, 3),

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tax_rates_state_year ON tax_rates(state, year);

-- Cost of living by metro/state
CREATE TABLE cost_of_living (
  col_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  year INT NOT NULL,

  -- Breakdown (monthly costs in USD)
  housing_median_rent INT,
  housing_median_own INT,
  food_monthly INT,
  transportation_monthly INT,
  utilities_monthly INT,
  childcare_monthly INT,
  healthcare_monthly INT,

  -- Aggregate
  monthly_total INT,
  annual_total INT,

  -- Source
  source TEXT, -- 'MIT', 'BLS', 'Zillow'

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_col_city_state ON cost_of_living(city, state, year);

-- ============================================================================
-- PHASE 3: LICENSING
-- ============================================================================

-- Nursing license requirements by state
CREATE TABLE nursing_licenses (
  license_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  state TEXT NOT NULL UNIQUE,

  -- Licensing Compact
  compact_state BOOLEAN DEFAULT FALSE,
  compact_joined_year INT,

  -- Endorsement (if moving from another state)
  endorsement_required BOOLEAN DEFAULT TRUE,
  endorsement_fee INT,
  endorsement_processing_days INT,

  -- New RN application
  rn_application_fee INT,
  rn_processing_days INT,
  rn_temporary_license BOOLEAN DEFAULT FALSE,

  -- Continuing education (per license renewal)
  ce_hours_required INT DEFAULT 0,
  ce_renewal_cost INT DEFAULT 0,

  -- Board of Nursing contact
  bon_website TEXT,
  bon_phone TEXT,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_licenses_state ON nursing_licenses(state);
CREATE INDEX idx_licenses_compact ON nursing_licenses(compact_state);

-- ============================================================================
-- PHASE 4+: USER ACCOUNTS & PREFERENCES
-- ============================================================================

-- User accounts (for freemium model)
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,

  -- Profile
  first_name TEXT,
  last_name TEXT,
  graduation_year INT,
  specialty TEXT,

  -- Subscription
  subscription_plan TEXT DEFAULT 'free', -- 'free', 'premium'
  subscription_started_at TIMESTAMP,
  subscription_ends_at TIMESTAMP,

  -- Preferences
  preferred_cities TEXT[], -- Array of city preferences
  preferred_specialties TEXT[],
  preferred_shift TEXT[],

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription ON users(subscription_plan);

-- Saved jobs / favorites
CREATE TABLE saved_jobs (
  saved_job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(job_id) ON DELETE CASCADE,

  saved_at TIMESTAMP DEFAULT NOW(),
  notes TEXT
);

CREATE INDEX idx_saved_jobs_user ON saved_jobs(user_id);

-- City comparison history (for analytics)
CREATE TABLE city_comparisons (
  comparison_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
  cities_compared TEXT[], -- Array of city names
  viewed_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================================

-- View: New-grad jobs in a city with normalized compensation
CREATE VIEW new_grad_jobs_by_city AS
SELECT
  j.city,
  j.state,
  COUNT(*) as total_jobs,
  COUNT(*) FILTER (WHERE j.new_grad_keywords = TRUE) as new_grad_friendly_count,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY j.salary_max_hourly) as median_salary_hourly,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY j.salary_max_hourly) as p25_salary,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY j.salary_max_hourly) as p75_salary,
  MIN(j.posted_at) as oldest_posting,
  MAX(j.posted_at) as newest_posting
FROM jobs j
WHERE j.is_active = TRUE
  AND j.experience_required_years <= 0
  AND j.posted_at > NOW() - INTERVAL '30 days'
GROUP BY j.city, j.state;

-- View: Employers hiring new grads
CREATE VIEW employers_hiring_new_grads AS
SELECT
  e.employer_id,
  e.company_name,
  e.facility_name,
  e.city,
  e.state,
  e.health_system,
  COUNT(j.job_id) as active_jobs,
  COUNT(*) FILTER (WHERE j.new_grad_keywords = TRUE) as new_grad_jobs
FROM employers e
LEFT JOIN jobs j ON j.company = e.company_name
  AND j.city = e.city
  AND j.is_active = TRUE
GROUP BY e.employer_id;

-- ============================================================================
-- ARCHIVE & MAINTENANCE
-- ============================================================================

-- Function to archive old jobs (>30 days)
CREATE OR REPLACE FUNCTION archive_old_jobs()
RETURNS void AS $$
BEGIN
  UPDATE jobs
  SET archived_at = NOW(), is_active = FALSE
  WHERE posted_at < NOW() - INTERVAL '30 days'
    AND archived_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Schedule this to run daily via cron (Supabase Extensions > Cron)
-- SELECT cron.schedule('archive_old_jobs', '0 0 * * *', 'SELECT archive_old_jobs()');

-- ============================================================================
-- INITIAL DATA: Tax rates 2026 (Federal)
-- ============================================================================

INSERT INTO tax_rates (state, year, federal_standard_deduction, federal_rate_10_threshold, federal_rate_12_threshold, federal_rate_22_threshold, state_income_tax_rate, state_standard_deduction)
VALUES
  ('TN', 2026, 16100, 11000, 44725, 95375, 0.0, 0),
  ('TX', 2026, 16100, 11000, 44725, 95375, 0.0, 0),
  ('FL', 2026, 16100, 11000, 44725, 95375, 0.0, 0),
  ('WA', 2026, 16100, 11000, 44725, 95375, 0.0, 0),
  ('NV', 2026, 16100, 11000, 44725, 95375, 0.0, 0),
  ('CA', 2026, 16100, 11000, 44725, 95375, 0.093, 5202),
  ('NY', 2026, 16100, 11000, 44725, 95375, 0.065, 4000),
  ('CO', 2026, 16100, 11000, 44725, 95375, 0.046, 0),
  ('IL', 2026, 16100, 11000, 44725, 95375, 0.0495, 0),
  ('MA', 2026, 16100, 11000, 44725, 95375, 0.050, 6100);

-- ============================================================================
-- INITIAL DATA: Nursing Licenses (sample)
-- ============================================================================

INSERT INTO nursing_licenses (state, compact_state, endorsement_fee, endorsement_processing_days, rn_application_fee, rn_processing_days, rn_temporary_license)
VALUES
  ('TN', TRUE, 100, 14, 150, 7, TRUE),
  ('TX', TRUE, 75, 14, 150, 7, TRUE),
  ('FL', TRUE, 100, 14, 150, 7, TRUE),
  ('CA', FALSE, 200, 30, 250, 14, FALSE),
  ('NY', FALSE, 175, 21, 225, 14, FALSE),
  ('CO', TRUE, 90, 14, 140, 7, TRUE),
  ('IL', FALSE, 120, 14, 160, 7, TRUE),
  ('WA', TRUE, 80, 14, 120, 7, TRUE),
  ('MA', FALSE, 150, 21, 200, 14, FALSE),
  ('PA', FALSE, 160, 21, 200, 14, FALSE);
