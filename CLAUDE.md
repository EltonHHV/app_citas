# CLAUDE.md - AI Assistant Guide for App Citas

## Project Overview

**App Citas** is a Flask-based medical/dental appointment management system designed for multiple clinics (consultorios) in Peru and Chile. The application handles appointment scheduling, patient management, and supports multi-branch operations for larger clinics.

### Technology Stack

- **Backend**: Flask (Python 3.x)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML/CSS with Bootstrap, Vanilla JavaScript
- **Deployment**: Gunicorn (Heroku-ready with Procfile)
- **Dependencies**: See `requirements.txt`
  - Flask
  - gunicorn
  - psycopg2-binary
  - supabase
  - pytz

## Architecture & File Structure

```
app_citas/
├── app.py                          # Main Flask application (743 lines)
├── requirements.txt                # Python dependencies
├── Procfile                        # Heroku deployment config
├── static/
│   ├── css/
│   │   ├── citas.css              # Styling for appointment creation
│   │   └── ver_citas.css          # Styling for calendar views
│   ├── logo.ico                    # Favicon
│   ├── recordatorio.png            # Reminder icon
│   └── wsp.png                     # WhatsApp icon
└── templates/
    ├── layout.html                 # Base template
    ├── login.html                  # Login page
    ├── citas.html                  # Create appointment form
    ├── ver_citas.html              # Weekly calendar view
    └── ver_citas_mensual.html      # Monthly calendar view
```

## Database Schema

### Key Tables (Supabase)

1. **doctores**
   - `id` (INTEGER, PRIMARY KEY)
   - `doctores` (TEXT) - Doctor/branch name
   - `password` (TEXT) - Plain text password (security concern)
   - `pago` (BOOLEAN) - Subscription status
   - `consultorio_id` (INTEGER, FK to consultorios)
   - `sedes` (TEXT) - 'SI' or 'NO' (has multiple branches)
   - `especialidad` (TEXT) - 'Dental', 'Obstétrico', 'Estético'
   - `color` (TEXT) - Color code for calendar display

2. **citas** (appointments)
   - `id` (INTEGER, PRIMARY KEY)
   - `Paciente` (TEXT)
   - `Motivo` (TEXT)
   - `Celular` (TEXT) - 9-digit phone number
   - `Fecha` (DATE)
   - `Hora` (TEXT) - Format: "HH:MM AM/PM"
   - `Doctor` (TEXT) - Doctor/branch name
   - `Asistencia` (BOOLEAN)
   - `consultorio_id` (INTEGER)

3. **consultorios**
   - `id` (INTEGER, PRIMARY KEY)
   - `nombre` (TEXT)
   - `nacionalidad` (TEXT) - 'Peru' or 'Chile'

4. **historia_clinica** (patient history)
   - `nombre` (TEXT)
   - `telefono` (TEXT)
   - `doctor_id` (INTEGER)

5. **motivoconsulta** (appointment reasons)
   - `id` (INTEGER)
   - `descripcion` (TEXT)
   - `especialidad` (TEXT)

## Application Routes

### Authentication Routes

- **`/login`** (GET, POST)
  - Validates doctor credentials
  - Checks subscription status (`pago` field)
  - Sets session with `doctor_id`

- **`/logout`**
  - Clears session

### Main Application Routes

- **`/`** (GET) - Redirects to `/citas`
  - Protected by `@check_subscription` decorator

- **`/citas`** (GET, POST) - Create new appointment
  - Shows form with autocomplete for patients
  - Filters doctors by consultorio and specialty
  - Validates 9-digit phone numbers

- **`/ver_citas`** (GET, POST) - Weekly calendar view
  - Displays 7-day week grid (Monday-Sunday)
  - Shows 8:00 AM - 8:00 PM time slots (30-minute intervals)
  - Color-coded by doctor
  - Navigation: prev/next week buttons

- **`/ver_citas_mensual`** (GET, POST) - Monthly calendar view
  - Full month calendar with all appointments
  - Groups AM/PM appointments
  - Color-coded by doctor

### AJAX/API Routes

- **`/horas_ocupadas`** (GET)
  - Returns occupied time slots for a specific date and doctor
  - Used for real-time availability checking

- **`/autocomplete_paciente`** (GET)
  - Returns patient names matching search query
  - Scoped to logged-in doctor

- **`/telefono_paciente`** (GET)
  - Retrieves phone number for selected patient

### CRUD Operations

- **`/editar_cita`** (POST)
  - Updates appointment date, time, motivo, and celular
  - Redirects to `/ver_citas`

- **`/eliminar_cita`** (POST)
  - Soft delete of appointment
  - Redirects to `/ver_citas`

- **`/editarxd`** (POST)
  - AJAX version of edit (returns JSON)

