-- Mart: resumen por estación.

with int as (

    select * from {{ ref('int_daily_weather_enriched') }}

),

seasonal as (

    select
        season,
        round(avg(temp_mean), 2)                    as temp_media,
        round(max(temp_max), 2)                     as temp_max,
        round(min(temp_min), 2)                     as temp_min,
        round(sum(precipitation_clean), 2)          as precipitacion_total,
        count_if(precipitation_clean > 0)           as dias_con_lluvia

    from int
    group by season

)

select * from seasonal