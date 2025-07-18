--------------------------------------------------------------------------
-- Need to partition and cluster staging tables as well
SELECT
  username,
  piece_color,
  total_win_count,
  total_loss_count,
  total_draw_count,
  total_games,
FROM `checkmate-453316.prod_staging.stg__weekly_games`
WHERE username = "Razgovor"
    AND week_number = "Week 40"
    AND week_start = "2023-10-01"

--------------------------------------------------------------------------
SELECT
  white.username,
  "white" AS piece_color ,
  COUNT(*) AS total_games
FROM `checkmate-453316.chess_raw.games` 
WHERE game_date BETWEEN "2023-10-01" AND "2023-10-01" + 6
 AND white.username = "Razgovor"
 AND rated = TRUE
GROUP BY ALL


 UNION ALL

SELECT  
  black.username,
  "black" AS piece_color ,
  COUNT(*) AS total_games
FROM `checkmate-453316.chess_raw.games` 
WHERE game_date BETWEEN "2023-10-01" AND "2023-10-01" + 6
 AND black.username = "Razgovor"
 AND rated = TRUE
GROUP BY ALL
-----------------------------------------------------------------------------
