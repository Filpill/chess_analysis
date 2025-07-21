{{
 config(
   materialized = 'incremental',
   incremental_strategy = 'insert_overwrite',
   partition_by = {
     'field': 'week_start_date',
     'data_type': 'date',
     'granularity': 'day'
   },
   cluster_by = ['username','time_class']
 )
}}

{% set is_dev = target.name == 'dev' %}

WITH cte_date_aggregate AS (
      SELECT
            cal.iso_week_start_date                                   AS week_start_date,
            cal.iso_week_desc                                         AS week_number,
            t.username,
            t.piece_color,
            t.time_class,
            AVG(t.rating)                                             AS avg_rating,
            AVG(t.accuracy)                                           AS avg_accuracy,
            SUM(CASE WHEN t.win_loss_draw = "win"  THEN 1 ELSE 0 END) AS win_count,
            SUM(CASE WHEN t.win_loss_draw = "loss" THEN 1 ELSE 0 END) AS loss_count,
            SUM(CASE WHEN t.win_loss_draw = "draw" THEN 1 ELSE 0 END) AS draw_count,
            COUNT(*)                                                  AS total_games
      FROM {{ ref("stg__player_games") }} t
      LEFT JOIN {{ ref("calendar") }} cal
        ON t.game_date = cal.cal_date
      WHERE 1=1
        {{ last_n_days_filter("t.game_date") }}
        AND t.rated = TRUE
        AND t.rules = "chess"
      GROUP BY ALL
),

cte_pivot_piece_color AS (
    SELECT
        wagg.week_start_date,
        wagg.week_number,
        wagg.username,
        wagg.time_class,
        AVG(wagg.avg_rating)                                                            AS avg_rating,
        SUM(wagg.total_games)                                                           AS total_games,

        SUM(CASE WHEN wagg.piece_color = "white" THEN wagg.win_count  ELSE 0 END)       AS white_win_count,
        SUM(CASE WHEN wagg.piece_color = "white" THEN wagg.loss_count ELSE 0 END)       AS white_loss_count,
        SUM(CASE WHEN wagg.piece_color = "white" THEN wagg.draw_count ELSE 0 END)       AS white_draw_count,
        AVG(CASE WHEN wagg.piece_color = "white" THEN wagg.avg_accuracy ELSE NULL END)  AS white_accuracy,

        SUM(CASE WHEN wagg.piece_color = "black" THEN wagg.win_count  ELSE 0 END)       AS black_win_count,
        SUM(CASE WHEN wagg.piece_color = "black" THEN wagg.loss_count ELSE 0 END)       AS black_loss_count,
        SUM(CASE WHEN wagg.piece_color = "black" THEN wagg.draw_count ELSE 0 END)       AS black_draw_count,
        AVG(CASE WHEN wagg.piece_color = "black" THEN wagg.avg_accuracy ELSE NULL END)  AS black_accuracy,

    FROM cte_date_aggregate wagg
    GROUP BY ALL
)

SELECT
      week_start_date,
      week_number,
      username,
      time_class,
      avg_rating,
      total_games,
      white_win_count,
      white_loss_count,
      white_draw_count,
      white_accuracy,
      black_win_count,
      black_loss_count,
      black_draw_count,
      black_accuracy
FROM cte_pivot_piece_color
