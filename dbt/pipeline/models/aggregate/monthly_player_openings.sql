{{ config(materialized='table') }}
{% set is_dev = target.name == 'dev' %}

WITH cte_aggregate AS (
    SELECT 
        games.game_month
      , games.game_month_str
      , games.username
      , games.time_class
      , map.opening_archetype
      , SUM(o.total)                                                              AS total_games

      , SUM(CASE WHEN games.piece_color = "white" THEN o.total      ELSE 0 END)   AS white_games
      , SUM(CASE WHEN games.piece_color = "white" THEN o.win_count  ELSE 0 END)   AS white_win_count
      , SUM(CASE WHEN games.piece_color = "white" THEN o.loss_count ELSE 0 END)   AS white_loss_count
      , SUM(CASE WHEN games.piece_color = "white" THEN o.draw_count ELSE 0 END)   AS white_draw_count

      , SUM(CASE WHEN games.piece_color = "black" THEN o.total      ELSE 0 END)   AS black_games
      , SUM(CASE WHEN games.piece_color = "black" THEN o.win_count  ELSE 0 END)   AS black_win_count
      , SUM(CASE WHEN games.piece_color = "black" THEN o.loss_count ELSE 0 END)   AS black_loss_count
      , SUM(CASE WHEN games.piece_color = "black" THEN o.draw_count ELSE 0 END)   AS black_draw_count


    FROM {{ ref("stg__monthly_player_games")}} games
    JOIN UNNEST(openings) o
    LEFT JOIN `checkmate-453316.universal.opening_map` map
        ON map.opening = o.opening
    WHERE 1=1
        AND rules = "chess"
        {{ dev_date_filter("games.game_month") }}
    GROUP BY ALL
),

cte_percentage AS (
  SELECT
        game_month
      , game_month_str
      , username
      , time_class
      , opening_archetype
      , total_games
      , white_games
      , white_win_count
      , white_loss_count
      , white_draw_count
      , black_games
      , black_win_count
      , black_loss_count
      , black_draw_count
  FROM cte_aggregate
  ORDER BY 
    game_month DESC
  , username ASC
  , total_games DESC

)

SELECT * FROM cte_percentage
