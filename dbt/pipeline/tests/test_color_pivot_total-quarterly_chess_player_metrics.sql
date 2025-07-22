SELECT
  week_start_date,
  username,
  time_class
FROM {{ ref('weekly_chess_player_metrics') }}
WHERE 1=1
  AND week_start_date >= DATE_TRUNC(DATE('{{ var("test_start_date") }}'), QUARTER)
  AND total_games != (white_win_count + white_loss_count + white_draw_count + black_win_count + black_loss_count + black_draw_count)