- **`/eliminarxd`** (POST)
  - AJAX version of delete (returns JSON)

## Key Features & Business Logic

### 1. Multi-Sede (Multi-Branch) Support

The system supports two operational modes:

**Single Doctor Mode** (`sedes = 'NO'`):
- Doctor sees only their own appointments
- Time slots are exclusive (cannot double-book)

**Multi-Sede Mode** (`sedes = 'SI'`):
- Multiple branches/doctors share same consultorio_id
- Each branch can book same time slot independently
- All branches of same consultorio see all appointments
- Doctor selection shows all branches with same specialty

Implementation in `app.py:172-181`:
```python
if tiene_sedes:
    # Get ALL appointments from consultorio
    filas = conn.table('citas').select(...).eq('consultorio_id', consultorio_id)
else:
    # Get only this doctor's appointments
    filas = conn.table('citas').select(...).eq('Doctor', doctor_name)
```

### 2. Subscription Management

All main routes are protected by `@check_subscription` decorator (lines 55-71):
- Checks if doctor is logged in
- Validates `pago = True` in database
- Redirects to login if subscription inactive

### 3. Specialty-Based Filtering

Appointment reasons (motivos) are filtered by doctor's specialty:
- Dental clinics see dental-specific motivos
- Obstetric clinics see obstetric-specific motivos
- Prevents irrelevant options from appearing

Implementation in `app.py:376-380`:
```python
if especialidad_doctor:
    motivos = conn.table('motivoconsulta').select('id, descripcion').eq('especialidad', especialidad_doctor)
```

### 4. Nationality Handling

Special handling for Chilean vs Peruvian clinics:
- `consultorio_id = 13` is hardcoded as Chile
- Affects WhatsApp message templates and formatting
- Default nationality is 'Peru'

See `app.py:196-206` and `app.py:669-684`

### 5. Color Coding System

Doctors are assigned colors for visual distinction in calendars:
- Supported colors: Rojo, Azul, Verde, Rosado, Naranja, Morado
- Maps to CSS classes: `doctor-rojo`, `doctor-azul`, etc.
- Hex color mapping in `app.py:580-591`

### 6. Time Slot Management

- Available hours: 8:00 AM - 8:00 PM
- 30-minute intervals
- Format: 12-hour AM/PM (e.g., "02:30 PM")
- Hardcoded in `citas.html:134-140`

### 7. Patient Autocomplete

Real-time patient search with phone number auto-fill:
- Searches `historia_clinica` table
- Scoped to doctor's own patients
- Auto-populates phone number on selection

## Important Constants

### CONSULTORIOS Dictionary (app.py:30-46)

Maps consultorio IDs to display names with emojis:
```python
CONSULTORIOS = {
    1: "de la Clínica Odontológica Godental",
    2: "de la Clínica Dental Virodent",
    ...
    12: "del CONSULTORIO OBSTETRICO FERMUJER🌸",
    14: "del CONSULTORIO OBSTETRICO PROMUJER🌺",
    15: "del CONSULTORIO OBSTETRICO DE MUJER A MUJER❤️",
    16: "del CENTRO ESTÉTICO MELIDERMA❤️",
}
```

**Note**: Some consultorios use emojis in their names.

### Supabase Configuration (app.py:1-2)

