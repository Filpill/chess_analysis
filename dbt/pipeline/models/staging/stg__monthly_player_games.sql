{{
 config(
   materialized = 'incremental',
   incremental_strategy = 'insert_overwrite',
   partition_by = {
     'field': 'game_month',
     'data_type': 'date',
     'granularity': 'month'
   }
 )
}}

{% set is_dev = target.name == 'dev' %}

WITH cte_base_aggregate AS (
      SELECT  
              t.game_month
            , t.game_month_str
            , t.username
            , t.piece_color
            , t.rules
            , t.time_class
            , t.opening
            , AVG(t.rating)                                             AS avg_rating
            , AVG(t.accuracy)                                           AS avg_accuracy
            , SUM(CASE WHEN t.win_loss_draw = "win"  THEN 1 ELSE 0 END) AS win_count
            , SUM(CASE WHEN t.win_loss_draw = "loss" THEN 1 ELSE 0 END) AS loss_count
            , SUM(CASE WHEN t.win_loss_draw = "draw" THEN 1 ELSE 0 END) AS draw_count
            , COUNT(*)                                                  AS total
      FROM {{  ref("stg__player_games") }} t
      WHERE 1=1
        {{ last_n_days_filter("t.game_month") }}
      GROUP BY ALL
),

cte_struct_agg AS (
      SELECT
              game_month
            , game_month_str
            , username
            , piece_color
            , rules
            , time_class
            , CAST(AVG(avg_rating)AS INT64)                             AS avg_rating
            , ROUND(AVG(avg_accuracy),1)                                AS avg_accuracy
            , SUM(win_count)                                            AS total_win_count
            , SUM(loss_count)                                           AS total_loss_count
            , SUM(draw_count)                                           AS total_draw_count
            , SUM(total)                                                AS total_games
            , ARRAY_AGG(
                        STRUCT(
                               opening,
                               win_count,
                               loss_count,
                               draw_count,
                               total
                        )
                        ORDER BY total DESC
            )                                                           AS openings
      FROM cte_base_aggregate
      GROUP BY ALL
)

SELECT * FROM cte_struct_agg
