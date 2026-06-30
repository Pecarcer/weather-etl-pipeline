import logging
import sys
import time


from extract import fetch_weather_data, parse_to_dataframe, save_raw
from transform import load_raw, clean, transform, create_aggregations, save

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

RAW_PATH = "data/raw/huelva_weather_raw.csv"


def run_pipeline():
    """Ejecuta el pipeline completo: extract → transform → load."""

    inicio = time.time()
    logging.info("=" * 60)
    logging.info("INICIO DEL PIPELINE")
    logging.info("=" * 60)

    # --- FASE 1: EXTRACT ---
    try:
        logging.info("[1/2] Iniciando extracción...")
        raw_data = fetch_weather_data()
        df_raw = parse_to_dataframe(raw_data)
        save_raw(df_raw)
        logging.info("[1/2] Extracción completada.")
    except Exception as e:
        logging.error(f"Pipeline ABORTADO en fase de extracción: {e}")
        sys.exit(1)  # Código de salida 1 = error, útil si algún día lo lanza un orquestador

    # --- FASE 2: TRANSFORM ---
    try:
        logging.info("[2/2] Iniciando transformación...")
        df = load_raw(RAW_PATH)
        df = clean(df)
        df = transform(df)
        monthly, seasonal = create_aggregations(df)
        save(df, monthly, seasonal)
        logging.info("[2/2] Transformación completada.")
    except Exception as e:
        logging.error(f"Pipeline ABORTADO en fase de transformación: {e}")
        sys.exit(1)

    duracion = round(time.time() - inicio, 2)
    logging.info("=" * 60)
    logging.info(f"PIPELINE COMPLETADO EN {duracion}s")
    logging.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()