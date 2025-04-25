CREATE OR REPLACE TABLE `checkmate-453316.chess_aggregate.monthly_chess_openings` AS (
WITH cte_aggregate AS (
    SELECT 
        game_month
      , game_month_str
      , time_class
      , opening
      , SUM(o.total)                                                                                 AS total_games

      , SUM(CASE WHEN piece_color = "white" THEN o.total      ELSE 0 END)                            AS white_games
      , SUM(CASE WHEN piece_color = "white" THEN o.win_count  ELSE 0 END)                            AS white_win_count
      , SUM(CASE WHEN piece_color = "white" THEN o.loss_count ELSE 0 END)                            AS white_loss_count
      , SUM(CASE WHEN piece_color = "white" THEN o.draw_count ELSE 0 END)                            AS white_draw_count

      , SUM(CASE WHEN piece_color = "black" THEN o.total      ELSE 0 END)                            AS black_games
      , SUM(CASE WHEN piece_color = "black" THEN o.win_count  ELSE 0 END)                            AS black_win_count
      , SUM(CASE WHEN piece_color = "black" THEN o.loss_count ELSE 0 END)                            AS black_loss_count
      , SUM(CASE WHEN piece_color = "black" THEN o.draw_count ELSE 0 END)                            AS black_draw_count


    FROM `checkmate-453316.chess_aggregate.monthly_player_games`
    JOIN UNNEST(openings) o
    WHERE 1=1
        AND rules = "chess"
    GROUP BY ALL
),

cte_percentage AS (
  SELECT
        game_month
      , game_month_str
      , time_class
      , opening
      , total_games
      , white_games
      , white_win_count
      , white_loss_count
      , white_draw_count
      , ROUND(SAFE_DIVIDE(white_win_count, white_games)*100, 1) AS white_win_percentage
      , black_games
      , black_win_count
      , black_loss_count
      , black_draw_count
      , ROUND(SAFE_DIVIDE(black_win_count, black_games)*100, 1) AS black_win_percentage
  FROM cte_aggregate

)

SELECT * FROM cte_percentage
ORDER BY 
    game_month DESC
  , total_games DESC

)