**⚠️ SECURITY CONCERN**: Credentials are hardcoded in source code:
```python
SUPABASE_URL = "https://iyulfnxxhxgxlumsgsly.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Development Conventions

### 1. Language

- **Primary Language**: Spanish
  - All UI text, flash messages, variables
  - Database column names in Spanish (Paciente, Fecha, Hora, Motivo, Celular)
  - Comments in code are in Spanish

### 2. Naming Conventions

**Database Columns**:
- PascalCase for column names: `Paciente`, `Fecha`, `Hora`, `Motivo`
- Lowercase for table names: `doctores`, `citas`, `historia_clinica`

**Python Variables**:
- snake_case: `doctor_id`, `tiene_sedes`, `consultorio_nombre`
- Some inconsistency with camelCase in older code

**JavaScript Variables**:
- camelCase: `pacienteInput`, `doctorSelect`, `fechaInput`

### 3. Form Handling

- Uses Flask's `request.form.get()` with `.strip()`
- Flash messages for user feedback
- Bootstrap 5 styling
- Client-side validation before server-side

### 4. Session Management

```python
session["doctor_id"] = doctor_id
session.permanent = True
```

### 5. Error Handling

- Try-except blocks for database operations
- Flash messages with categories: 'success', 'warning', 'danger', 'error'
- Minimal error logging (prints to console)

### 6. Template Inheritance

All templates extend `layout.html`:
```jinja
{% extends "layout.html" %}
{% block content %}...{% endblock %}
{% block scripts %}...{% endblock %}
```

## Common Development Tasks

### Adding a New Consultorio

1. Add entry to `CONSULTORIOS` dictionary in `app.py`
2. Insert record in Supabase `consultorios` table
3. Create doctor account(s) with `consultorio_id`
4. Update nationality handling if not Peru (lines 196-206, 669-684)

### Adding a New Appointment Reason (Motivo)

1. Insert into `motivoconsulta` table with appropriate `especialidad`
2. Will automatically appear in forms filtered by specialty

### Modifying Time Slots

Edit `horarios` array in `templates/citas.html:134-140`

### Adding a New Doctor/Branch

1. Insert into `doctores` table
2. Set appropriate `consultorio_id`, `especialidad`, `color`, `sedes`
3. If multi-sede, ensure other doctors in same consultorio have `sedes='SI'`

## Security Considerations

### Known Issues

1. **Hardcoded Credentials** (app.py:1-2)
   - Supabase URL and key in source code
   - Should use environment variables

2. **Plain Text Passwords** (app.py:95-109)
   - Passwords stored in plain text
   - Direct comparison without hashing

3. **Secret Key** (app.py:19)
   - Weak secret key: `'xddx'`
   - Should use cryptographically secure random key

4. **SQL Injection Risk**
   - Mitigated by Supabase client library
   - But should still validate/sanitize inputs

5. **No CSRF Protection**
   - Forms lack CSRF tokens
   - Consider adding Flask-WTF

### Recommendations for AI Assistants

When making changes:
- ✅ DO suggest moving credentials to environment variables
- ✅ DO recommend password hashing (bcrypt, argon2)
- ✅ DO add input validation
- ❌ DON'T commit new hardcoded secrets
- ❌ DON'T remove existing functionality without user approval

## Testing Considerations

### No Automated Tests

This project currently has no test suite. When adding features:

1. **Manual Testing Checklist**:
   - Test login with valid/invalid credentials
   - Test subscription check (pago=True/False)
   - Create appointment with all field variations
   - Test multi-sede vs single-doctor behavior
   - Verify time slot availability logic
   - Check nationality-based differences

2. **Edge Cases to Consider**:
   - Same patient, different doctors
   - Same time slot, different branches
   - Month boundary transitions
   - Timezone handling (Peru uses America/Lima)
   - Phone number validation (exactly 9 digits)

## Frontend Patterns

### AJAX Requests

Standard pattern for AJAX endpoints:
```javascript
const res = await fetch(`/endpoint?param=${encodeURIComponent(value)}`);
const data = await res.json();
```

### Modal Handling

Bootstrap 5 modals for:
- Editing appointments
- Viewing multiple appointments at same time
- Deleting confirmations

### Form Validation

Two-level validation:
1. HTML5 `required` attributes
2. JavaScript validation before submit
3. Server-side validation in Flask

## Deployment

### Heroku Deployment

The `Procfile` specifies:
```
web: gunicorn app:app
```

### Environment Setup

Required environment variables (should be set):
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SECRET_KEY`

**Note**: Currently these are hardcoded but should be migrated to environment variables.

### Port Configuration

```python
app.run(host="0.0.0.0", port=5000, debug=True)
```

Set `debug=False` for production.

## Common Pitfalls for AI Assistants

### 1. Don't Break Multi-Sede Logic

When modifying appointment queries, always consider both modes:
- Single doctor: filter by `Doctor = doctor_name`
- Multi-sede: filter by `consultorio_id`

### 2. Preserve Time Format

Always use 12-hour AM/PM format for display:
- Database stores: "02:30 PM"
- Internal processing may use 24-hour: "14:30"
- Always convert for display

### 3. Respect Nationality Context

Chile (consultorio_id=13) has special handling. When modifying:
- Check lines 196-206 (ver_citas)
- Check lines 669-684 (ver_citas_mensual)
- Check lines 276-279 (nacionalidad assignment)

### 4. Phone Number Validation

Always validate 9 digits:
```python
if not celular.isdigit() or len(celular) != 9:
    flash("Número de celular inválido. Debe tener 9 dígitos.", "warning")
```

### 5. Session State

Several routes depend on session state:
- `start_of_week` (ver_citas)
- `end_of_week` (ver_citas)
- `start_of_month` (ver_citas_mensual)

Clear or update appropriately when modifying navigation.

### 6. Color Class Mapping

When adding new doctor colors, update:
1. Database `doctores.color` field
2. `COLORES_HEX` dictionary (app.py:580-591)
3. CSS classes in `ver_citas.css`

## Code Quality Notes

### Areas for Improvement

1. **Code Duplication**
   - Duplicate imports (lines 9-12)
   - Similar logic in editarxd/editar_cita
   - Nacionalidad checks repeated multiple times

