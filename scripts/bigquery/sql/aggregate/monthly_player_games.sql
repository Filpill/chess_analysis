DECLARE start_date DATE;
DECLARE end_date DATE;
DECLARE script_setting STRING;

BEGIN

/* ------ Select Script Setting Here - "dev" or "prod"
            Only affecting date range of data ------------  */
SET script_setting = "dev"; 

IF script_setting = "prod" THEN
      SET start_date = CURRENT_DATE() - 365*5;
      SET end_date = CURRENT_DATE();
ELSEIF script_setting = "dev" THEN
      SET start_date = CURRENT_DATE()-27;
      SET end_date = CURRENT_DATE()-25;
END IF;

CREATE OR REPLACE TABLE `checkmate-453316.chess_aggregate.monthly_player_games` 
PARTITION BY game_month
AS (

WITH cte_base AS (
      SELECT  
              game_month
            , game_month_formatted
            , username
            , piece_color
            , rules
            , time_class
            , opening
            , win_loss_draw
            , rating
            , accuracy
            , COUNT(*)                  AS game_count
      FROM `checkmate-453316.chess_staging.player_games` 
      WHERE game_date BETWEEN start_date AND end_date
      GROUP BY ALL
)

, cte_agg AS (
      SELECT 
            --   base.* EXCEPT(game_count,opening,rating,accuracy)
              base.game_month
            , base.game_month_formatted
            , username
            , piece_color
            , rules
            , time_class
            , game_count
            , AVG(base.rating)                                             AS avg_rating
            , AVG(base.accuracy)                                           AS avg_accuracy
            , SUM(CASE WHEN base.win_loss_draw = "win" THEN 1 ELSE 0 END)  AS win_count
            , SUM(CASE WHEN base.win_loss_draw = "loss" THEN 1 ELSE 0 END) AS loss_count
            , SUM(CASE WHEN base.win_loss_draw = "draw" THEN 1 ELSE 0 END) AS draw_count
            , ARRAY_AGG(
                        STRUCT(opening,game_count)
                        ORDER BY base.game_count
            )                                                              AS opening_counts
      FROM cte_base AS base
      GROUP BY ALL
)

SELECT * FROM cte_agg

);

END;
