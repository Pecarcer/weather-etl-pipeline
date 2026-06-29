import pandas as pd
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

INPUT_PATH = "data/raw/huelva_weather_raw.csv"
OUTPUT_PATH = "data/processed/huelva_weather_clean.csv"


# -----------------------------------------------------------------------------
# PASO 1: CARGA
# Leemos el CSV raw que generó extract.py. 
# -----------------------------------------------------------------------------
def load_raw(path):
    """Carga el CSV raw y devuelve un DataFrame con tipos correctos."""
    logging.info(f"Cargando datos desde {path}...")
    df = pd.read_csv(path, parse_dates=["date"])
    logging.info(f"Datos cargados: {len(df)} filas.")
    return df


# -----------------------------------------------------------------------------
# PASO 2: LIMPIEZA
# Limpieza de nulos, duplicados y nombres de columna consistentes.
# -----------------------------------------------------------------------------
def clean(df):
    """Limpia el DataFrame: nulos, duplicados y nombres de columna."""

    filas_inicial = len(df)

    # Eliminamos filas duplicadas exactas — en datos de API no debería
    # haber, pero es buena práctica defensiva incluirlo siempre
    df = df.drop_duplicates()

    # Rellenamos nulos en columnas numéricas con la mediana de esa columna.
    # Usamos mediana en lugar de media porque es más robusta ante valores
    # extremos (un día de tormenta no distorsiona el relleno)
    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        nulos = df[col].isnull().sum()
        if nulos > 0:
            mediana = df[col].median()
            df[col] = df[col].fillna(mediana)
            logging.info(f"Columna '{col}': {nulos} nulos rellenados con mediana ({mediana:.2f})")

    # Estandarizamos nombres de columna: minúsculas y sin espacios.
    # Esto es estándar en Snowflake y dbt — evita problemas de mayúsculas
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    filas_final = len(df)
    logging.info(f"Limpieza completada: {filas_inicial - filas_final} filas eliminadas.")
    return df


# -----------------------------------------------------------------------------
# PASO 3: TRANSFORMACIÓN Y ENRIQUECIMIENTO
# -----------------------------------------------------------------------------
def transform(df):
    """Enriquece el DataFrame con columnas calculadas."""

    # -- Columnas de tiempo --
    # Extraer año, mes y día de la fecha es fundamental para poder hacer
    # groupby por mes o año después. En SQL sería EXTRACT(MONTH FROM date).
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day

    # Nombre del mes en texto — útil para gráficos y reportes
    df["month_name"] = df["date"].dt.strftime("%B")

    # Día de la semana (0=lunes, 6=domingo)
    df["weekday"] = df["date"].dt.dayofweek

    # -- Estación del año --
    # Función auxiliar que asigna estación según el mes.
    # map() aplica la función a cada valor de la columna — equivale a un
    # CASE WHEN en SQL.
    def get_season(month):
        if month in [12, 1, 2]:
            return "Invierno"
        elif month in [3, 4, 5]:
            return "Primavera"
        elif month in [6, 7, 8]:
            return "Verano"
        else:
            return "Otoño"

    df["season"] = df["month"].map(get_season)

    # -- Rango térmico diario --
    # Diferencia entre máxima y mínima del día. Un rango alto indica
    # día continental, bajo indica influencia atlántica/costera.
    df["temp_range"] = (df["temperature_2m_max"] - df["temperature_2m_min"]).round(2)

    # -- Clasificación de precipitación --
    # Convertimos un número continuo en categorías discretas.
    # En Snowflake/dbt esto sería un CASE WHEN sobre la columna.
    def classify_rain(mm):
        if mm == 0:
            return "Sin lluvia"
        elif mm < 1:
            return "Inapreciable"
        elif mm < 10:
            return "Lluvia débil"
        elif mm < 30:
            return "Lluvia moderada"
        else:
            return "Lluvia intensa"

    df["rain_category"] = df["precipitation_sum"].map(classify_rain)

    # -- Sunshine en horas --
    # La API devuelve sunshine_duration en segundos, lo convertimos a horas
    # redondeado a 2 decimales para que sea legible
    if "sunshine_duration" in df.columns:
        df["sunshine_hours"] = (df["sunshine_duration"] / 3600).round(2)
        df = df.drop(columns=["sunshine_duration"])

    logging.info(f"Transformación completada. Columnas finales: {list(df.columns)}")
    return df


