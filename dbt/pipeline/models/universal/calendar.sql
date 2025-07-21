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

          /* Extracting Basic Attibutes */
          cal_date
        , EXTRACT(DAY          FROM cal_date)                                                   AS day
        , EXTRACT(WEEK(SUNDAY) FROM cal_date)                                                   AS week
        , EXTRACT(ISOWEEK      FROM cal_date)                                                   AS iso_week
        , EXTRACT(MONTH        FROM cal_date)                                                   AS month
        , EXTRACT(QUARTER      FROM cal_date)                                                   AS quarter
        , EXTRACT(YEAR         FROM cal_date)                                                   AS year
        , FORMAT_DATE('%B', cal_date)                                                           AS month_name

        /*Quarterly Format*/
        , FORMAT_DATE('%Y-Q%Q', cal_date)                                                       AS year_quarter
        , DATE_TRUNC(cal_date, QUARTER)                                                         AS quarter_start_date
        , DATE_SUB(
              DATE_TRUNC(DATE_ADD(cal_date, INTERVAL 1 QUARTER), QUARTER),
              INTERVAL 1 DAY
          )                                                                                     AS quarter_end_date

        /* Monthly Formats */
        , DATE_TRUNC(cal_date, MONTH)                                                           AS month_start_date
        , DATE_SUB(
              DATE_TRUNC(DATE_ADD(cal_date, INTERVAL 1 MONTH), MONTH),
              INTERVAL 1 DAY
          )                                                                                     AS month_end_date
        , FORMAT_DATE('%b-%y', DATE_TRUNC(cal_date, MONTH))                                     AS month_year_short
        , FORMAT_DATE('%B %Y', DATE_TRUNC(cal_date, MONTH))                                     AS month_year_full

          /* Weekly Formats (ISO) - Mon to Sun */
        , "Week " || EXTRACT(ISOWEEK FROM cal_date)                                             AS iso_week_desc
        , DATE_TRUNC(cal_date, ISOWEEK)                                                         AS iso_week_start_date
        , DATE_ADD(DATE_TRUNC(cal_date, ISOWEEK), INTERVAL 6 DAY)                               AS iso_week_end_date

          /* Weekly Formats (Default) - Sun to Sat */
        , "Week " || EXTRACT(WEEK(SUNDAY)  FROM cal_date)                                       AS week_number_desc
        , DATE_TRUNC(cal_date, WEEK(SUNDAY))                                                    AS week_start_date
        , DATE_ADD(DATE_TRUNC(cal_date, WEEK(SUNDAY)), INTERVAL 6 DAY)                          AS week_end_date


        /* Yearly Boolean Date Flags */
        , EXTRACT(YEAR FROM cal_date) = EXTRACT(YEAR FROM CURRENT_DATE())                                                                           AS flag_current_year
        , EXTRACT(YEAR FROM cal_date) = EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR))                                                AS flag_1st_previous_year
        , EXTRACT(YEAR FROM cal_date) = EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR))                                                AS flag_2nd_previous_year
        , cal_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH) AND CURRENT_DATE()                                                           AS flag_current_last_12_months
        , cal_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 24 MONTH) AND DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)                              AS flag_previous_last_12_months


        /* Quarterly Boolean Date Flags */
        , cal_date BETWEEN DATE_TRUNC(CURRENT_DATE(), QUARTER)
                      AND DATE_SUB(DATE_TRUNC(DATE_ADD(CURRENT_DATE(), INTERVAL 1 QUARTER), QUARTER), INTERVAL 1 DAY)                               AS flag_current_quarter

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 QUARTER), QUARTER)
                      AND DATE_SUB(DATE_TRUNC(CURRENT_DATE(), QUARTER), INTERVAL 1 DAY)                                                             AS flag_1st_previous_quarter

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 QUARTER), QUARTER)
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 QUARTER), QUARTER), INTERVAL 1 DAY)                               AS flag_2nd_previous_quarter

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), QUARTER)
                      AND DATE_SUB(DATE_TRUNC(DATE_ADD(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 QUARTER), QUARTER), INTERVAL 1 DAY)
                  AND EXTRACT(QUARTER FROM cal_date) = EXTRACT(QUARTER FROM CURRENT_DATE())                                                         AS flag_current_quarter_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 QUARTER), QUARTER)
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), QUARTER), INTERVAL 1 DAY)
                  AND EXTRACT(QUARTER FROM cal_date) = EXTRACT(QUARTER FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 QUARTER))                           AS flag_1st_previous_quarter_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 2 QUARTER), QUARTER)
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 QUARTER), QUARTER), INTERVAL 1 DAY)
                  AND EXTRACT(QUARTER FROM cal_date) = EXTRACT(QUARTER FROM DATE_SUB(CURRENT_DATE(), INTERVAL 2 QUARTER))                           AS flag_2nd_previous_quarter_last_year

        /* Monthly Boolean Date Flags */
        , cal_date BETWEEN DATE_TRUNC(CURRENT_DATE(), MONTH) 
                      AND DATE_SUB(DATE_TRUNC(DATE_ADD(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH), INTERVAL 1 DAY)                                   AS flag_current_month

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH) 
                      AND DATE_SUB(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 1 DAY)                                                               AS flag_1st_previous_month

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH), MONTH) 
                      AND LAST_DAY(DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH))                                                                      AS flag_2nd_previous_month

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), MONTH)
                        AND DATE_SUB(DATE_TRUNC(DATE_ADD(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 MONTH), MONTH), INTERVAL 1 DAY)
                      AND EXTRACT(MONTH FROM cal_date) = EXTRACT(MONTH FROM CURRENT_DATE())                                                         AS flag_current_month_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 MONTH), MONTH)
                        AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), MONTH), INTERVAL 1 DAY)
                      AND EXTRACT(MONTH FROM cal_date) = EXTRACT(MONTH FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))                             AS flag_1st_previous_month_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 2 MONTH), MONTH)
                        AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), MONTH), INTERVAL 1 DAY)
                      AND EXTRACT(MONTH FROM cal_date) = EXTRACT(MONTH FROM DATE_SUB(CURRENT_DATE(), INTERVAL 2 MONTH))                             AS flag_2nd_previous_month_last_year

        /* Weekly (Starting Sunday) Boolean Date Flags */
        , cal_date BETWEEN DATE_TRUNC(CURRENT_DATE(), WEEK)
                      AND DATE_SUB(DATE_TRUNC(DATE_ADD(CURRENT_DATE(), INTERVAL 1 WEEK), WEEK), INTERVAL 1 DAY)                                     AS flag_current_week

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK), WEEK)
                      AND DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK), INTERVAL 1 DAY)                                                                AS flag_1st_previous_week

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 WEEK), WEEK)
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK), WEEK), INTERVAL 1 DAY)                                     AS flag_2nd_previous_week

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), WEEK)
                      AND DATE_SUB(DATE_TRUNC(DATE_ADD(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 WEEK), WEEK), INTERVAL 1 DAY)
                  AND EXTRACT(WEEK FROM cal_date) = EXTRACT(WEEK FROM CURRENT_DATE())                                                               AS flag_current_week_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 WEEK), WEEK)
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), WEEK), INTERVAL 1 DAY)
                  AND EXTRACT(WEEK FROM cal_date) = EXTRACT(WEEK FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK))                                    AS flag_1st_previous_week_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 2 WEEK), WEEK)
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 WEEK), WEEK), INTERVAL 1 DAY)
                  AND EXTRACT(WEEK FROM cal_date) = EXTRACT(WEEK FROM DATE_SUB(CURRENT_DATE(), INTERVAL 2 WEEK))                                    AS flag_2nd_previous_week_last_year

        /* ISO Weekly Boolean Date Flags */
        , cal_date BETWEEN DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY))
                      AND DATE_SUB(DATE_TRUNC(DATE_ADD(CURRENT_DATE(), INTERVAL 1 WEEK), WEEK(MONDAY)), INTERVAL 1 DAY)                             AS flag_current_iso_week

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK), WEEK(MONDAY))
                      AND DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)), INTERVAL 1 DAY)                                                        AS flag_1st_previous_iso_week

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 2 WEEK), WEEK(MONDAY))
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK), WEEK(MONDAY)), INTERVAL 1 DAY)                             AS flag_2nd_previous_iso_week

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), WEEK(MONDAY))
                      AND DATE_SUB(DATE_TRUNC(DATE_ADD(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 WEEK), WEEK(MONDAY)), INTERVAL 1 DAY)
                  AND EXTRACT(ISOWEEK FROM cal_date) = EXTRACT(ISOWEEK FROM CURRENT_DATE())                                                         AS flag_current_iso_week_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 WEEK), WEEK(MONDAY))
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), WEEK(MONDAY)), INTERVAL 1 DAY)
                  AND EXTRACT(ISOWEEK FROM cal_date) = EXTRACT(ISOWEEK FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 WEEK))                              AS flag_1st_previous_iso_week_last_year

        , cal_date BETWEEN DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 2 WEEK), WEEK(MONDAY))
                      AND DATE_SUB(DATE_TRUNC(DATE_SUB(DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR), INTERVAL 1 WEEK), WEEK(MONDAY)), INTERVAL 1 DAY)
                  AND EXTRACT(ISOWEEK FROM cal_date) = EXTRACT(ISOWEEK FROM DATE_SUB(CURRENT_DATE(), INTERVAL 2 WEEK))                              AS flag_2nd_previous_iso_week_last_year

    FROM cte_date_array
)

SELECT * FROM cte_apply_formatting
ORDER BY cal_date DESC
