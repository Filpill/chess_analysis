{{ config(materialized='table') }}
{% set is_dev = target.name == 'dev' %}

WITH cte_date_array AS (
    SELECT
      DATE_SUB(CURRENT_DATE(), INTERVAL x DAY) AS cal_date
    FROM
      UNNEST(GENERATE_ARRAY(0, 365 *10)) AS x
),

cte_apply_formatting AS (
    SELECT
          cal_date
        , EXTRACT(DAY FROM cal_date)                                      AS day_digit
        , EXTRACT(MONTH FROM cal_date)                                    AS month_digit
        , EXTRACT(YEAR FROM cal_date)                                     AS year_digit
        , FORMAT_DATE('%B', cal_date)                                     AS month_name

        /*Monthly Formats*/
        , DATE_TRUNC(cal_date, MONTH)                                     AS month_start_date
        , DATE_SUB(
              DATE_TRUNC(DATE_ADD(cal_date, INTERVAL 1 MONTH), MONTH),
              INTERVAL 1 DAY
          )                                                               AS month_end_date
        , FORMAT_DATE('%b-%y', DATE_TRUNC(cal_date, MONTH))               AS month_year_type1
        , FORMAT_DATE('%B %Y', DATE_TRUNC(cal_date, MONTH))               AS month_year_type2

          /*Weekly Formats - Mon to Sun*/
        , "Week " || EXTRACT(ISOWEEK FROM cal_date)                       AS iso_week_number_type1
        , EXTRACT(ISOWEEK FROM cal_date)                                  AS iso_week_number_type2
        , DATE_TRUNC(cal_date, ISOWEEK)                                   AS iso_week_start
        , DATE_ADD(DATE_TRUNC(cal_date, ISOWEEK), INTERVAL 6 DAY)         AS iso_week_end

          /*Weekly Formats - Sun to Sat*/
        , "Week " || EXTRACT(WEEK(SUNDAY)  FROM cal_date)                 AS week_number_type1
        , EXTRACT(WEEK(SUNDAY)    FROM cal_date)                          AS week_number_type2
        , DATE_TRUNC(cal_date, WEEK(SUNDAY))                              AS week_start_date
        , DATE_ADD(DATE_TRUNC(cal_date, WEEK(SUNDAY)), INTERVAL 6 DAY)    AS week_end_date
    FROM cte_date_array

)

SELECT * FROM cte_apply_formatting
ORDER BY cal_date DESC
