import pandas as pd

df = pd.read_csv("data/raw/huelva_weather_raw.csv")

print("=== PRIMERAS FILAS ===")
print(df.head())

print("\n=== ESTRUCTURA ===")
print(df.info())

print("\n=== ESTADÍSTICAS ===")
print(df.describe())

print("\n=== VALORES NULOS ===")
print(df.isnull().sum())