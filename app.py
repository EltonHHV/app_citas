SUPABASE_URL = "https://iyulfnxxhxgxlumsgsly.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5dWxmbnh4aHhneGx1bXNnc2x5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzNjIzOTcsImV4cCI6MjA2NTkzODM5N30.ZCvtfSU_fRv5UtCOf-9pQoulu1RVjYpfZRy2FD_-_N4"

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import calendar
import pytz

from datetime import date
from flask import jsonify
from datetime import date, timedelta
from datetime import date, timedelta
from datetime import datetime
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from functools import wraps
app = Flask(__name__)
app.secret_key = 'xddx'  # Cambia esto por una clave secreta real

# SUPABASE_URL = "***********"
# SUPABASE_KEY = "***********"


# Crear cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Método para interactuar con la base de datos


CONSULTORIOS = {
    1: "de la Clínica Odontológica Godental",
    2: "de la Clínica Dental Virodent",
    3: "de la Clínica Dental Aldana",
    4: "del Centro Dental Enríquez",
    5: "del Consultorio Odontológico Ruguzdent",
    7: "del Consultorio Dental Saludent",
}


# Método para interactuar con la base de datos
def get_db_connection():
    return supabase  # Retorna el cliente de Supabase para usarlo en las consultas

# Decorador para verificar si el doctor tiene la suscripción activa
def check_subscription(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        doctor_id = session.get("doctor_id")
        if not doctor_id:
            flash("Por favor, inicie sesión", "warning")
            return redirect(url_for("login"))  # Redirige a login si no está autenticado

        conn = get_db_connection()
        doctor = conn.table('doctores').select('id', 'pago').eq('id', doctor_id).execute().data

        if not doctor or not doctor[0]['pago']:
            flash("Por favor, renueve su suscripción para acceder al sistema.", "warning")
            return redirect(url_for("login"))  # Redirigir al login si el pago es False

        return func(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
@check_subscription
def inicio():
    return redirect(url_for("nueva_cita"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        doctor_id = request.form.get("doctor_id").strip()
        password = request.form.get("password").strip()

        # Verificar las credenciales del doctor en la base de datos
        conn = get_db_connection()

        # Convertir doctor_id a entero si es necesario
        try:
            doctor_id_int = int(doctor_id)
        except ValueError:
            flash("ID de doctor inválido", "danger")
            return redirect(url_for("login"))

        # Obtener el doctor y su estado de pago
        doctor = conn.table('doctores').select('id', 'doctores', 'password', 'pago').eq('id', doctor_id_int).execute().data

        # Verificar que se encuentre el doctor, la contraseña sea correcta y el pago sea True
        if doctor:
            if doctor[0]['password'] == password:
                if doctor[0]['pago'] == True:
                    session["doctor_id"] = doctor_id  # Guardamos el id del doctor en la sesión
                    session.permanent = True  # Hace que la sesión sea permanente
                    return redirect(url_for("nueva_cita"))  # Redirigir a la página de citas
                else:
                    flash("Por favor, renueve su suscripción para acceder al sistema.", "warning")
                    return redirect(url_for("login"))
            else:
                flash("Contraseña incorrecta", "danger")
                return redirect(url_for("login"))
        else:
            flash("Doctor no encontrado", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")  # Si el método es GET, mostramos el formulario de login



@app.route("/ver_citas", methods=["GET", "POST"])
@check_subscription
def ver_citas():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        flash("Por favor, inicie sesión", "warning")
        return redirect(url_for("login"))  # Redirige a login si no está autenticado

    # Obtener el nombre del doctor
    conn = get_db_connection()
    doctor = conn.table('doctores').select('doctores').eq('id', doctor_id).execute().data
    doctor_name = doctor[0]['doctores'] if doctor else ''

    hoy = date.today()

    if 'start_of_week' not in session:
        start_of_week = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
        end_of_week = start_of_week + timedelta(days=6)     # Domingo de esta semana
    else:
        start_of_week = session['start_of_week']
        end_of_week = session['end_of_week']

    if isinstance(start_of_week, str):
        start_of_week = datetime.strptime(start_of_week, "%a, %d %b %Y %H:%M:%S GMT").date()
    if isinstance(end_of_week, str):
        end_of_week = datetime.strptime(end_of_week, "%a, %d %b %Y %H:%M:%S GMT").date()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "next":  
            start_of_week += timedelta(weeks=1)
            end_of_week += timedelta(weeks=1)
        elif action == "prev": 
            start_of_week -= timedelta(weeks=1)
            end_of_week -= timedelta(weeks=1)

    session['start_of_week'] = start_of_week
    session['end_of_week'] = end_of_week

    # Obtener citas solo para el doctor autenticado (por nombre)
    filas = conn.table('citas').select('id', 'Fecha', 'Hora', 'Motivo', 'Celular', 'Doctor', 'Paciente') \
        .gte('Fecha', start_of_week).lte('Fecha', end_of_week).eq('Doctor', doctor_name).execute().data

    doctores_data = conn.table('doctores').select('doctores', 'color').execute().data
    doctores_dict = {doctor['doctores']: doctor['color'] for doctor in doctores_data}

    for cita in filas:
        doctor_color = doctores_dict.get(cita['Doctor'], 'default_color') 
        cita['color'] = doctor_color  

    total_doctores = len(doctores_data)

    doctores_leyenda = {doctor['doctores']: doctor['color'] for doctor in doctores_data}

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

        color_class = {
            "rojo": "doctor-rojo",
            "azul": "doctor-azul",
            "verde": "doctor-verde",
            "rosado": "doctor-rosado",
            "naranja": "doctor-naranja"
        }.get(c["color"].lower(), "doctor-default")

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

    conn = get_db_connection()
    pacientes = conn.table('historia_clinica').select('nombre').eq('doctor_id', doctor_id).execute().data
    motivos = conn.table('motivoconsulta').select('id, descripcion').execute().data
    hoy = date.today().isoformat()

    return render_template(
        "ver_citas.html",
        start_of_week=start_of_week,
        end_of_week=end_of_week,
        ocupadas=ocupadas,
        doctores=doctores,
        doctores_leyenda=doctores_leyenda,
        mostrar_leyenda=mostrar_leyenda,
        pacientes=pacientes,  # Solo pacientes de ese doctor
        motivos=motivos,
        hoy=hoy,
        doctor_name=doctor_name,  # Enviar nombre del doctor autenticado
        timedelta=timedelta
    )



@app.route("/citas", methods=["GET", "POST"])
@check_subscription
def nueva_cita():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        flash("Por favor, inicie sesión", "warning")
        return redirect(url_for("login"))  # Redirige a login si no está autenticado

    # Obtener el nombre del doctor para guardarlo y el consultorio_id
    conn = get_db_connection()
    doctor = conn.table('doctores').select('doctores', 'consultorio_id').eq('id', doctor_id).execute().data
    doctor_name = doctor[0]['doctores'] if doctor else ''
    consultorio_id = doctor[0]['consultorio_id'] if doctor else None  # Obtener el consultorio_id del doctor

    # Procesar el envío del formulario
    if request.method == "POST":
        paciente = request.form.get("paciente", "").strip()
        motivo = request.form.get("motivo", "").strip()
        if motivo == "Otro":
            motivo = request.form.get("motivo_otro", "").strip()
        celular, doctor, fecha, hora = (request.form.get(field, "").strip() for field in ["celular", "doctor", "fecha", "hora"])
        asistencia = False  

        if not (paciente and motivo and celular and fecha and hora):
            flash("Todos los campos obligatorios deben estar completados.", "warning")
        elif not celular.isdigit() or len(celular) != 9:
            flash("Número de celular inválido. Debe tener 9 dígitos.", "warning")
        else:
            try:
                # Guardamos el consultorio_id junto con los demás datos
                conn = get_db_connection()
                supabase.table('citas').insert({
                    'Paciente': paciente,
                    'Motivo': motivo,
                    'Celular': celular,
                    'Fecha': fecha,
                    'Hora': hora,
                    'Doctor': doctor_name,  # Guardamos el nombre del doctor
                    'Asistencia': asistencia,
                    'consultorio_id': consultorio_id  # Guardamos el consultorio_id
                }).execute()

                flash("Cita guardada exitosamente.", "success")
                return redirect(url_for("ver_citas"))
            except Exception as e:
                flash(f"Error al guardar la cita: {e}", "danger")

    # Obtener lista de pacientes, doctores y motivos
    pacientes_unicos = conn.table('historia_clinica').select('nombre').execute().data
    pacientes = {p['nombre'] for p in pacientes_unicos}  # Utilizamos un set para eliminar duplicados
    pacientes = list(pacientes)  # Convertimos el set nuevamente a lista

    # Filtrar solo el doctor actual
    doctores = conn.table('doctores').select('id, doctores').eq('id', doctor_id).execute().data
    motivos = conn.table('motivoconsulta').select('id, descripcion').execute().data

    doctor_default = doctores[0]['doctores'] if doctores else ''

    fecha_sel = request.form.get("fecha", "")
    doctor_sel = request.form.get("doctor", doctor_default)
    citas_ocup = []
    if fecha_sel and doctor_sel:
        conn2 = get_db_connection()
        filas = conn2.table('citas').select('Hora').eq('Fecha', fecha_sel).eq('Doctor', doctor_name).execute().data
        citas_ocup = [f["Hora"] for f in filas]

    hoy = date.today().isoformat()

    return render_template(
        "citas.html",
        pacientes=pacientes,
        doctores=doctores,  # Solo el doctor que ha iniciado sesión
        motivos=motivos,
        hoy=hoy,
        valores=request.form,
        citas_ocupadas=citas_ocup,
        doctor_default=doctor_default
    )



@app.route("/horas_ocupadas")
def horas_ocupadas():
    doctor_id = session.get("doctor_id")
    fecha = request.args.get("fecha", "").strip()
    if not fecha or not doctor_id:
        return jsonify([])

    conn = get_db_connection()

    # Obtener el nombre del doctor autenticado
    doctor = conn.table('doctores').select('doctores').eq('id', doctor_id).execute().data
    doctor_name = doctor[0]['doctores'] if doctor else ''

    # Filtrar horas ocupadas para ese doctor en particular (usando su nombre)
    filas = conn.table('citas').select('Hora').eq('Fecha', fecha).eq('Doctor', doctor_name).execute().data
    return jsonify([f["Hora"] for f in filas])




@app.route("/autocomplete_paciente")
def autocomplete_paciente():
    doctor_id = session.get("doctor_id")
    q = request.args.get("q", "").strip()
    if not q or not doctor_id:
        return jsonify([])

    conn = get_db_connection()
    # Filtrar pacientes solo para el doctor autenticado
    filas = conn.table('historia_clinica').select('nombre').eq('doctor_id', doctor_id).ilike('nombre', f'{q}%').order('nombre').execute().data
    return jsonify([f["nombre"] for f in filas])


@app.route("/telefono_paciente")
def telefono_paciente():
    nombre = request.args.get("nombre", "").strip()
    doctor_id = session.get("doctor_id")  # Obtener el doctor_id de la sesión
    if not nombre or not doctor_id:
        return jsonify({"telefono": ""})

    conn = get_db_connection()
    # Filtrar teléfono solo para pacientes del doctor autenticado
    filas = conn.table('historia_clinica').select('telefono').eq('doctor_id', doctor_id).ilike('nombre', nombre).execute().data
    if filas:
        fila = filas[0]
        return jsonify({"telefono": fila["telefono"] if fila.get("telefono") else ""})
    return jsonify({"telefono": ""})


@app.route('/editar_cita', methods=['POST'])
def editar_cita():
    id_cita     = request.form['id']
    nueva_fecha = request.form['fecha']
    nueva_hora  = request.form['hora']
    conn = get_db_connection()
    conn.table('citas').update({
        'Fecha': nueva_fecha,
        'Hora': nueva_hora
    }).eq('id', id_cita).execute()
    flash('Cita reprogramada correctamente', 'success')
    return redirect(url_for('ver_citas'))

@app.route('/eliminar_cita', methods=['POST'])
def eliminar_cita():
    id_cita = request.form['id']
    conn = get_db_connection()
    conn.table('citas').delete().eq('id', id_cita).execute()
    flash('Cita cancelada', 'warning')
    return redirect(url_for('ver_citas'))





@app.route('/editarxd', methods=['POST'])
def editarxd():
    id_cita     = request.form['id']
    nueva_fecha = request.form['fecha']
    nueva_hora  = request.form['hora']
    conn = get_db_connection()
    conn.table('citas').update({
        'Fecha': nueva_fecha,
        'Hora': nueva_hora
    }).eq('id', id_cita).execute()
    return jsonify({"success": True, "message": "Cita reprogramada correctamente"})


@app.route('/eliminarxd', methods=['POST'])
def eliminarxd():
    id_cita = request.form['id']
    conn = get_db_connection()
    conn.table('citas').delete().eq('id', id_cita).execute()
    return jsonify({"success": True, "message": "Cita cancelada"})



@app.route("/logout")
def logout():
    session.pop("doctor_id", None)  # Eliminar el doctor_id de la sesión
    return redirect(url_for("login"))  # Redirigir a la página de login








from datetime import datetime, timedelta, date
import calendar
@app.route("/ver_citas_mensual", methods=["GET", "POST"])
@check_subscription
def ver_citas_mensual():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        flash("Por favor, inicie sesión", "warning")
        return redirect(url_for("login"))  # Redirige a login si no está autenticado

    # Obtener el nombre del doctor
    conn = get_db_connection()
    doctor = conn.table('doctores').select('doctores', 'consultorio_id').eq('id', doctor_id).execute().data
    doctor_name = doctor[0]['doctores'] if doctor else ''
    consultorio_id = doctor[0]['consultorio_id'] if doctor else None
    consultorio_nombre = CONSULTORIOS.get(consultorio_id, "Nuestra clínica")


    hoy = date.today()

    if 'start_of_month' not in session:
        start_of_month = hoy.replace(day=1)  # Primer día del mes
    else:
        start_of_month_str = session['start_of_month']
        if isinstance(start_of_month_str, str):
            start_of_month = datetime.strptime(start_of_month_str, '%a, %d %b %Y %H:%M:%S GMT').date()
        else:
            start_of_month = start_of_month_str

    # Lógica para el mes siguiente o anterior
    if request.method == "POST":
        action = request.form.get("action")
        if action == "next_month":
            if start_of_month.month == 12:
                start_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1, day=1)
            else:
                start_of_month = start_of_month.replace(month=start_of_month.month + 1, day=1)
        elif action == "prev_month":
            if start_of_month.month == 1:
                start_of_month = start_of_month.replace(year=start_of_month.year - 1, month=12, day=1)
            else:
                start_of_month = start_of_month.replace(month=start_of_month.month - 1, day=1)

    session['start_of_month'] = start_of_month

    # Obtener citas para este mes
    last_day_of_month = calendar.monthrange(start_of_month.year, start_of_month.month)[1]
    end_of_month = start_of_month.replace(day=last_day_of_month)

    filas = conn.table('citas').select('id', 'Fecha', 'Hora', 'Motivo', 'Celular', 'Doctor', 'Paciente') \
        .gte('Fecha', start_of_month).lte('Fecha', end_of_month).eq('Doctor', doctor_name).execute().data

    # Configura la zona horaria de Chimbote (Perú)
    tz_peru = pytz.timezone('America/Lima')

    ocupadas = {}
    for c in filas:
        fecha = c["Fecha"]

        # Asegúrate de que la variable 'fecha' sea un objeto datetime
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()  # Convierte de str a datetime.date

        hora = c["Hora"]
        key = fecha.strftime('%Y-%m-%d')
        ocupadas[key] = ocupadas.get(key, [])
        ocupadas[key].append({
            "id": c["id"],
            "paciente": c["Paciente"],
            "motivo": c["Motivo"],
            "celular": c["Celular"],
            "doctor": c["Doctor"],
            "fecha": fecha,
            "hora": hora
        })

    # Ordenar las citas AM y PM, AM primero y luego PM
    for fecha, citas in ocupadas.items():
        # Separar las citas en AM y PM
        citas_am = [cita for cita in citas if "AM" in cita["hora"]]
        citas_pm = [cita for cita in citas if "PM" in cita["hora"]]

        # Ordenar las citas AM y PM por hora
        citas_am.sort(key=lambda cita: datetime.strptime(cita["hora"], '%I:%M %p'))
        citas_pm.sort(key=lambda cita: datetime.strptime(cita["hora"], '%I:%M %p'))

        # Reunir las citas ordenadas (primero AM, luego PM)
        ocupadas[fecha] = citas_am + citas_pm

    # Crear la cuadrícula para el calendario mensual
    weeks = []
    current_day = start_of_month

    # Determina el primer día de la semana (en qué día cae el primer día del mes)
    first_day_of_week = start_of_month.weekday()  # 0=Monday, 6=Sunday
    first_day_of_week = (first_day_of_week +1) % 7  # +1 para ajustar el cálculo y hacer que el martes sea 0, etc.

    # Empieza el calendario con días vacíos antes del primer día del mes
    while current_day.month == start_of_month.month:
        week = []
        # Deja las celdas vacías antes del primer día del mes
        for _ in range(first_day_of_week):
            week.append({"date": None})
        # Rellena los días del mes
        while len(week) < 7 and current_day.month == start_of_month.month:
            week.append({"date": current_day})
            current_day += timedelta(days=1)
        weeks.append(week)
        first_day_of_week = 0  # Después de la primera semana, no dejamos celdas vacías.

    # Convertir la fecha de hoy a la hora de Perú (Chimbote)
    hoy = datetime.now(tz_peru).date()

    return render_template(
        "ver_citas_mensual.html",
        start_of_month=start_of_month,
        weeks=weeks,
        ocupadas=ocupadas,
        today=hoy,  # Pasa la fecha actual al template con la hora de Perú)
        consultorio=consultorio_nombre
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
