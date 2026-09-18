{#
  Use the custom schema name as-is (staging / intermediate / marts)
  instead of dbt's default "<target_schema>_<custom_schema>" concatenation,
  so tables land in clean schemas inside the DuckDB warehouse.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
