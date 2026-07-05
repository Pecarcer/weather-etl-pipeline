-- Mart: resumen mensual agregado.
-- Equivale a la parte mensual de create_aggregations() en transform.py.
-- Esta tabla es el resultado final que consumiría un analista o un dashboard.

with int as (

    select * from {{ ref('int_daily_weather_enriched') }}

),

monthly as (

    select
        year,
        month,
        month_name,
        round(avg(temp_mean), 2)                    as temp_media,
        round(max(temp_max), 2)                     as temp_max,
        round(min(temp_min), 2)                     as temp_min,
        round(sum(precipitation_clean), 2)          as precipitacion_total,
        count_if(precipitation_clean > 0)           as dias_con_lluvia,
        round(avg(sunshine_hours), 2)               as horas_sol_media

    from int
    group by year, month, month_name
    order by year, month

)

select * from monthly