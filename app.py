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
    8: "de la Clínica Dental Santa Apolonia 2",
    9: "del Consultorio Obstétrico Happuch",
    10: "de la CLÍNICA BRAVO'S DENTAL",
    11: "de la CLÍNICA CLARDENT",
    12: "del CONSULTORIO OBSTETRICO FERMUJER",
    13: "de la CLINICA DENTAL SOMI",
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
        return redirect(url_for("login"))

    # Obtener información completa del doctor incluyendo sedes, consultorio_id y especialidad
    conn = get_db_connection()
    doctor_info = conn.table('doctores').select('doctores, consultorio_id, sedes, especialidad').eq('id', doctor_id).execute().data
    
    if not doctor_info:
        flash("Doctor no encontrado", "danger")
        return redirect(url_for("login"))
    
    doctor_name = doctor_info[0]['doctores']
    consultorio_id = doctor_info[0]['consultorio_id']
    tiene_sedes = doctor_info[0].get('sedes', 'NO') == 'SI'
    especialidad_doctor = doctor_info[0].get('especialidad', 'Dental')

    # Imprimir consultorio_id para ver qué estamos recibiendo
    print(f"Consultorio ID recibido: {consultorio_id}")

    # Obtener información del consultorio del doctor logueado
    consultorio_data = conn.table('consultorios').select('nombre', 'nacionalidad').eq('id', consultorio_id).execute().data
    consultorio_nombre = consultorio_data[0]['nombre'] if consultorio_data else "Nuestra clínica"

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

    # Obtener citas según si tiene múltiples sedes o no
    if tiene_sedes:
        # Si tiene sedes=SI, obtener TODAS las citas del consultorio (todas las sedes)
        # ✅ MODIFICADO: Ahora incluimos consultorio_id en el select
        filas = conn.table('citas').select('id', 'Fecha', 'Hora', 'Motivo', 'Celular', 'Doctor', 'Paciente', 'consultorio_id') \
            .gte('Fecha', start_of_week).lte('Fecha', end_of_week).eq('consultorio_id', consultorio_id).execute().data
    else:
        # Si tiene sedes=NO, obtener solo las citas de ese doctor específico
        # ✅ MODIFICADO: Ahora incluimos consultorio_id en el select
        filas = conn.table('citas').select('id', 'Fecha', 'Hora', 'Motivo', 'Celular', 'Doctor', 'Paciente', 'consultorio_id') \
            .gte('Fecha', start_of_week).lte('Fecha', end_of_week).eq('Doctor', doctor_name).execute().data

    # ✅ NUEVO: Obtener todos los consultorios para mapear nacionalidades
    todos_consultorios = conn.table('consultorios').select('id', 'nombre', 'nacionalidad').execute().data
    consultorios_dict = {c['id']: c for c in todos_consultorios}

    doctores_data = conn.table('doctores').select('doctores', 'color').execute().data
    doctores_dict = {doctor['doctores']: doctor['color'] for doctor in doctores_data}

    # Recuerda que el bucle debería ser sobre 'filas', y la variable es 'cita', no 'c'
    for cita in filas:
        doctor_color = doctores_dict.get(cita['Doctor'], 'default_color') 
        cita['color'] = doctor_color

        # ✅ NUEVO: Agregar nacionalidad del consultorio de la cita
        cita_consultorio_id = cita.get('consultorio_id')
        print(f"Consultorio ID de la cita: {cita_consultorio_id}")
        
        # Si el consultorio_id es 13, asignamos directamente "Chile" como nacionalidad
        if cita_consultorio_id == 13:
            cita['nacionalidad'] = 'Chile'
            cita['consultorio_nombre'] = "Consultorio Chile"
            print("Nacionalidad asignada directamente: Chile")
        else:
            # En cualquier otro caso, usamos el valor por defecto "Peru"
            cita['nacionalidad'] = cita.get("nacionalidad", "Peru")  # Aquí es donde respetamos "Peru" por defecto
            cita['consultorio_nombre'] = consultorio_nombre
            print(f"Nacionalidad asignada: {cita['nacionalidad']}")


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
            "naranja": "doctor-naranja",
            "morado": "doctor-morado"
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
            "color_class": color_class,
            "nacionalidad": c.get("nacionalidad", "Peru"),  # Respetamos el valor por defecto
            "consultorio_nombre": c.get("consultorio_nombre", consultorio_nombre)  # Usamos el nombre del consultorio
        })
        doctores[c["Doctor"]] = c["color"]

    mostrar_leyenda = (total_doctores >= 2)

    # Obtener lista de pacientes
    pacientes = conn.table('historia_clinica').select('nombre').eq('doctor_id', doctor_id).execute().data
    
    # Filtrar motivos por especialidad del DOCTOR
    if especialidad_doctor:
        motivos = conn.table('motivoconsulta').select('id, descripcion').eq('especialidad', especialidad_doctor).execute().data
    else:
        motivos = conn.table('motivoconsulta').select('id, descripcion').execute().data
    
    # Obtener lista de doctores/sedes para el select del modal
    if tiene_sedes:
        # Si tiene sedes, obtener todas las sedes del mismo consultorio con la misma especialidad
        doctores_select = conn.table('doctores').select('id, doctores, consultorio_id, sedes, especialidad')\
            .eq('consultorio_id', consultorio_id)\
            .eq('sedes', 'SI')\
            .eq('especialidad', especialidad_doctor)\
            .execute().data
    else:
        # Si no tiene sedes, solo mostrar el doctor actual
        doctores_select = conn.table('doctores').select('id, doctores, consultorio_id, sedes, especialidad')\
            .eq('id', doctor_id)\
            .execute().data

    hoy_iso = date.today().isoformat()

    # Si el consultorio_id es 13, asignamos directamente 'Chile'
    if consultorio_id == 13:
        nacionalidad = 'Chile'
    else:
        nacionalidad =  'Peru'  # Usamos el valor por defecto 'Peru' si no está

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
        hoy=hoy_iso,
        doctor_name=doctor_name,
        doctores_select=doctores_select,
        tiene_multiples_sedes=tiene_sedes,
        consultorio_nombre=consultorio_nombre,  # Nombre del consultorio del doctor logueado
        nacionalidad=nacionalidad,  # Aseguramos que la nacionalidad es pasada correctamente
        timedelta=timedelta
    )






