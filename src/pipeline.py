import logging
import sys
import time

from extract import fetch_weather_data, parse_to_dataframe, save_raw
from transform import load_raw, clean, transform, create_aggregations
from load import load_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

RAW_PATH = "data/raw/huelva_weather_raw.csv"


def run_pipeline():
    inicio = time.time()
    logging.info("=" * 60)
    logging.info("INICIO DEL PIPELINE")
    logging.info("=" * 60)

    # --- FASE 1: EXTRACT ---
    try:
        logging.info("[1/3] Iniciando extracción...")
        raw_data = fetch_weather_data()
        df_raw = parse_to_dataframe(raw_data)
        save_raw(df_raw)
        logging.info("[1/3] Extracción completada.")
    except Exception as e:
        logging.error(f"Pipeline ABORTADO en extracción: {e}")
        sys.exit(1)

    # --- FASE 2: TRANSFORM ---
    try:
        logging.info("[2/3] Iniciando transformación...")
        df = load_raw(RAW_PATH)
        df = clean(df)
        df = transform(df)
        monthly, seasonal = create_aggregations(df)
        logging.info("[2/3] Transformación completada.")
    except Exception as e:
        logging.error(f"Pipeline ABORTADO en transformación: {e}")
        sys.exit(1)

    # --- FASE 3: LOAD ---
    try:
        logging.info("[3/3] Iniciando carga...")
        load_all(df, monthly, seasonal)
        logging.info("[3/3] Carga completada.")
    except Exception as e:
        logging.error(f"Pipeline ABORTADO en carga: {e}")
        sys.exit(1)

    duracion = round(time.time() - inicio, 2)
    logging.info("=" * 60)
    logging.info(f"PIPELINE COMPLETADO EN {duracion}s")
    logging.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()