-- Capa intermediate: enriquece con columnas derivadas.
-- Equivale a la función transform() de transform.py.

with stg as (

    select * from {{ ref('stg_daily_weather') }}

),

enriched as (

    select
        date,
        temp_max,
        temp_min,
        temp_mean,
        precipitation_sum,
        precipitation_clean,
        wind_speed_max,
        sunshine_hours,

        -- Columnas de tiempo
        year(date)                                  as year,
        month(date)                                 as month,
        day(date)                                   as day,
        dayofweek(date)                             as weekday,
        monthname(date)                             as month_name,

        -- Estación del año
        case
            when month(date) in (12, 1, 2)  then 'Invierno'
            when month(date) in (3, 4, 5)   then 'Primavera'
            when month(date) in (6, 7, 8)   then 'Verano'
            else                                 'Otoño'
        end                                         as season,

        -- Rango térmico diario
        round(temp_max - temp_min, 2)               as temp_range,

        -- Clasificación de precipitación
        case
            when precipitation_clean = 0            then 'Sin lluvia'
            when precipitation_clean < 1            then 'Inapreciable'
            when precipitation_clean < 10           then 'Lluvia débil'
            when precipitation_clean < 30           then 'Lluvia moderada'
            else                                         'Lluvia intensa'
        end                                         as rain_category

    from stg

)

select * from enriched