@app.route("/citas", methods=["GET", "POST"])
@check_subscription
def nueva_cita():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        flash("Por favor, inicie sesión", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    
    # Obtener información completa del doctor incluyendo sedes y especialidad
    doctor_info = conn.table('doctores').select('doctores, consultorio_id, sedes, especialidad').eq('id', doctor_id).execute().data
    if not doctor_info:
        flash("Doctor no encontrado", "danger")
        return redirect(url_for("login"))
    
    doctor_name = doctor_info[0]['doctores']
    consultorio_id = doctor_info[0]['consultorio_id']
    tiene_sedes = doctor_info[0].get('sedes', 'NO') == 'SI'
    especialidad_doctor = doctor_info[0].get('especialidad', 'Dental')  # Especialidad del doctor

    # Procesar el envío del formulario
    if request.method == "POST":
        paciente = request.form.get("paciente", "").strip()
        motivo = request.form.get("motivo", "").strip()
        if motivo == "Otro":
            motivo = request.form.get("motivo_otro", "").strip()
        celular = request.form.get("celular", "").strip()
        doctor_seleccionado = request.form.get("doctor", "").strip()  # Este es el nombre del doctor (o sede)
        fecha = request.form.get("fecha", "").strip()
        hora = request.form.get("hora", "").strip()
        asistencia = False

        if not (paciente and motivo and celular and fecha and hora):
            flash("Todos los campos obligatorios deben estar completados.", "warning")
        elif not celular.isdigit() or len(celular) != 9:
            flash("Número de celular inválido. Debe tener 9 dígitos.", "warning")
        else:
            try:
                # Guardamos la cita con el nombre del doctor en la columna 'Doctor'
                conn.table('citas').insert({
                    'Paciente': paciente,
                    'Motivo': motivo,
                    'Celular': celular,
                    'Fecha': fecha,
                    'Hora': hora,
                    'Doctor': doctor_seleccionado,  # Usamos el nombre del doctor/sede directamente
                    'Asistencia': asistencia,
                    'consultorio_id': consultorio_id
                }).execute()

                flash("Cita guardada exitosamente.", "success")
                return redirect(url_for("ver_citas"))
            except Exception as e:
                flash(f"Error al guardar la cita: {e}", "danger")

    # Obtener lista de pacientes
    pacientes_unicos = conn.table('historia_clinica').select('nombre').execute().data
    pacientes = list({p['nombre'] for p in pacientes_unicos})

    # Obtener doctores según si tiene múltiples sedes o no
    if tiene_sedes:
        doctores = conn.table('doctores').select('id, doctores, consultorio_id, sedes, especialidad')\
            .eq('consultorio_id', consultorio_id)\
            .eq('sedes', 'SI')\
            .eq('especialidad', especialidad_doctor)\
            .execute().data
    else:
        doctores = conn.table('doctores').select('id, doctores, consultorio_id, sedes, especialidad').eq('id', doctor_id).execute().data

    # Filtrar motivos por especialidad del DOCTOR (no del consultorio)
    if especialidad_doctor:
        motivos = conn.table('motivoconsulta').select('id, descripcion').eq('especialidad', especialidad_doctor).execute().data
    else:
        motivos = conn.table('motivoconsulta').select('id, descripcion').execute().data

    doctor_default = doctor_name

    hoy = date.today().isoformat()

    return render_template(
        "citas.html",
        pacientes=pacientes,
        doctores=doctores,
        motivos=motivos,
        hoy=hoy,
        valores=request.form,
        doctor_default=doctor_default,
        tiene_multiples_sedes=tiene_sedes
    )


@app.route("/horas_ocupadas")
def horas_ocupadas():
    doctor_id = session.get("doctor_id")
    fecha = request.args.get("fecha", "").strip()
    doctor_seleccionado = request.args.get("doctor", "").strip()
    
    if not fecha or not doctor_id or not doctor_seleccionado:
        return jsonify([])

    conn = get_db_connection()

    # Obtener solo las citas del doctor/sede específico seleccionado
    # Cada sede es independiente, solo mostramos ocupadas las horas de ESA sede
    filas = conn.table('citas').select('Hora').eq('Fecha', fecha).eq('Doctor', doctor_seleccionado).execute().data
    
    return jsonify([f["Hora"] for f in filas])


@app.route("/autocomplete_paciente")
def autocomplete_paciente():
    doctor_id = session.get("doctor_id")
    q = request.args.get("q", "").strip()
    if not q or not doctor_id:
        return jsonify([])

    conn = get_db_connection()
    filas = (
        conn.table('historia_clinica')
        .select('nombre')
        .eq('doctor_id', doctor_id)
        .ilike('nombre', f'%{q}%')
        .order('nombre')
        .execute()
        .data
    )

    return jsonify([f["nombre"] for f in filas])


@app.route("/telefono_paciente")
def telefono_paciente():
    nombre = request.args.get("nombre", "").strip()
    doctor_id = session.get("doctor_id")
    if not nombre or not doctor_id:
        return jsonify({"telefono": ""})

    conn = get_db_connection()
    filas = conn.table('historia_clinica').select('telefono').eq('doctor_id', doctor_id).ilike('nombre', nombre).execute().data
    if filas:
        fila = filas[0]
        return jsonify({"telefono": fila["telefono"] if fila.get("telefono") else ""})
    return jsonify({"telefono": ""})


@app.route('/editar_cita', methods=['POST'])
def editar_cita():
    # Obtener campos obligatorios (reprogramación)
    id_cita     = request.form['id']
    nueva_fecha = request.form['fecha']
    nueva_hora  = request.form['hora']
    
    # Obtener campos editables (Motivo y Celular)
    # Usamos .get() por seguridad, aunque los campos serán obligatorios
    nuevo_motivo = request.form.get('motivo')
    nuevo_celular = request.form.get('celular') 

    conn = get_db_connection()
    
    # Preparamos el objeto de actualización con todos los campos
    datos_a_actualizar = {
        'Fecha': nueva_fecha,
        'Hora': nueva_hora,
        # Incluimos los nuevos campos editables
        'Motivo': nuevo_motivo,
        'Celular': nuevo_celular
    }
    
    conn.table('citas').update(datos_a_actualizar).eq('id', id_cita).execute()
    
    flash('Cita actualizada correctamente', 'success')
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
    # Obtener campos de reprogramación
    id_cita     = request.form['id']
    nueva_fecha = request.form['fecha']
    nueva_hora  = request.form['hora']
    
    # Obtener nuevos campos editables
    nuevo_motivo = request.form.get('motivo')
    nuevo_celular = request.form.get('celular')
    
    conn = get_db_connection()
    
    # Preparamos el objeto de actualización
    datos_a_actualizar = {
        'Fecha': nueva_fecha,
        'Hora': nueva_hora,
        # Incluimos las columnas de tu BD: "Motivo" y "Celular"
        'Motivo': nuevo_motivo,
        'Celular': nuevo_celular
    }
    
    conn.table('citas').update(datos_a_actualizar).eq('id', id_cita).execute()
    
    return jsonify({"success": True, "message": "Cita actualizada correctamente"})



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
from datetime import datetime, timedelta, date
import calendar

@app.route("/ver_citas_mensual", methods=["GET", "POST"])
@check_subscription
def ver_citas_mensual():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        flash("Por favor, inicie sesión", "warning")
        return redirect(url_for("login"))

    # Obtener el nombre del doctor y verificar si maneja múltiples sedes
    conn = get_db_connection()
    doctor_data = conn.table('doctores').select('doctores', 'consultorio_id', 'sedes').eq('id', doctor_id).execute().data
    
    if not doctor_data:
        flash("Doctor no encontrado", "error")
        return redirect(url_for("login"))
    
    doctor_name = doctor_data[0]['doctores']
    consultorio_id = doctor_data[0]['consultorio_id']
    tiene_sedes = doctor_data[0]['sedes'] == 'SI'
    
    # Imprimir el consultorio_id en la consola
    print(f"Consultorio ID: {consultorio_id}")

    # Obtener información del consultorio del doctor logueado
    consultorio_data = conn.table('consultorios').select('nombre', 'nacionalidad').eq('id', consultorio_id).execute().data
    consultorio_nombre = consultorio_data[0]['nombre'] if consultorio_data else "Nuestra clínica"

    # ✅ NUEVO: Obtener todos los consultorios para mapear nacionalidades
    todos_consultorios = conn.table('consultorios').select('id', 'nombre', 'nacionalidad').execute().data
    consultorios_dict = {c['id']: c for c in todos_consultorios}

    # Mapeo de nombres de colores en español a códigos hexadecimales
    COLORES_HEX = {
        'Azul': "#ABCDF4",
        'Morado': "#E0A7F7",
        'Verde': '#27AE60',
        'Rojo': '#E74C3C',
        'Naranja': '#F39C12',
        'Rosado': '#FF69B4',
        'Celeste': '#87CEEB',
        'Amarillo': '#F1C40F',
        'Gris': '#95A5A6',
        'Turquesa': '#1ABC9C'
    }

    # Si tiene_sedes = SI, obtener todos los doctores del mismo consultorio con sus colores
    if tiene_sedes:
        doctores_del_consultorio = conn.table('doctores').select('doctores', 'color').eq('consultorio_id', consultorio_id).execute().data
        nombres_doctores = [d['doctores'] for d in doctores_del_consultorio]
        colores_doctores = {
            d['doctores']: COLORES_HEX.get(d['color'], '#95A5A6') 
            for d in doctores_del_consultorio
        }
    else:
        nombres_doctores = [doctor_name]
        colores_doctores = {}

    hoy = date.today()

    if 'start_of_month' not in session:
        start_of_month = hoy.replace(day=1)
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

    # ✅ MODIFICADO: Incluir consultorio_id en el select
    query = conn.table('citas').select('id', 'Fecha', 'Hora', 'Motivo', 'Celular', 'Doctor', 'Paciente', 'consultorio_id') \
        .gte('Fecha', start_of_month).lte('Fecha', end_of_month)
    
    if len(nombres_doctores) == 1:
        query = query.eq('Doctor', nombres_doctores[0])
    else:
        query = query.in_('Doctor', nombres_doctores)
    
    filas = query.execute().data

    tz_peru = pytz.timezone('America/Lima')

    ocupadas = {}
    for c in filas:
        fecha = c["Fecha"]
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()

        hora = c["Hora"]
        key = fecha.strftime('%Y-%m-%d')
        ocupadas[key] = ocupadas.get(key, [])
        
        # ✅ NUEVO: Agregar nacionalidad y nombre del consultorio de la cita
        cita_consultorio_id = c.get('consultorio_id')

        # Asegurarse de que el ID del consultorio sea un número entero para evitar comparaciones incorrectas
        print(f"Consultorio ID recibido: {cita_consultorio_id}")

        # Convertir el ID a int (si es necesario) para asegurarnos de que sea comparable con las claves en el diccionario
        cita_consultorio_id = int(cita_consultorio_id) if cita_consultorio_id else None

        # Verificar que el ID está bien convertido a entero
        print(f"Consultorio ID convertido: {cita_consultorio_id}")

        # Si el consultorio_id es 13, asignamos directamente 'Chile'
        if cita_consultorio_id == 13:
            nacionalidad_cita = 'Chile'
            consultorio_nombre_cita = "la CLINICA DENTAL SOMI"  # Asignamos un nombre de consultorio para Chile
            print("Nacionalidad asignada directamente: Chile")
        else:
            # Verificar si el consultorio ID está en el diccionario de consultorios
            if cita_consultorio_id and cita_consultorio_id in consultorios_dict:
                consultorio_info = consultorios_dict[cita_consultorio_id]  # Accedemos al consultorio

                print(f"Consultorio encontrado: {consultorio_info}")

                nacionalidad_cita = consultorio_info['nacionalidad']
                consultorio_nombre_cita = consultorio_info['nombre']  # Asignamos el nombre del consultorio encontrado
                print(f"Nacionalidad asignada: {nacionalidad_cita}")
            else:
                # Si el consultorio no se encuentra, asignamos la nacionalidad por defecto como Perú
                nacionalidad_cita = 'Peru'  # Default es Perú
                consultorio_nombre_cita = consultorio_nombre  # Usamos el nombre del consultorio predeterminado
                print(f"Consultorio no encontrado, asignada nacionalidad por defecto: {nacionalidad_cita}")

        # Agregar la cita a las ocupadas
        ocupadas[key].append({
            "id": c["id"],
            "paciente": c["Paciente"],
            "motivo": c["Motivo"],
            "celular": c["Celular"],
            "doctor": c["Doctor"],
            "fecha": fecha,
            "hora": hora,
            "nacionalidad": nacionalidad_cita,  # ✅ NUEVO
            "consultorio_nombre": consultorio_nombre_cita  # ✅ NUEVO
        })

    for fecha, citas in ocupadas.items():
        citas_am = [cita for cita in citas if "AM" in cita["hora"]]
        citas_pm = [cita for cita in citas if "PM" in cita["hora"]]
        citas_am.sort(key=lambda cita: datetime.strptime(cita["hora"], '%I:%M %p'))
        citas_pm.sort(key=lambda cita: datetime.strptime(cita["hora"], '%I:%M %p'))
        ocupadas[fecha] = citas_am + citas_pm

    weeks = []
    current_day = start_of_month
    first_day_of_week = start_of_month.weekday()
    first_day_of_week = (first_day_of_week + 1) % 7

    while current_day.month == start_of_month.month:
        week = []
        for _ in range(first_day_of_week):
            week.append({"date": None})
        while len(week) < 7 and current_day.month == start_of_month.month:
            week.append({"date": current_day})
            current_day += timedelta(days=1)
        weeks.append(week)
        first_day_of_week = 0

    hoy = datetime.now(tz_peru).date()

    return render_template(
        "ver_citas_mensual.html",
        start_of_month=start_of_month,
        weeks=weeks,
        ocupadas=ocupadas,
        today=hoy,
        consultorio=consultorio_nombre,  # Nombre del consultorio del doctor logueado
        tiene_sedes=tiene_sedes,
        colores_doctores=colores_doctores
    )



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
