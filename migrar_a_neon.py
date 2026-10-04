import json
import psycopg2

# 1. PEGA TU CADENA DE CONEXIÓN DE NEON AQUÍ
DATABASE_URL = "postgresql://neondb_owner:npg_wBZ0o6RCpIyK@ep-odd-dew-b5jh2vje-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

print("Conectando a Neon DB...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("¡Conexión exitosa!")
except Exception as e:
    print(f"Error de conexión: {e}")
    exit()

# 2. CREACIÓN DE TABLAS EN LA NUBE
print("Creando tablas...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS configuracion (clave VARCHAR PRIMARY KEY, valor VARCHAR);
    CREATE TABLE IF NOT EXISTS periodos (periodo VARCHAR, fecha VARCHAR);
    CREATE TABLE IF NOT EXISTS alumnos_mensuales (id VARCHAR PRIMARY KEY, nino VARCHAR, padre VARCHAR, periodo VARCHAR, asistidas INT, restantes INT, pago VARCHAR);
    CREATE TABLE IF NOT EXISTS alumnos_libres (id VARCHAR PRIMARY KEY, nino VARCHAR, padre VARCHAR, asistidas INT, pagadas INT, estado VARCHAR);
    CREATE TABLE IF NOT EXISTS movimientos (id VARCHAR PRIMARY KEY, tipo VARCHAR, detalle VARCHAR, fecha_op VARCHAR, monto VARCHAR, f_traslado VARCHAR, info_extra VARCHAR);
    CREATE TABLE IF NOT EXISTS asistencias (id VARCHAR PRIMARY KEY, nino VARCHAR, periodo VARCHAR, dia VARCHAR, modalidad VARCHAR);
""")
conn.commit()

# 3. LEER EL ARCHIVO LOCAL
print("Leyendo datos_voley.json...")
try:
    with open("datos_voley.json", "r", encoding="utf-8") as f:
        datos = json.load(f)
except FileNotFoundError:
    print("No se encontró el archivo datos_voley.json en esta carpeta.")
    exit()

# 4. EXPORTAR DATOS A NEON
print("Exportando datos. Por favor espera...")

# Exportar Fondo Previo
if datos.get("fondo_previo"):
    cur.execute(
        "INSERT INTO configuracion (clave, valor) VALUES (%s, %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor",
        ("fondo_previo", str(datos["fondo_previo"]))
    )

# Exportar Periodos (Limpiamos la tabla primero para evitar duplicados si corres el script 2 veces)
cur.execute("TRUNCATE periodos")
for periodo, fechas in datos.get("periodos", {}).items():
    for fecha in fechas:
        cur.execute("INSERT INTO periodos (periodo, fecha) VALUES (%s, %s)", (periodo, fecha))

# Exportar Mensuales
for m in datos.get("mensuales", []):
    cur.execute(
        "INSERT INTO alumnos_mensuales VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (m[0], m[1], m[2], m[3], m[4], m[5], m[6])
    )

# Exportar Libres
for l in datos.get("libres", []):
    cur.execute(
        "INSERT INTO alumnos_libres VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (l[0], l[1], l[2], l[3], l[4], l[5])
    )

# Exportar Movimientos de Tesorería
for mov in datos.get("movimientos", []):
    cur.execute(
        "INSERT INTO movimientos VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (mov[0], mov[1], mov[2], mov[3], str(mov[4]), mov[5], mov[6])
    )

# Exportar Asistencias
for a in datos.get("asistencias_detalle", []):
    cur.execute(
        "INSERT INTO asistencias VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (a[0], a[1], a[2], a[3], a[4])
    )

# Guardar cambios y cerrar conexión
conn.commit()
cur.close()
conn.close()

print("✅ ¡Migración completada exitosamente! Tu base de datos Neon ya tiene toda tu información.")