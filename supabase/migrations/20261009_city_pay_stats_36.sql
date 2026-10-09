-- City pay statistics at 36 hours/week (1,872 hours/year).
-- Pay per posting = midpoint of posted min and max hourly pay.
-- Annual and monthly postings were stored at 2,080 hours, so they are
-- rescaled by 2,080 / 1,872. Hourly postings are unchanged.
-- Middle 90% = 5th to 95th percentile of pay per posting.

CREATE OR REPLACE VIEW city_pay_stats_36 AS
WITH base AS (
  SELECT
    city,
    state,
    CASE
      WHEN salary_period_original IN ('yearly', 'monthly')
        THEN ((salary_min_hourly + salary_max_hourly) / 2) * 2080 / 1872
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

-- Only needed if the public site reads this view with the anon key.
GRANT SELECT ON city_pay_stats_36 TO anon;