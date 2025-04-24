DECLARE start_date DATE DEFAULT CURRENT_DATE()-60;
DECLARE end_date DATE DEFAULT CURRENT_DATE()-25;

CREATE OR REPLACE TABLE `checkmate-453316.chess_data_aggregated.player_monthly_agg` AS (

WITH cte_white_black_union AS (

    SELECT  
        DATE_TRUNC(game_date, MONTH)                       AS month_period
      , FORMAT_DATE('%b-%y', DATE_TRUNC(game_date, MONTH)) AS formatted_month
      , white.username                                     AS username
      , white.rating                                       AS rating
      , white.result                                       AS result
      , rated
      , time_class
      , time_control
      , rules
      , accuracies.white                                   AS accuracy
      , opening
    FROM `checkmate-453316.chess_data.games` 

      UNION ALL

    SELECT  
        DATE_TRUNC(game_date, MONTH)                       AS month_period
      , FORMAT_DATE('%b-%y', DATE_TRUNC(game_date, MONTH)) AS formatted_month
      , black.username                                     AS username
      , black.rating                                       AS rating
      , black.result                                       AS result
      , rated
      , time_class
      , time_control
      , rules
      , accuracies.black                                   AS accuracy
      , opening
    FROM `checkmate-453316.chess_data.games` 
  
),

cte_base_agg AS (

    SELECT 
        t.month_period
      , t.formatted_month
      , t.username
      , t.time_class
      , t.rules
      , CASE
            WHEN result = "win"                 THEN "win"
            WHEN result = "timeout"             THEN "loss"
            WHEN result = "threecheck"          THEN "loss"
            WHEN result = "resigned"            THEN "loss"
            WHEN result = "kingofthehill"       THEN "loss"
            WHEN result = "checkmated"          THEN "loss"
            WHEN result = "bughousepartnerlose" THEN "loss"
            WHEN result = "abandoned"           THEN "loss"
            WHEN result = "timevsinsufficient"  THEN "draw"
            WHEN result = "stalemate"           THEN "draw"
            WHEN result = "repetition"          THEN "draw"
            WHEN result = "insufficient"        THEN "draw"
            WHEN result = "agreed"              THEN "draw"
            WHEN result = "50move"              THEN "draw"
        END                              AS win_loss_draw   
      , COUNT(*)                         AS game_count
      , ROUND(AVG(t.rating),0)           AS avg_rating
      , AVG(t.accuracy)                  AS avg_accuracy
    FROM cte_white_black_union t

    WHERE 1=1 
      AND month_period BETWEEN start_date AND end_date
      AND rated = True

    GROUP BY ALL
)

SELECT * FROM cte_base_agg
)
