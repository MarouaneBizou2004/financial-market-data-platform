{% macro calculate_percentage_change(current_col, previous_col) %}
    ROUND((({{ current_col }} - {{ previous_col }}) * 1.0 / NULLIF({{ previous_col }}, 0)), 6)
{% endmacro %}
