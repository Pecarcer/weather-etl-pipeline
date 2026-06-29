import requests
import pandas as pd
import logging
import os
from datetime import date, timedelta


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

LATITUDE = 37.26          # Latitud de Huelva
LONGITUDE = -6.95         # Longitud de Huelva
START_DATE = "2020-01-01"
END_DATE = str(date.today() - timedelta(days=1)) # Fecha de ayer

# Variables meteorológicas que queremos. Las unimos con coma en un solo string
# porque la API de Open-Meteo no acepta el parámetro repetido varias veces.
DAILY_VARIABLES = ",".join([
    "temperature_2m_max",     # Temperatura máxima del día (°C)
    "temperature_2m_min",     # Temperatura mínima del día (°C)
    "temperature_2m_mean",    # Temperatura media del día (°C)
    "precipitation_sum",      # Precipitación total del día (mm)
    "wind_speed_10m_max",     # Velocidad máxima del viento a 10m (km/h)
    "sunshine_duration"       # Horas de sol (segundos — lo convertiremos luego)
])

OUTPUT_PATH = "data/raw/huelva_weather_raw.csv"


def fetch_weather_data():
    """Llama al endpoint histórico de Open-Meteo y devuelve el JSON de respuesta."""

    base_url = "https://archive-api.open-meteo.com/v1/archive"

    query = (
        f"latitude={LATITUDE}"
        f"&longitude={LONGITUDE}"
        f"&start_date={START_DATE}"
        f"&end_date={END_DATE}"
        f"&daily={DAILY_VARIABLES}"       # comas literales, sin codificar
        f"&timezone=Europe/Madrid"
    )

    url = f"{base_url}?{query}"

    logging.info(f"Llamando a la API de Open-Meteo para Huelva ({START_DATE} → {END_DATE})...")
    logging.info(f"URL: {url}")  

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        logging.info("Respuesta recibida correctamente.")
        return response.json()

    except requests.exceptions.Timeout:
        logging.error("La API tardó demasiado en responder (timeout 30s).")
        raise
    except requests.exceptions.HTTPError as e:
        logging.error(f"Error HTTP de la API: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de red inesperado: {e}")
        raise


# -----------------------------------------------------------------------------
# PARSEO — convierte el JSON crudo en un DataFrame limpio
# La API devuelve un dict con clave "daily" que contiene listas paralelas:
# {"time": ["2020-01-01", ...], "temperature_2m_max": [16.2, ...], ...}
# pd.DataFrame() las convierte directamente en columnas.
# -----------------------------------------------------------------------------
def parse_to_dataframe(data):
    """Transforma el JSON de la API en un DataFrame de pandas estructurado."""

    # Extraemos solo la parte "daily" del JSON — el resto son metadatos
    daily = data["daily"]

    # pd.DataFrame recibe un dict de listas y crea una columna por cada clave
    df = pd.DataFrame(daily)

    # Renombramos "time" a "date" para que sea más descriptivo
    df.rename(columns={"time": "date"}, inplace=True)

    # Convertimos la columna de fecha de string a tipo datetime de pandas.
    # Esto es importante: permite filtrar por fechas, calcular diferencias, etc.
    df["date"] = pd.to_datetime(df["date"])

    # sunshine_duration viene en segundos — lo convertimos a horas para que
    # tenga sentido al leerlo (este tipo de conversión es trabajo de Transform)
    df["sunshine_hours"] = (df["sunshine_duration"] / 3600).round(2)
    df.drop(columns=["sunshine_duration"], inplace=True)

    logging.info(f"DataFrame creado: {len(df)} filas, {len(df.columns)} columnas.")
    return df


# -----------------------------------------------------------------------------
# CARGA — persiste el DataFrame como CSV en el sistema de ficheros
# En la semana 2 esta función cambiará para escribir directamente a Snowflake.
# Por ahora, CSV en disco es nuestra "capa de almacenamiento".
# -----------------------------------------------------------------------------
def save_raw(df):
    """Guarda el DataFrame como CSV en la carpeta data/raw/."""

    # exist_ok=True evita error si la carpeta ya existe
    os.makedirs("data/raw", exist_ok=True)

    # index=False evita que pandas escriba el índice numérico como columna extra
    df.to_csv(OUTPUT_PATH, index=False)
    logging.info(f"CSV guardado en: {OUTPUT_PATH} ({len(df)} filas)")



if __name__ == "__main__":
    raw_data = fetch_weather_data()
    df = parse_to_dataframe(raw_data)
    save_raw(df)

    # Mostramos las primeras filas para confirmar visualmente que todo fue bien
    print("\n=== PRIMERAS FILAS DEL DATASET ===")
    print(df.head(10))
    print(f"\nTotal filas: {len(df)} | Columnas: {list(df.columns)}")