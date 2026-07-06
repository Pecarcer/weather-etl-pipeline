from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os

# Ruta al proyecto en Windows accesible desde WSL2
PROJECT_PATH = "/mnt/d/Programacion/ESTUDIAR EN SERIO/weather-etl-pipeline"
DBT_PATH = "/mnt/d/Programacion/ESTUDIAR\\ EN\\ SERIO/weather-etl-pipeline/weather_dbt"

# Añadimos src/ al path para poder importar los módulos
sys.path.insert(0, f"{PROJECT_PATH}/src")

default_args = {
    "owner": "jose_carmona",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="weather_etl_pipeline",
    description="Pipeline ETL completo: Open-Meteo → Snowflake → dbt",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",    # se ejecuta cada día automáticamente
    catchup=False,                 # no ejecuta fechas pasadas al activar
    tags=["weather", "snowflake", "dbt"],
) as dag:

    # --- TAREA 1: EXTRACT ---
    # Llama a la API de Open-Meteo y guarda el CSV raw
    def run_extract():
        from extract import fetch_weather_data, parse_to_dataframe, save_raw
        raw_data = fetch_weather_data()
        df = parse_to_dataframe(raw_data)
        save_raw(df)

    task_extract = PythonOperator(
        task_id="extract_from_api",
        python_callable=run_extract,
    )

    # --- TAREA 2: TRANSFORM + LOAD A SNOWFLAKE ---
    # Limpia, transforma y carga en Snowflake
    def run_transform_load():
        from transform import load_raw, clean, transform, create_aggregations
        from load import load_all

        RAW_PATH = f"{PROJECT_PATH}/data/raw/huelva_weather_raw.csv"
        df = load_raw(RAW_PATH)
        df = clean(df)
        df = transform(df)
        monthly, seasonal = create_aggregations(df)
        load_all(df, monthly, seasonal)

    task_load = PythonOperator(
        task_id="transform_and_load_snowflake",
        python_callable=run_transform_load,
    )

    # --- TAREA 3: DBT RUN ---
    # Ejecuta los modelos dbt sobre los datos cargados en Snowflake
    task_dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PATH} && dbt run --profiles-dir ~/.dbt",
    )

    # --- TAREA 4: DBT TEST ---
    # Valida la calidad de los datos tras la transformación
    task_dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PATH} && dbt test --profiles-dir ~/.dbt",
    )

    # --- DEPENDENCIAS ---
    # Define el orden de ejecución: cada >> significa "después de"
    task_extract >> task_load >> task_dbt_run >> task_dbt_test
