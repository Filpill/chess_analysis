DECLARE start_date     DATE    DEFAULT  '2025-04-01';
DECLARE end_date       DATE    DEFAULT  '2025-04-30';
DECLARE milli_to_base  FLOAT64 DEFAULT  0.001;
DECLARE base_to_mega   INT64   DEFAULT  1000000;
DECLARE base_to_giga   INT64   DEFAULT  1000000000;
DECLARE script_setting STRING;

SET script_setting = "project";

WITH cte_jobs_base AS (
  SELECT
        creation_time
      , EXTRACT(DATE FROM creation_time)                   AS job_created_date
      , DATE_TRUNC(EXTRACT(DATE FROM creation_time),MONTH) AS job_created_month
      , project_id
      , user_email
      , job_id
      , start_time
      , end_time
      , job_type
      , statement_type
      , priority
      , query
      , cache_hit
      , TIMESTAMP_DIFF(end_time, start_time, MILLISECOND)  AS total_query_time_ms
      , total_slot_ms
      , total_bytes_processed
      , total_bytes_billed
  FROM `checkmate-453316`.`region-eu`.INFORMATION_SCHEMA.JOBS jbp
  WHERE
    EXTRACT(DATE FROM end_time) BETWEEN start_date AND end_date
)

, cte_user_level_aggregate AS (
  SELECT 
        project_id
      , job_created_date
      , user_email
      , COUNT(*)                                               AS number_of_queries
      , ROUND(SUM(total_query_time_ms) * milli_to_base   , 1)  AS total_query_time_seconds
      , ROUND(SUM(total_slot_ms) * milli_to_base         , 1)  AS total_slot_seconds
      , ROUND(SUM(total_bytes_processed) / base_to_mega  , 1)  AS total_megabytes_processed
      , ROUND(SUM(total_bytes_billed) / base_to_mega     , 1)  AS total_megabytes_billed
  FROM cte_jobs_base
  GROUP BY ALL
  ORDER BY job_created_date ASC
)

, cte_project_level_aggregate AS (
  SELECT
        project_id
      , job_created_month
      , COUNT(*)                                                AS number_of_queries
      , ROUND(SUM(total_slot_ms) * milli_to_base         , 1)   AS total_slot_seconds
      , ROUND(SUM(total_bytes_billed) / base_to_giga     , 1)   AS total_gigabytes_billed
      , SUM(total_bytes_billed) / base_to_giga / 1000 * 100     AS free_process_consumed_percentage
  FROM cte_jobs_base
  GROUP BY ALL
  ORDER BY job_created_month ASC
)

-- SELECT * FROM cte_jobs_base;
-- SELECT * FROM cte_user_level_aggregate;
SELECT * FROM cte_project_level_aggregate;
