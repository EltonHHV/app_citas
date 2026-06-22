import json
from supabase import create_client

# Credenciales hardcodeadas
SUPABASE_URL = "https://iyulfnxxhxgxlumsgsly.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5dWxmbnh4aHhneGx1bXNnc2x5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzNjIzOTcsImV4cCI6MjA2NTkzODM5N30.ZCvtfSU_fRv5UtCOf-9pQoulu1RVjYpfZRy2FD_-_N4"

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

def get_samples(table_name):
    try:

        # Para citas y doctores obtener los últimos 20 registros
        if table_name.lower() in ["citas", "doctores"]:
            res = (
                supabase
                .table(table_name)
                .select("*")
                .order("id", desc=True)
                .limit(20)
                .execute()
            )

        # Para el resto de tablas obtener 2 registros
        else:
            res = (
                supabase
                .table(table_name)
                .select("*")
                .limit(2)
                .execute()
            )

        return res.data if res.data else []

    except Exception as e:
        print(f"⚠️ Error consultando {table_name}: {e}")
        return []


def main():
    try:
        response = supabase.rpc("get_db_structure").execute()
        tables = response.data

        if not tables:
            print("⚠️ No se encontraron tablas")
            return

        lines = []

        for table in tables:
            table_name = table["table_name"]

            lines.append("")
            lines.append("=" * 70)
            lines.append(f"📦 TABLA: {table_name}")
            lines.append("=" * 70)

            lines.append("")

            lines.append("🧱 COLUMNAS:")
            for col in table.get("columns", []):
                lines.append(
                    f"   - {col['column_name']} ({col['data_type']})"
                )

            lines.append("")
            lines.append("📄 REGISTROS:")

            samples = get_samples(table_name)

            if samples:

                if table_name.lower() in ["citas", "doctores"]:
                    lines.append(
                        f"   Mostrando últimos {len(samples)} registros:"
                    )
                else:
                    lines.append(
                        f"   Mostrando {len(samples)} registros de muestra:"
                    )

                for i, row in enumerate(samples, start=1):
                    lines.append("")
                    lines.append(f"   Registro {i}")

                    lines.append(
                        json.dumps(
                            row,
                            indent=4,
                            ensure_ascii=False,
                            default=str
                        )
                    )
            else:
                lines.append("   ⚠️ Sin registros")

            lines.append("")

        output = "\n".join(lines)

        print(output)

        with open(
            "estructura_bd.txt",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(output)

        print("\n✅ Información guardada en estructura_bd.txt")

    except Exception as e:
        print(f"❌ Error general: {e}")


if __name__ == "__main__":
    main()