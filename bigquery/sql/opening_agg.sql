CREATE OR REPLACE TABLE `checkmate-453316.chess_data_aggregated.opening_agg` AS (
  SELECT 
      game_date
    , rated
    , time_class
    , rules
    , TRIM(REGEXP_REPLACE(REGEXP_REPLACE(opening, r'\d.*$', ''), r'\.{3,}\s*$', '')) AS opening
    , COUNT(*) AS row_count
  FROM `checkmate-453316.chess_data.games`
  GROUP BY ALL
)
