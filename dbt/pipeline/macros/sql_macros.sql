{% macro last_n_days_filter(column, days=30) %}
  {% if is_incremental() %}
    AND {{ column }} BETWEEN CURRENT_DATE() - {{ days }} AND CURRENT_DATE()
  {% endif %}
{% endmacro %}
