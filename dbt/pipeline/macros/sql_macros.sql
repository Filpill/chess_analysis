{% macro dev_date_filter(column='date_column') %}
  {% if target.name == 'dev' %}
    AND {{ column }} BETWEEN CURRENT_DATE()-60 AND CURRENT_DATE()
  {% endif %}
{% endmacro %}
