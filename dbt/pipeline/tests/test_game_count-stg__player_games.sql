SELECT
    COUNT(*) AS raw_count
FROM {{ source('chess_raw','games') }}
WHERE 1=1
  AND game_date >= DATE('{{ var("test_start_date") }}')

EXCEPT DISTINCT

SELECT
    CAST(COUNT(*)/2 AS INT64) AS agg_count
FROM {{ ref('stg__player_games') }}
WHERE 1=1
  AND game_date >= DATE('{{ var("test_start_date") }}')
