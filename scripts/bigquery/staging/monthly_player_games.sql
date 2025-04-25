DECLARE start_date DATE;
DECLARE end_date DATE;
DECLARE script_setting STRING;

BEGIN

/*===========================================================*/
/* ------ Select Script Setting Here - "dev" or "prod"
--------------Only affecting date range of data ------------  */
SET script_setting = "prod"; 

IF script_setting = "prod" THEN
      SET start_date = CURRENT_DATE() - 365*5;
      SET end_date = CURRENT_DATE();
ELSEIF script_setting = "dev" THEN
      SET start_date = CURRENT_DATE()-27;
      SET end_date = CURRENT_DATE()-25;
END IF;
/*===========================================================*/

CREATE OR REPLACE TABLE `checkmate-453316.chess_staging.monthly_player_games` 
PARTITION BY game_month
AS (

WITH 

cte_base_aggregate AS (
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
      FROM `checkmate-453316.chess_staging.player_games` t
      WHERE 
        game_date BETWEEN start_date AND end_date
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

);

END;

