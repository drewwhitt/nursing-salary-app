-- City pay statistics at 40 hours/week (2,080 hours/year).
-- Stored annual and monthly pay is at 1,872 hours, so it is rescaled
-- by 1,872 / 2,080 to get the 40-hour rate. Hourly postings are unchanged.
-- Pay per posting = midpoint of posted min and max hourly pay.
-- Middle 90% = 5th to 95th percentile of pay per posting.

CREATE OR REPLACE VIEW city_pay_stats_40 AS
WITH base AS (
  SELECT
    city,
    state,
    CASE
      WHEN salary_period_original IN ('yearly', 'annual', 'year', 'monthly')
        THEN ((salary_min_hourly + salary_max_hourly) / 2) * 1872 / 2080
      ELSE (salary_min_hourly + salary_max_hourly) / 2
    END AS pay
  FROM jobs
  WHERE is_active = true
    AND salary_min_hourly IS NOT NULL
    AND salary_max_hourly IS NOT NULL
),
bounds AS (
  SELECT
    city,
    state,
    COUNT(*) AS jobs_with_pay,
    percentile_cont(0.05) WITHIN GROUP (ORDER BY pay) AS p05,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY pay) AS p95
  FROM base
  GROUP BY city, state
)
SELECT
  b.city,
  b.state,
  b.jobs_with_pay,
  COUNT(r.pay) AS jobs_after_trim,
  ROUND(percentile_cont(0.5) WITHIN GROUP (ORDER BY r.pay)::numeric, 2) AS median_hourly,
  ROUND(b.p05::numeric, 2) AS middle90_low,
  ROUND(b.p95::numeric, 2) AS middle90_high,
  CASE WHEN b.jobs_with_pay < 30 THEN 'insufficient' ELSE 'ok' END AS status
FROM bounds b
LEFT JOIN base r
  ON r.city = b.city AND r.state = b.state
 AND r.pay BETWEEN b.p05 AND b.p95
GROUP BY b.city, b.state, b.jobs_with_pay, b.p05, b.p95;

GRANT SELECT ON city_pay_stats_40 TO anon;