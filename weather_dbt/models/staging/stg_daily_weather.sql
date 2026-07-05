-- Capa staging: normaliza los datos raw sin aplicar lógica de negocio.
-- Es equivalente a la función clean() de transform.py.
-- Lee directamente de la tabla que carga el pipeline Python.

with source as (

    select * from {{ source('raw', 'daily_weather') }}

),

renamed as (

    select
        date,
        temperature_2m_max                          as temp_max,
        temperature_2m_min                          as temp_min,
        temperature_2m_mean                         as temp_mean,
        precipitation_sum,
        wind_speed_10m_max                          as wind_speed_max,
        sunshine_hours,

        -- Garantizamos que no hay nulos en columnas clave
        coalesce(temperature_2m_mean, 0)            as temp_mean_clean,
        coalesce(precipitation_sum, 0)              as precipitation_clean

    from source
    where date is not null  -- filtramos filas sin fecha

)

select * from renamed