from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date
from flask import jsonify
from datetime import date, timedelta
from datetime import date, timedelta
from datetime import datetime
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session


app = Flask(__name__)

# Agregar una clave secreta para manejar la sesión
app.secret_key = 'tu_clave_secreta'  # Cambia 'tu_clave_secreta' por algo más seguro

from supabase import create_client, Client

# URL de tu proyecto Supabase y tu clave pública (anon key)
SUPABASE_URL = "https://iyulfnxxhxgxlumsgsly.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5dWxmbnh4aHhneGx1bXNnc2x5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzNjIzOTcsImV4cCI6MjA2NTkzODM5N30.ZCvtfSU_fRv5UtCOf-9pQoulu1RVjYpfZRy2FD_-_N4"

# Crear cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Método para interactuar con la base de datos
def get_db_connection():
    return supabase  # Retorna el cliente de Supabase para usarlo en las consultas


@app.route("/", methods=["GET"])
def inicio():
    return redirect(url_for("nueva_cita"))

@app.route("/citas", methods=["GET", "POST"])
def nueva_cita():
    # Procesar envío
    if request.method == "POST":
        paciente = request.form.get("paciente", "").strip()
        motivo = request.form.get("motivo", "").strip()

        # Si el motivo es 'Otro', tomar el valor del campo adicional
        if motivo == "Otro":
            motivo = request.form.get("motivo_otro", "").strip()

        celular = request.form.get("celular", "").strip()
        doctor = request.form.get("doctor", "").strip()
        fecha = request.form.get("fecha", "").strip()
        hora = request.form.get("hora", "").strip()

        # Validaciones
        if not (paciente and motivo and celular and fecha and hora):
            flash("Todos los campos obligatorios deben estar completados.", "warning")
        elif not celular.isdigit() or len(celular) != 9:
            flash("Número de celular inválido. Debe tener 9 dígitos.", "warning")
        else:
            try:
                conn = get_db_connection()
                #SUBABASE:
                supabase.table('citas').insert({
                    'Paciente': paciente,
                    'Motivo': motivo,
                    'Celular': celular,
                    'Fecha': fecha,
                    'Hora': hora,
                    'Doctor': doctor
                }).execute()
                #LOCALMENTE
                # conn.execute(
                #     "INSERT INTO citas (Paciente, Motivo, Celular, Fecha, Hora, Doctor) "
                #     "VALUES (?, ?, ?, ?, ?, ?)",
                #     (paciente, motivo, celular, fecha, hora, doctor)
                # )
                # conn.commit()
                # conn.close()
                flash("Cita guardada exitosamente.", "success")
                # Redirigir para limpiar formulario y evitar repost
                return redirect(url_for("ver_citas"))
            except sqlite3.Error as e:
                flash(f"Error al guardar la cita: {e}", "danger")

    # Cargar datos para el formulario

    #SUBABASE:
    conn = get_db_connection()  # Obtener la conexión de Supabase
    pacientes_unicos = conn.table('historia_clinica').select('nombre').execute().data
    pacientes = {p['nombre'] for p in pacientes_unicos}  # Utilizamos un set para eliminar duplicados
    pacientes = list(pacientes)  # Convertimos el set nuevamente a lista

    doctores = conn.table('doctores').select('id, doctores').execute().data
    motivos = conn.table('motivoconsulta').select('id, descripcion').execute().data


    #LOCALMENTE:
    # conn = get_db_connection()
    # pacientes = conn.execute(
    #     "SELECT DISTINCT nombre FROM historia_clinica ORDER BY nombre"
    # ).fetchall()
    # doctores = conn.execute(
    #     "SELECT id, doctores FROM doctores"
    # ).fetchall()
    # motivos = conn.execute(
    #     "SELECT id, descripcion FROM motivoconsulta"
    # ).fetchall()
    # conn.close()

    # Seleccionar el primer doctor como valor por defecto si no se seleccionó ninguno
    doctor_default = doctores[0]['doctores'] if doctores else ''

    # Determinar qué horas están ocupadas por el doctor y la fecha elegidos
    fecha_sel = request.form.get("fecha", "")
    doctor_sel = request.form.get("doctor", doctor_default)  # Usar el doctor por defecto si no se seleccionó ninguno
    citas_ocup = []
    if fecha_sel and doctor_sel:
        conn2 = get_db_connection()
        #SUBABASE:
        # Reemplazar con la consulta usando Supabase
        filas = conn2.table('citas').select('Hora').eq('Fecha', fecha_sel).eq('Doctor', doctor_sel).execute().data

        #LOCALMENTE

        # filas = conn2.execute(
        #     "SELECT Hora FROM citas WHERE Fecha = ? AND Doctor = ?",
        #     (fecha_sel, doctor_sel)
        # ).fetchall()
        # conn2.close()
        citas_ocup = [f["Hora"] for f in filas]

    hoy = date.today().isoformat()
    

    return render_template(
        "citas.html",
        pacientes=pacientes,
        doctores=doctores,
        motivos=motivos,
        hoy=hoy,
        valores=request.form,
        citas_ocupadas=citas_ocup,
        doctor_default=doctor_default  # Pasamos el valor del doctor por defecto
    )

