{{ config(materialized='table') }}
{% set is_dev = target.name == 'dev' %}

WITH cte_aggregate AS (
    SELECT 
        games.week_start
      , games.week_number
      , games.time_class
      , map.opening_archetype
      , SUM(CASE WHEN games.piece_color = "white" THEN o.total      ELSE 0 END)   AS total_games /*Black and White Data Unioned -- only counting one piece color*/

      , SUM(CASE WHEN games.piece_color = "white" THEN o.win_count  ELSE 0 END)   AS white_win_count
      , SUM(CASE WHEN games.piece_color = "white" THEN o.loss_count ELSE 0 END)   AS white_loss_count
      , SUM(CASE WHEN games.piece_color = "white" THEN o.draw_count ELSE 0 END)   AS white_draw_count

      , SUM(CASE WHEN games.piece_color = "black" THEN o.win_count  ELSE 0 END)   AS black_win_count
      , SUM(CASE WHEN games.piece_color = "black" THEN o.loss_count ELSE 0 END)   AS black_loss_count
      , SUM(CASE WHEN games.piece_color = "black" THEN o.draw_count ELSE 0 END)   AS black_draw_count


    FROM {{ ref("stg__weekly_games")}} games
    JOIN UNNEST(openings) o
    LEFT JOIN `checkmate-453316.universal.opening_map` map
        ON map.opening = o.opening
    WHERE 1=1
        AND rules = "chess"
        {{ dev_date_filter("games.week_start") }}
    GROUP BY ALL
),

cte_percentage AS (
  SELECT
        week_start
      , week_number
      , time_class
      , opening_archetype
      , total_games
      , white_win_count
      , white_loss_count
      , white_draw_count
      , black_win_count
      , black_loss_count
      , black_draw_count
  FROM cte_aggregate
  ORDER BY 
    week_start DESC
  , total_games DESC

)

SELECT * FROM cte_percentage
