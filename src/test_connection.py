import snowflake.connector
from dotenv import load_dotenv
import os

# load_dotenv() lee el fichero .env y carga las variables como variables
# de entorno del proceso — así las credenciales nunca están hardcodeadas
load_dotenv()

def test_connection():
    print("Intentando conectar a Snowflake...")

    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE")
    )

    cursor = conn.cursor()

    # Consulta simple para verificar que llegamos bien
    cursor.execute("SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_WAREHOUSE()")
    row = cursor.fetchone()

    print(f"✅ Conexión exitosa")
    print(f"   Usuario:    {row[0]}")
    print(f"   Base datos: {row[1]}")
    print(f"   Warehouse:  {row[2]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_connection()