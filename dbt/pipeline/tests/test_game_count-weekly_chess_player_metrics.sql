SELECT
    COUNT(*) AS raw_count
FROM {{ source('chess_raw','games') }}
WHERE 1=1
  AND game_date >= DATE_TRUNC(DATE('{{ var("test_start_date") }}'), ISOWEEK)
  AND rated = TRUE
  AND rules = "chess"

EXCEPT DISTINCT

SELECT
    CAST(SUM(total_games)/2 AS INT64) AS agg_count
FROM {{ ref('weekly_chess_player_metrics') }}
WHERE 1=1
  AND week_start_date >= DATE_TRUNC(DATE('{{ var("test_start_date") }}'), ISOWEEK)
