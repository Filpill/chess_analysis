DECLARE start_date DATE;
DECLARE end_date DATE;
DECLARE script_setting STRING;

BEGIN

/* ------ Select Script Setting Here - "dev" or "prod"
            Only affecting date range of data ------------  */
SET script_setting = "prod"; 

IF script_setting = "prod" THEN
      SET start_date = CURRENT_DATE() - 365*5;
      SET end_date = CURRENT_DATE();
ELSEIF script_setting = "dev" THEN
      SET start_date = CURRENT_DATE()-27;
      SET end_date = CURRENT_DATE()-25;
END IF;

CREATE OR REPLACE TABLE `checkmate-453316.chess_staging.player_games` 
PARTITION BY game_date
AS (

WITH cte_white_black_union AS (

    SELECT
        game_id  
      , game_date
      , "white"                                                AS piece_color
      , white.username                                         AS username
      , white.rating                                           AS rating
      , white.result                                           AS result
      , rated
      , time_class
      , time_control
      , rules
      , accuracies.white                                       AS accuracy
      , opening                                                AS opening_line
    FROM `checkmate-453316.chess_raw.games` 

      UNION ALL

    SELECT  
        game_id  
      , game_date
      , "black"                                                AS piece_color
      , black.username                                         AS username
      , black.rating                                           AS rating
      , black.result                                           AS result
      , rated
      , time_class
      , time_control
      , rules
      , accuracies.black                                       AS accuracy
      , opening                                                AS opening_line
    FROM `checkmate-453316.chess_raw.games` 
  
),

cte_base AS (

    SELECT 
        game_id
      , game_date
      , DATE_TRUNC(game_date, MONTH)                           AS game_month
      , FORMAT_DATE('%b-%y', DATE_TRUNC(game_date, MONTH))     AS game_month_formatted
      , t.username
      , t.rating
      , t.piece_color
      , t.time_class
      , t.rules
      , t.result                                               AS raw_result
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
        END                                                   AS win_loss_draw   
      , t.opening_line                                        AS opening_line
      , TRIM(
            REGEXP_REPLACE(REGEXP_REPLACE(t.opening_line , r'\d.*$', ''), r'\.{3,}\s*$', '')
        )                                                     AS opening
      , t.accuracy
    FROM cte_white_black_union t

    WHERE 1=1 
      AND game_date BETWEEN start_date AND end_date
      AND rated = True

)

SELECT * FROM cte_base
);

END;