# -----------------------------------------------------------------------------
# PASO 4: AGREGACIONES — groupby en acción
# Creamos dos tablas de resumen que guardaremos como CSVs separados:
# una por mes y otra por estación. 
# -----------------------------------------------------------------------------
def create_aggregations(df):
    """Genera tablas de resumen agregadas por mes y por estación."""

    # -- Resumen mensual --
    # groupby() agrupa las filas por año y mes.
    # agg() define qué función aplicar a cada columna.
    # Equivale exactamente a:
    # SELECT year, month,
    #   AVG(temperature_2m_mean), MAX(temperature_2m_max), ...
    # FROM df GROUP BY year, month
    monthly = (
        df.groupby(["year", "month", "month_name"])
        .agg(
            temp_media=("temperature_2m_mean", "mean"),
            temp_max=("temperature_2m_max", "max"),
            temp_min=("temperature_2m_min", "min"),
            precipitacion_total=("precipitation_sum", "sum"),
            dias_con_lluvia=("precipitation_sum", lambda x: (x > 0).sum()),
            horas_sol_media=("sunshine_hours", "mean"),
        )
        .round(2)
        .reset_index()  # convierte el índice compuesto en columnas normales
        .sort_values(["year", "month"])
    )

    # -- Resumen por estación --
    seasonal = (
        df.groupby("season")
        .agg(
            temp_media=("temperature_2m_mean", "mean"),
            temp_max=("temperature_2m_max", "max"),
            temp_min=("temperature_2m_min", "min"),
            precipitacion_total=("precipitation_sum", "sum"),
            dias_con_lluvia=("precipitation_sum", lambda x: (x > 0).sum()),
        )
        .round(2)
        .reset_index()
    )

    logging.info(f"Agregación mensual: {len(monthly)} filas")
    logging.info(f"Agregación estacional: {len(seasonal)} filas")

    return monthly, seasonal


# -----------------------------------------------------------------------------
# PASO 5: GUARDADO
# Guardamos tres CSVs distintos en data/processed/:
# - el dataset diario completo y limpio
# - el resumen mensual
# - el resumen estacional
# -----------------------------------------------------------------------------
def save(df, monthly, seasonal):
    """Guarda los DataFrames procesados en data/processed/."""
    os.makedirs("data/processed", exist_ok=True)

    df.to_csv(OUTPUT_PATH, index=False)
    logging.info(f"Dataset diario guardado: {OUTPUT_PATH}")

    monthly.to_csv("data/processed/huelva_monthly.csv", index=False)
    logging.info("Resumen mensual guardado: data/processed/huelva_monthly.csv")

    seasonal.to_csv("data/processed/huelva_seasonal.csv", index=False)
    logging.info("Resumen estacional guardado: data/processed/huelva_seasonal.csv")


# -----------------------------------------------------------------------------
# PUNTO DE ENTRADA
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    df = load_raw(INPUT_PATH)
    df = clean(df)
    df = transform(df)
    monthly, seasonal = create_aggregations(df)
    save(df, monthly, seasonal)

    print("\n=== MUESTRA DEL DATASET DIARIO ===")
    print(df.head())

    print("\n=== RESUMEN MENSUAL (últimos 6 meses) ===")
    print(monthly.tail(6).to_string(index=False))

    print("\n=== RESUMEN POR ESTACIÓN ===")
    print(seasonal.to_string(index=False))