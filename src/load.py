import pandas as pd
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

OUTPUT_DIR = "data/processed"


def load_daily(df: pd.DataFrame) -> None:
    """Escribe el dataset diario procesado a CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f"{OUTPUT_DIR}/huelva_weather_clean.csv"
    df.to_csv(path, index=False)
    logging.info(f"Dataset diario escrito: {path} ({len(df)} filas)")


def load_monthly(df: pd.DataFrame) -> None:
    """Escribe el resumen mensual a CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f"{OUTPUT_DIR}/huelva_monthly.csv"
    df.to_csv(path, index=False)
    logging.info(f"Resumen mensual escrito: {path} ({len(df)} filas)")


def load_seasonal(df: pd.DataFrame) -> None:
    """Escribe el resumen estacional a CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f"{OUTPUT_DIR}/huelva_seasonal.csv"
    df.to_csv(path, index=False)
    logging.info(f"Resumen estacional escrito: {path} ({len(df)} filas)")


def load_all(df_daily, df_monthly, df_seasonal) -> None:
    """Ejecuta todas las cargas en secuencia."""
    load_daily(df_daily)
    load_monthly(df_monthly)
    load_seasonal(df_seasonal)