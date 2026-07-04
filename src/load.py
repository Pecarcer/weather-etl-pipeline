import snowflake.connector
import pandas as pd
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# -----------------------------------------------------------------------------
# CONEXIÓN
# Se suele usar un secrets manager (AWS Secrets Manager,
# Vault...) — aquí usamos .env que es el estándar para desarrollo local.
# -----------------------------------------------------------------------------
def get_connection():
    """Devuelve una conexión activa a Snowflake."""
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
    )


# -----------------------------------------------------------------------------
# CARGA GENÉRICA
# write_pandas() es la función de Snowflake que carga un DataFrame completo
# de forma eficiente — internamente usa un stage temporal y COPY INTO,
# que es exactamente el mismo mecanismo que usarías cargando desde S3.
# -----------------------------------------------------------------------------
def load_dataframe(df: pd.DataFrame, schema: str, table: str) -> None:
    """
    Carga un DataFrame en una tabla de Snowflake.
    Trunca la tabla antes de insertar para evitar duplicados en cada ejecución.
    """
    from snowflake.connector.pandas_tools import write_pandas

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Truncamos la tabla antes de cada carga — así el pipeline es
        # idempotente: ejecutarlo varias veces produce el mismo resultado.
        # En producción podrías usar MERGE para upserts, pero TRUNCATE + INSERT
        # es el patrón más seguro para empezar.
        cursor.execute(f"TRUNCATE TABLE IF EXISTS {schema}.{table}")
        logging.info(f"Tabla {schema}.{table} truncada.")

        # Snowflake espera los nombres de columna en mayúsculas
        df.columns = df.columns.str.upper()

        # write_pandas hace la carga eficiente en bulk —
        # mucho más rápido que insertar fila a fila con INSERT
        success, chunks, rows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=table,
            schema=schema,
            auto_create_table=False  # la tabla ya existe, la creamos en Snowsight
        )

        if success:
            logging.info(f"✅ {rows} filas cargadas en {schema}.{table} ({chunks} chunk/s)")
        else:
            logging.error(f"❌ Fallo al cargar {schema}.{table}")

    finally:
        # El bloque finally garantiza que la conexión se cierra siempre,
        # incluso si hay un error — evita conexiones huérfanas
        cursor.close()
        conn.close()


# -----------------------------------------------------------------------------
# FUNCIONES ESPECÍFICAS POR TABLA
# Cada función mapea el DataFrame correcto a su tabla de destino.
# Cuando en semana 3 añadas dbt, estas funciones seguirán siendo válidas
# para la capa RAW — dbt se encargará de las transformaciones analíticas.
# -----------------------------------------------------------------------------
def load_daily(df: pd.DataFrame) -> None:
    """Carga el dataset diario en RAW.DAILY_WEATHER."""
    logging.info("Cargando dataset diario en Snowflake...")

    # La columna 'date' debe ser string para que Snowflake la interprete bien
    df = df.copy()
    df["date"] = df["date"].astype(str)

    load_dataframe(df, schema="RAW", table="DAILY_WEATHER")


def load_monthly(df: pd.DataFrame) -> None:
    """Carga el resumen mensual en ANALYTICS.MONTHLY_SUMMARY."""
    logging.info("Cargando resumen mensual en Snowflake...")
    load_dataframe(df, schema="ANALYTICS", table="MONTHLY_SUMMARY")


def load_seasonal(df: pd.DataFrame) -> None:
    """Carga el resumen estacional en ANALYTICS.SEASONAL_SUMMARY."""
    logging.info("Cargando resumen estacional en Snowflake...")
    load_dataframe(df, schema="ANALYTICS", table="SEASONAL_SUMMARY")


def load_all(df_daily, df_monthly, df_seasonal) -> None:
    """Ejecuta las tres cargas en secuencia."""
    load_daily(df_daily)
    load_monthly(df_monthly)
    load_seasonal(df_seasonal)