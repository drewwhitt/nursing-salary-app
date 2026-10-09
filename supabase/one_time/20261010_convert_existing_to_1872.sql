-- ONE-TIME UPDATE. Run once in the Supabase SQL Editor, before the next scrape.
-- Do NOT place this in supabase/migrations/ (migration tools would re-run it).
--
-- Rows scraped before the scraper change converted annual and monthly pay at
-- 2,080 hours. This rescales them to 1,872 hours so all stored values match.
-- Rows already converted at 1,872 must not be rescaled again, so the cutoff
-- below must be the time the new scraper was first deployed.

-- Step 1: back up the table so the change can be reversed.
CREATE TABLE IF NOT EXISTS jobs_backup_pre_1872 AS
SELECT * FROM jobs;

-- Step 2: set the deployment time (edit this before running).
-- Replace the timestamp with the time you first ran the new scraper, in UTC.
-- Example: '2026-10-10 14:00:00'
DO $$
DECLARE
  cutoff timestamp := '2026-10-10 00:00:00';  -- EDIT THIS
  updated_count integer;
BEGIN
  UPDATE jobs
  SET
    salary_min_hourly = salary_min_hourly * 2080 / 1872,
    salary_max_hourly = salary_max_hourly * 2080 / 1872,
    updated_at = NOW()
  WHERE salary_period_original IN ('yearly', 'annual', 'year', 'monthly')
    AND scraped_at < cutoff;

  GET DIAGNOSTICS updated_count = ROW_COUNT;
  RAISE NOTICE 'Rows rescaled to 1,872 hours: %', updated_count;
END $$;

-- To reverse this, restore from the backup table (run only if needed):
-- UPDATE jobs j
-- SET salary_min_hourly = b.salary_min_hourly,
--     salary_max_hourly = b.salary_max_hourly,
--     updated_at = b.updated_at
-- FROM jobs_backup_pre_1872 b
-- WHERE j.job_id = b.job_id;