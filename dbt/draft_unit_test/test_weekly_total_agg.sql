------------------------------------------------------------
SELECT
  SUM(total_games) AS total_games
FROM `checkmate-453316.prod_aggregate.weekly_openings`
WHERE week_start = "2023-10-01"
------------------------------------------------------------
SELECT
  COUNT(*) AS total_games
FROM `checkmate-453316.chess_raw.games` 
WHERE game_date BETWEEN "2023-10-01" AND "2023-10-07"
   AND rules = "chess"
   AND rated = TRUE
GROUP BY ALL
------------------------------------------------------------