@app.route("/autocomplete_paciente")
def autocomplete_paciente():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    conn = get_db_connection()
    #SUBASE:
    filas = conn.table('historia_clinica').select('nombre').ilike('nombre', f'{q}%').order('nombre').execute().data
    #LOCALMENTE
    # COLLATE NOCASE hace la búsqueda case‑insensitive
    # filas = conn.execute(
    #     "SELECT nombre FROM historia_clinica WHERE nombre LIKE ? || '%' COLLATE NOCASE ORDER BY nombre",
    #     (q,)
    # ).fetchall()
    # conn.close()
    return jsonify([f["nombre"] for f in filas])

@app.route("/telefono_paciente")
def telefono_paciente():
    nombre = request.args.get("nombre", "").strip()
    if not nombre:
        return jsonify({"telefono": ""})
    conn = get_db_connection()
    #SUBABASE:
    fila = conn.table('historia_clinica').select('telefono').ilike('nombre', nombre).execute().data
    #LOCALMENTE
    # fila = conn.execute(
    #     "SELECT telefono FROM historia_clinica WHERE nombre = ? COLLATE NOCASE",
    #     (nombre,)
    # ).fetchone()
    # conn.close()
    return jsonify({"telefono": fila["telefono"] if fila else ""})

@app.route("/horas_ocupadas")
def horas_ocupadas():
    fecha = request.args.get("fecha", "").strip()
    doctor = request.args.get("doctor", "").strip()
    if not fecha or not doctor:
        return jsonify([])
    conn = get_db_connection()
    #SUBABASE:
    filas = conn.table('citas').select('Hora').eq('Fecha', fecha).eq('Doctor', doctor).execute().data

    #LOCALMENTE:
    # filas = conn.execute(
    #     "SELECT Hora FROM citas WHERE Fecha = ? AND Doctor = ?",
    #     (fecha, doctor)
    # ).fetchall()
    # conn.close()
    return jsonify([f["Hora"] for f in filas])







