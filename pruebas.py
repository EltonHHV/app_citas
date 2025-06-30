from supabase import create_client

# Definir las credenciales de conexión a Supabase
SUPABASE_URL = "https://iyulfnxxhxgxlumsgsly.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5dWxmbnh4aHhneGx1bXNnc2x5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzNjIzOTcsImV4cCI6MjA2NTkzODM5N30.ZCvtfSU_fRv5UtCOf-9pQoulu1RVjYpfZRy2FD_-_N4"

# Crear un cliente de Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ejecutar la función 'get_tables_and_columns' creada en el paso anterior
response = supabase.rpc('get_tables_and_columns').execute()

# Verificar si se obtuvieron resultados
if response.data:
    # Imprimir las tablas y sus columnas
    for row in response.data:
        print(f"Tabla: {row['table_name']} - Columna: {row['column_name']}")
else:
    print("No se encontraron tablas ni columnas.")