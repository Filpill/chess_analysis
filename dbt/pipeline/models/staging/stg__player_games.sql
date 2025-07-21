{{
 config(
   materialized = 'incremental',
   incremental_strategy = 'insert_overwrite',
   partition_by = {
     'field': 'game_date',
     'data_type': 'date',
     'granularity': 'day'
   }
 )
}}

{% set is_dev = target.name == 'dev' %}

WITH cte_white_black_union AS (

    SELECT
        game_id,
        game_date,
        "white"                                                AS piece_color,
        white.username                                         AS username,
        white.rating                                           AS rating,
        white.result                                           AS result,
        rated,
        time_class,
        time_control,
        rules,
        accuracies.white                                       AS accuracy,
        opening                                                AS opening_line,
    FROM {{ source("chess_raw", "games") }} 

      UNION ALL

    SELECT
        game_id,
        game_date,
        "black"                                                AS piece_color,
        black.username                                         AS username,
        black.rating                                           AS rating,
        black.result                                           AS result,
        rated,
        time_class,
        time_control,
        rules,
        accuracies.black                                       AS accuracy,
        opening                                                AS opening_line,
    FROM {{ source("chess_raw", "games") }}
)

SELECT
    t.game_id,
    t.game_date,
    t.username,
    t.rating,
    t.piece_color,
    t.time_class,
    t.rules,
    t.result                                               AS raw_result,
    t.rated,
    CASE
        WHEN t.result = "win"                 THEN "win"
        WHEN t.result = "timeout"             THEN "loss"
        WHEN t.result = "threecheck"          THEN "loss"
        WHEN t.result = "resigned"            THEN "loss"
        WHEN t.result = "kingofthehill"       THEN "loss"
        WHEN t.result = "checkmated"          THEN "loss"
        WHEN t.result = "bughousepartnerlose" THEN "loss"
        WHEN t.result = "abandoned"           THEN "loss"
        WHEN t.result = "timevsinsufficient"  THEN "draw"
        WHEN t.result = "stalemate"           THEN "draw"
        WHEN t.result = "repetition"          THEN "draw"
        WHEN t.result = "insufficient"        THEN "draw"
        WHEN t.result = "agreed"              THEN "draw"
        WHEN t.result = "50move"              THEN "draw"
    END                                                   AS win_loss_draw,
    t.opening_line                                        AS opening_line,
    TRIM(
        REGEXP_REPLACE(REGEXP_REPLACE(t.opening_line , r'\d.*$', ''), r'\.{3,}\s*$', '')
    )                                                     AS opening,
    t.accuracy,
FROM cte_white_black_union t

WHERE 1=1 
  {{ last_n_days_filter("t.game_date") }}