@app.route("/ver_citas", methods=["GET", "POST"])
def ver_citas():
    hoy = date.today()

    # Si no hay fecha de inicio de semana en la sesión, se establece a esta semana
    if 'start_of_week' not in session:
        start_of_week = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
        end_of_week = start_of_week + timedelta(days=6)     # Domingo de esta semana
    else:
        start_of_week = session['start_of_week']
        end_of_week = session['end_of_week']

    # Asegurarnos de que `start_of_week` y `end_of_week` sean objetos `datetime.date`
    if isinstance(start_of_week, str):
        start_of_week = datetime.strptime(start_of_week, "%a, %d %b %Y %H:%M:%S GMT").date()
    if isinstance(end_of_week, str):
        end_of_week = datetime.strptime(end_of_week, "%a, %d %b %Y %H:%M:%S GMT").date()

    # Si el usuario hace clic en los botones para cambiar la semana
    if request.method == "POST":
        action = request.form.get("action")
        if action == "next":  # Avanzar a la próxima semana
            start_of_week += timedelta(weeks=1)
            end_of_week += timedelta(weeks=1)
        elif action == "prev":  # Retroceder a la semana anterior
            start_of_week -= timedelta(weeks=1)
            end_of_week -= timedelta(weeks=1)

    # Guardar las fechas de inicio y fin en la sesión
    session['start_of_week'] = start_of_week
    session['end_of_week'] = end_of_week

    conn = get_db_connection()

    # Obtener citas de la semana con datos de doctor
    #SUBABASE:
    filas = conn.table('citas').select('citas.id', 'citas.Fecha', 'citas.Hora', 'citas.Motivo', 'citas.Celular', 'citas.Doctor', 'citas.Paciente', 'doctores.color') \
        .join('doctores', 'citas.Doctor', 'doctores.doctores') \
        .gte('Fecha', start_of_week).lte('Fecha', end_of_week).execute().data

    total_doctores = len(conn.table('doctores').select('*').execute().data)
    doctores_leyenda = {d['doctores']: d['color'] for d in conn.table('doctores').select('doctores, color').execute().data}

    #LOCALEMNTE
    # filas = conn.execute(
    #     "SELECT citas.id, citas.Fecha, citas.Hora, citas.Motivo, citas.Celular, citas.Doctor, citas.Paciente, doctores.color "
    #     "FROM citas "
    #     "JOIN doctores ON citas.Doctor = doctores.doctores "
    #     "WHERE citas.Fecha BETWEEN ? AND ?",
    #     (start_of_week, end_of_week)
    # ).fetchall()
    # # Consultar número total de doctores en la tabla doctores
    # total_doctores = conn.execute("SELECT COUNT(*) FROM doctores").fetchone()[0]
    # # Obtener todos los doctores y colores de la tabla doctores para la leyenda
    # doctores_leyenda = dict(conn.execute("SELECT doctores, color FROM doctores").fetchall())
    # conn.close()

    # Agrupar citas y obtener diccionario doctores que tienen citas
    ocupadas = {}
    doctores = {}
    for c in filas:
        fecha = c["Fecha"]
        hora_orig = c["Hora"]
        try:
            hora_obj = datetime.strptime(hora_orig, "%I:%M %p")
        except ValueError:
            hora_obj = datetime.strptime(hora_orig, "%H:%M")
        hora_fmt = hora_obj.strftime("%H:%M")
        key = (fecha, hora_fmt)

        color_lower = c["color"].lower()
        if color_lower == "rojo":
            color_class = "doctor-rojo"
        elif color_lower == "azul":
            color_class = "doctor-azul"
        elif color_lower == "verde":
            color_class = "doctor-verde"
        elif color_lower == "rosado":
            color_class = "doctor-rosado"
        elif color_lower == "naranja":
            color_class = "doctor-naranja"
        else:
            color_class = "doctor-default"

        ocupadas.setdefault(key, []).append({
            "id": c["id"],
            "paciente": c["Paciente"],
            "motivo": c["Motivo"],
            "celular": c["Celular"],
            "doctor": c["Doctor"],
            "fecha": fecha,
            "hora": hora_fmt,
            "hora_original": hora_orig,
            "color_class": color_class
        })
        doctores[c["Doctor"]] = c["color"]

    mostrar_leyenda = (total_doctores >= 2)

    # ...código que ya tienes...
    conn = get_db_connection()
    # Ya tienes citas y colores, ahora agrega:
    pacientes = conn.execute("SELECT DISTINCT nombre FROM historia_clinica ORDER BY nombre").fetchall()
    doctores = conn.execute("SELECT id, doctores FROM doctores").fetchall()
    motivos = conn.execute("SELECT id, descripcion FROM motivoconsulta").fetchall()
    conn.close()
    hoy = date.today().isoformat()


    return render_template(
        "ver_citas.html",
        start_of_week=start_of_week,
        end_of_week=end_of_week,
        ocupadas=ocupadas,
        doctores=doctores,
        doctores_leyenda=doctores_leyenda,
        mostrar_leyenda=mostrar_leyenda,
        pacientes=pacientes,
        motivos=motivos,
        hoy=hoy,
        timedelta=timedelta
    )










@app.route('/editar_cita', methods=['POST'])
def editar_cita():
    id_cita     = request.form['id']
    nueva_fecha = request.form['fecha']
    nueva_hora  = request.form['hora']
    conn = get_db_connection()
    #SUBABASE:
    conn.table('citas').update({
        'Fecha': nueva_fecha,
        'Hora': nueva_hora
    }).eq('id', id_cita).execute()
    #LOCALMENTE
    # conn.execute(
    #     "UPDATE citas SET Fecha = ?, Hora = ? WHERE id = ?",
    #     (nueva_fecha, nueva_hora, id_cita)
    # )
    # conn.commit()
    # conn.close()
    flash('Cita reprogramada correctamente', 'success')
    return redirect(url_for('ver_citas'))

@app.route('/eliminar_cita', methods=['POST'])
def eliminar_cita():
    id_cita = request.form['id']
    conn = get_db_connection()
    #SUBABASE:
    conn.table('citas').delete().eq('id', id_cita).execute()

    #LOCALMENTE 
    # conn.execute("DELETE FROM citas WHERE id = ?", (id_cita,))
    # conn.commit()
    # conn.close()
    flash('Cita cancelada', 'warning')
    return redirect(url_for('ver_citas'))



if __name__ == "__main__":
    # Escucha en 0.0.0.0 para aceptar conexiones desde tu LAN
    app.run(host="0.0.0.0", port=5000, debug=True)