2. **Magic Numbers**
   - Hardcoded consultorio_id checks (13 for Chile)
   - Should use constants

3. **Comments**
   - Many Spanish comments
   - Some outdated/incorrect comments
   - Debug prints left in code (line 725)

4. **Function Length**
   - `ver_citas()` is 227 lines
   - `ver_citas_mensual()` is 189 lines
   - Consider refactoring into smaller functions

### Recommended Refactoring (for AI assistants to suggest)

```python
# Good practice for nacionalidad check
CHILE_CONSULTORIO_ID = 13
DEFAULT_NACIONALIDAD = 'Peru'

def get_nacionalidad(consultorio_id):
    return 'Chile' if consultorio_id == CHILE_CONSULTORIO_ID else DEFAULT_NACIONALIDAD
```

## Git Workflow

### Branch Naming

Current development branch:
```
claude/claude-md-mic8mxct5hdcksh5-01G5MTanHP9NfqFUzgkb4vaN
```

### Recent Commits Pattern

Recent commits show pattern:
```
feat: Update emoji for CONSULTORIO OBSTETRICO PROMUJER for consistency
feat: Update emoji for CONSULTORIO OBSTETRICO FERMUJER for consistency
feat: Add CENTRO ESTÉTICO MELIDERMA to CONSULTORIOS dictionary
```

Use conventional commit format: `feat:`, `fix:`, `refactor:`, etc.

### What to Commit

- ✅ Feature additions
- ✅ Bug fixes
- ✅ Consultorio updates
- ❌ Debugging code
- ❌ Commented-out code
- ❌ Hardcoded credentials

## Integration Points

### WhatsApp Integration

Images suggest WhatsApp integration:
- `static/wsp.png` - WhatsApp icon
- `static/recordatorio.png` - Reminder icon

Likely used for appointment reminders (not visible in current code).

### Timezone Handling

Peru timezone:
```python
tz_peru = pytz.timezone('America/Lima')
hoy = datetime.now(tz_peru).date()
```

Important for appointment scheduling across timezones.

## Quick Reference for Common Operations

### Query Appointments

```python
# Single doctor
filas = conn.table('citas').select('*').eq('Doctor', doctor_name).execute().data

# Multi-sede (all consulorio)
filas = conn.table('citas').select('*').eq('consultorio_id', consultorio_id).execute().data

# Date range
filas = conn.table('citas').select('*').gte('Fecha', start).lte('Fecha', end).execute().data
```

### Create Appointment

```python
conn.table('citas').insert({
    'Paciente': paciente,
    'Motivo': motivo,
    'Celular': celular,
    'Fecha': fecha,
    'Hora': hora,
    'Doctor': doctor_seleccionado,
    'Asistencia': False,
    'consultorio_id': consultorio_id
}).execute()
```

### Update Appointment

```python
conn.table('citas').update({
    'Fecha': nueva_fecha,
    'Hora': nueva_hora,
    'Motivo': nuevo_motivo,
    'Celular': nuevo_celular
}).eq('id', id_cita).execute()
```

### Delete Appointment

```python
conn.table('citas').delete().eq('id', id_cita).execute()
```

## Special UI Behaviors

### Multiple Appointments at Same Time

When 2+ appointments share same time slot:
- Cell shows "X CITAS" with orange background
- Click opens modal to select which appointment to view

### Color-Coded Calendar

Each doctor has assigned color visible in weekly/monthly view:
- Helps distinguish multiple doctors/branches
- Legend shown when 2+ doctors exist

### Dynamic Form Fields

- "Otro" (Other) option in Motivo triggers text input
- Doctor/Sede label changes based on consultorio_id
- Time slots marked "OCUPADO" when taken

## Final Notes for AI Assistants

### Before Making Changes

1. **Understand the context**: Is this single-doctor or multi-sede?
2. **Check nacionalidad**: Does this affect Peru or Chile?
3. **Verify specialty**: Is this Dental, Obstétrico, or Estético?
4. **Test across views**: Changes affect both weekly and monthly views

### When in Doubt

- Preserve existing behavior unless explicitly asked to change
- Suggest security improvements but don't force them
- Ask user before refactoring working code
- Spanish is the primary language - keep it consistent

### Code Style to Follow

```python
# Good: Existing pattern
conn = get_db_connection()
doctor_data = conn.table('doctores').select('field').eq('id', doctor_id).execute().data

# Good: Flash messages in Spanish
flash("Cita guardada exitosamente.", "success")

# Good: Descriptive variable names
tiene_sedes = doctor_info[0].get('sedes', 'NO') == 'SI'

# Good: Date formatting
hoy = date.today().isoformat()
```

---

**Last Updated**: 2025-11-23
**Project Status**: Active development
**Primary Maintainer**: Repository owner
**AI Assistant**: Use this guide for context when making changes
