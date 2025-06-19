# import sqlite3
# import pandas as pd

# # Conecta a tu base de datos SQLite
# conn = sqlite3.connect('datos.db')

# # Lista de las tablas que deseas exportar
# tablas = ['citas', 'doctores', 'motivoconsulta']  # agrega más si tienes

# # Recorre cada tabla y exporta a CSV
# for tabla in tablas:
#     df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
#     df.to_csv(f"{tabla}.csv", index=False)
#     print(f"✅ Tabla '{tabla}' exportada como {tabla}.csv")

# conn.close()




################################################3


# import sqlite3
# import csv

# # Ruta de tu base de datos SQLite
# conexion = sqlite3.connect('datos.db')  # Reemplaza con el nombre real del archivo .db
# cursor = conexion.cursor()

# # Ejecutar consulta con las columnas deseadas
# cursor.execute("SELECT id, nombre, dni, telefono FROM historia_clinica")
# registros = cursor.fetchall()

# # Crear archivo CSV y escribir los datos
# with open('historia_clinica.csv', mode='w', newline='', encoding='utf-8') as archivo_csv:
#     escritor = csv.writer(archivo_csv)
    
#     # Escribir encabezados
#     escritor.writerow(['id', 'nombre', 'dni', 'telefono'])
    
#     # Escribir datos
#     escritor.writerows(registros)

# # Cerrar conexión
# conexion.close()

# print("✅ Exportación completada: historia_clinica.csv")




from supabase import create_client, Client

# URL de tu proyecto Supabase y tu clave pública (anon key)
url = "https://iyulfnxxhxgxlumsgsly.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5dWxmbnh4aHhneGx1bXNnc2x5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzNjIzOTcsImV4cCI6MjA2NTkzODM5N30.ZCvtfSU_fRv5UtCOf-9pQoulu1RVjYpfZRy2FD_-_N4"

supabase: Client = create_client(url, key)

# Obtener todos los registros de una tabla
data = supabase.table("citas").select("*").execute()

print("Datos de la tabla citas:")
print(data.data)
