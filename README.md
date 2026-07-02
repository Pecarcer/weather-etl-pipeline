# 🌦️ Weather ETL Pipeline — Huelva

Pipeline ETL en Python que extrae datos meteorológicos históricos de Huelva
desde la API de Open-Meteo, los transforma con pandas y genera análisis
agregados por mes y estación.

---

## Arquitectura

```
Open-Meteo API → extract.py → [data/raw/] → transform.py → [data/processed/] → load.py
                                                                      ↓
                                                            notebooks/eda.ipynb
```

---

## Stack tecnológico

| Librería       | Uso                                  |
| -------------- | ------------------------------------ |
| **pandas**     | Transformación y agregación de datos |
| **requests**   | Extracción desde API REST            |
| **matplotlib** | Visualización en EDA                 |
| **Jupyter**    | Análisis exploratorio                |

---

## Estructura del proyecto

```
weather-etl-pipeline/
├── src/
│   ├── extract.py      # Extracción desde Open-Meteo API
│   ├── transform.py    # Limpieza, enriquecimiento y agregaciones
│   ├── load.py         # Escritura a CSV (preparado para Snowflake)
│   └── pipeline.py     # Orquestación del flujo completo
├── notebooks/
│   └── eda.ipynb       # Análisis exploratorio con visualizaciones
├── data/
│   ├── raw/            # Datos crudos (ignorado por git)
│   └── processed/      # Datos procesados (ignorado por git)
├── requirements.txt
└── README.md
```

---

## Cómo ejecutar

```bash
# 1. Clonar el repositorio
git clone https://github.com/Pecarcer/weather-etl-pipeline.git
cd weather-etl-pipeline

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 3. Ejecutar el pipeline completo
python src/pipeline.py

# 4. Explorar el análisis
jupyter notebook notebooks/eda.ipynb
```

---

## Datos

- **Fuente:** [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- **Ubicación:** Huelva, Andalucía, España (37.26°N, 6.95°W)
- **Periodo:** 2020-01-01 → presente
- **Variables:** temperatura máx/mín/media, precipitación, viento, horas de sol

---

## Próximos pasos

- [ ] Carga a Snowflake con Snowpark
- [ ] Modelos dbt sobre Snowflake
- [ ] Orquestación con Apache Airflow
