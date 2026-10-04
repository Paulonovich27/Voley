import streamlit as st
import pandas as pd
import psycopg2
import time
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Sistema Vóley", page_icon="🏐", layout="wide")

# PEGA AQUÍ TU URL DE NEON
DATABASE_URL = "postgresql://usuario:contraseña@ep-tu-base-de-datos.aws.neon.tech/neondb?sslmode=require"

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def run_query(query, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            try: return cur.fetchall()
            except: conn.commit()
    finally:
        conn.close()

def run_update(query, params=()):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
    finally:
        conn.close()

def generar_id():
    return str(int(time.time() * 1000))

def calcular_deuda_profesor():
    hoy = datetime.now().date()
    clases_pasadas = 0
    periodos = run_query("SELECT fecha FROM periodos")
    if periodos:
        for row in periodos:
            try:
                if datetime.strptime(row[0], "%d/%m/%Y").date() <= hoy:
                    clases_pasadas += 1
            except: pass
            
    total_generado = clases_pasadas * 80.0
    total_pagado = 0.0
    movimientos = run_query("SELECT monto FROM movimientos WHERE tipo='Egreso' AND detalle='Pago Profesor'")
    if movimientos:
        for mov in movimientos:
            try: total_pagado += float(mov[0])
            except: pass
            
    return clases_pasadas, total_generado, total_generado - total_pagado

# ==========================================
# 2. SISTEMA DE LOGIN Y PERMISOS
# ==========================================
if "rol" not in st.session_state:
    st.session_state["rol"] = None

if st.session_state["rol"] is None:
    st.markdown("<h1 style='text-align: center;'>🏐 Sistema de Gestión - Vóley</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #6b7280;'>Acceso a la plataforma</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar", use_container_width=True)
            
            if submit:
                # CREA TUS CONTRASEÑAS AQUÍ
                if usuario == "admin" and password == "voleyadmin":
                    st.session_state["rol"] = "admin"
                    st.rerun()
                elif usuario == "vecino" and password == "voley123":
                    st.session_state["rol"] = "vecino"
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
    st.stop() # Detiene la ejecución si no hay login

# Botón para cerrar sesión
with st.sidebar:
    st.write(f"👤 **Sesión actual:** {st.session_state['rol'].capitalize()}")
    if st.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.rerun()

st.title("🏐 Sistema de Gestión - Vóley")

# Obtener listas maestras para ambos roles
res_per = run_query("SELECT DISTINCT periodo FROM periodos")
lista_periodos = [row[0] for row in res_per] if res_per else []

res_m = run_query("SELECT nino FROM alumnos_mensuales")
lista_nombres_m = [row[0] for row in res_m] if res_m else []

res_l = run_query("SELECT nino FROM alumnos_libres")
lista_nombres_l = [row[0] for row in res_l] if res_l else []
lista_todos_nombres = lista_nombres_m + lista_nombres_l


# ==========================================
# 3. VISTA VECINOS (SOLO LECTURA)
# ==========================================
if st.session_state["rol"] == "vecino":
    tab_resumen, tab_asist = st.tabs(["💰 Resumen de Cuentas", "✅ Asistencias"])
    
    with tab_resumen:
        st.header("Transparencia Financiera")
        
        fondo = run_query("SELECT valor FROM configuracion WHERE clave='fondo_previo'")
        fondo_val = float(fondo[0][0]) if fondo else 0.0
        
        total_movs = 0.0
        movs_db = run_query("SELECT tipo, monto FROM movimientos")
        if movs_db:
            for m in movs_db:
                try:
                    if m[0] == "Ingreso": total_movs += float(m[1])
                    elif m[0] == "Egreso": total_movs -= float(m[1])
                except: pass
        
        balance_total = fondo_val + total_movs
        clases, tot_prof, saldo_prof = calcular_deuda_profesor()
        
        col1, col2 = st.columns(2)
        col1.metric("📊 Balance Total en Cuenta", f"S/ {balance_total:.2f}")
        col2.metric("👨‍🏫 Deuda a Profesor", f"S/ {saldo_prof:.2f}", f"{clases} clases dictadas", delta_color="inverse")
        
        st.info("💡 Este panel refleja los ingresos totales, el fondo previo y los pagos realizados al profesor para mantener la transparencia con todos los vecinos.")

    with tab_asist:
        st.header("Historial de Asistencias")
        asistencias_db = run_query("SELECT nino, periodo, dia, modalidad FROM asistencias ORDER BY id DESC")
        if asistencias_db:
            df_a = pd.DataFrame(asistencias_db, columns=["Niño", "Periodo", "Día", "Modalidad"])
            st.dataframe(df_a, use_container_width=True, hide_index=True)
        else:
            st.write("No hay asistencias registradas aún.")


# ==========================================
# 4. VISTA ADMIN (CONTROL TOTAL)
# ==========================================
elif st.session_state["rol"] == "admin":
    tab_per, tab_alum, tab_asis, tab_tes, tab_rep = st.tabs([
        "1. Periodos", "2. Alumnos", "3. Asistencia", "4. Tesorería", "5. Reportes"
    ])

    # --- PESTAÑA 1: PERIODOS ---
    with tab_per:
        st.header("📅 Gestor de Periodos")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Crear / Editar")
            opcion_per = st.selectbox("1. Seleccionar o Crear:", ["-- Nuevo Periodo --"] + lista_periodos)
            nombre_per = st.text_input("2. Nombre:", value="" if opcion_per == "-- Nuevo Periodo --" else opcion_per, disabled=(opcion_per != "-- Nuevo Periodo --"))
            nueva_fecha = st.date_input("3. Agregar Fecha:", format="DD/MM/YYYY")
            
            if st.button("➕ Añadir Día", type="primary"):
                if nombre_per:
                    fecha_str = nueva_fecha.strftime("%d/%m/%Y")
                    existe = run_query("SELECT * FROM periodos WHERE periodo=%s AND fecha=%s", (nombre_per, fecha_str))
                    if not existe:
                        run_update("INSERT INTO periodos (periodo, fecha) VALUES (%s, %s)", (nombre_per, fecha_str))
                        st.success(f"Día {fecha_str} añadido.")
                        st.rerun()

        with col2:
            st.subheader(f"📋 Días Asignados ({nombre_per})")
            if nombre_per:
                dias_db = run_query("SELECT fecha FROM periodos WHERE periodo=%s", (nombre_per,))
                if dias_db:
                    dias_lista = [d[0] for d in dias_db]
                    dias_lista.sort(key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
                    df_dias = pd.DataFrame(dias_lista, columns=["Fechas de Clase"])
                    st.dataframe(df_dias, use_container_width=True, hide_index=True)
                    dia_borrar = st.selectbox("Borrar día:", dias_lista)
                    if st.button("🗑️ Borrar Fecha"):
                        run_update("DELETE FROM periodos WHERE periodo=%s AND fecha=%s", (nombre_per, dia_borrar))
                        st.rerun()

    # --- PESTAÑA 2: ALUMNOS ---
    with tab_alum:
        st.header("➕ Formulario y Lista de Alumnos")
        with st.expander("Registrar Nuevo Alumno", expanded=True):
            with st.form("form_alumno"):
                ca, cb, cc, cd = st.columns(4)
                nino = ca.text_input("Nombre del Niño")
                padre = cb.text_input("Nombre del Padre/Apoderado")
                modalidad = cc.selectbox("Modalidad", ["Mensual", "Libre"])
                periodo_alum = cd.selectbox("Periodo (Mensual)", ["-"] + lista_periodos)
                
                if st.form_submit_button("Guardar Alumno", type="primary") and nino and padre:
                    if modalidad == "Mensual" and periodo_alum != "-":
                        total_clases = run_query("SELECT COUNT(*) FROM periodos WHERE periodo=%s", (periodo_alum,))[0][0]
                        run_update("INSERT INTO alumnos_mensuales VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                   (generar_id(), nino, padre, periodo_alum, 0, total_clases, "No"))
                    else:
                        run_update("INSERT INTO alumnos_libres VALUES (%s, %s, %s, %s, %s, %s)",
                                   (generar_id(), nino, padre, 0, 0, "🔴 Debe"))
                    st.rerun()

        st.subheader("📋 Mensuales")
        alum_m = run_query("SELECT id, nino, padre, periodo, asistidas, restantes, pago FROM alumnos_mensuales")
        if alum_m:
            df_m = pd.DataFrame(alum_m, columns=["ID", "Niño", "Padre", "Periodo", "Asistidas", "Restantes", "Pagó Mes"])
            st.dataframe(df_m.style.apply(lambda r: [f"background-color: {'#1e3a8a' if r['Pagó Mes']=='Sí' else '#7f1d1d'}; color: white"] * len(r), axis=1), use_container_width=True, hide_index=True)
            del_m = st.selectbox("Borrar (ID):", ["-"] + df_m["ID"].tolist(), key="dm")
            if st.button("🗑️ Eliminar Mensual"):
                run_update("DELETE FROM alumnos_mensuales WHERE id=%s", (del_m,))
                st.rerun()

        st.subheader("📋 Libres")
        alum_l = run_query("SELECT id, nino, padre, asistidas, pagadas, estado FROM alumnos_libres")
        if alum_l:
            df_l = pd.DataFrame(alum_l, columns=["ID", "Niño", "Padre", "Asistidas", "Pagadas", "Estado"])
            st.dataframe(df_l.style.apply(lambda r: [f"background-color: {'#065f46' if 'Al Día' in r['Estado'] else '#991b1b'}; color: white"] * len(r), axis=1), use_container_width=True, hide_index=True)
            del_l = st.selectbox("Borrar (ID):", ["-"] + df_l["ID"].tolist(), key="dl")
            if st.button("🗑️ Eliminar Libre"):
                run_update("DELETE FROM alumnos_libres WHERE id=%s", (del_l,))
                st.rerun()

    # --- PESTAÑA 3: ASISTENCIA ---
    with tab_asis:
        st.header("✅ Registro de Asistencia")
        c1, c2, c3 = st.columns(3)
        per_asis = c1.selectbox("1. Periodo:", ["-"] + lista_periodos, key="per_asis")
        
        fechas_asis = ["-"]
        if per_asis != "-":
            d_db = run_query("SELECT fecha FROM periodos WHERE periodo=%s", (per_asis,))
            if d_db:
                fechas_asis = sorted([d[0] for d in d_db], key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            
        dia_asis = c2.selectbox("2. Día:", fechas_asis)
        alum_asis = c3.selectbox("3. Alumno:", ["-"] + lista_todos_nombres)
        
        if st.button("✅ Marcar Asistencia", type="primary"):
            if per_asis != "-" and dia_asis != "-" and alum_asis != "-":
                if run_query("SELECT id FROM asistencias WHERE nino=%s AND periodo=%s AND dia=%s", (alum_asis, per_asis, dia_asis)):
                    st.warning("Ya tiene asistencia en esta fecha.")
                else:
                    mod = None
                    if alum_asis in lista_nombres_m:
                        run_update("UPDATE alumnos_mensuales SET asistidas = asistidas + 1, restantes = restantes - 1 WHERE nino=%s", (alum_asis,))
                        mod = "Mensual"
                    elif alum_asis in lista_nombres_l:
                        run_update("UPDATE alumnos_libres SET asistidas = asistidas + 1 WHERE nino=%s", (alum_asis,))
                        l_data = run_query("SELECT asistidas, pagadas FROM alumnos_libres WHERE nino=%s", (alum_asis,))[0]
                        run_update("UPDATE alumnos_libres SET estado=%s WHERE nino=%s", ("🟢 Al Día" if l_data[1] >= l_data[0] else "🔴 Debe", alum_asis))
                        mod = "Libre"
                    if mod:
                        run_update("INSERT INTO asistencias VALUES (%s, %s, %s, %s, %s)", (generar_id(), alum_asis, per_asis, dia_asis, mod))
                        st.rerun()

        st.subheader("📋 Historial")
        asist_db = run_query("SELECT id, nino, periodo, dia, modalidad FROM asistencias ORDER BY id DESC")
        if asist_db:
            df_a = pd.DataFrame(asist_db, columns=["ID", "Niño", "Periodo", "Día", "Modalidad"])
            st.dataframe(df_a, use_container_width=True, hide_index=True)
            del_a = st.selectbox("Deshacer (ID):", ["-"] + df_a["ID"].tolist())
            if st.button("🗑️ Deshacer Asistencia", type="primary"):
                row = df_a[df_a["ID"] == del_a].iloc[0]
                if row["Modalidad"] == "Mensual": run_update("UPDATE alumnos_mensuales SET asistidas = asistidas - 1, restantes = restantes + 1 WHERE nino=%s", (row["Niño"],))
                else: 
                    run_update("UPDATE alumnos_libres SET asistidas = asistidas - 1 WHERE nino=%s", (row["Niño"],))
                    l_data = run_query("SELECT asistidas, pagadas FROM alumnos_libres WHERE nino=%s", (row["Niño"],))[0]
                    run_update("UPDATE alumnos_libres SET estado=%s WHERE nino=%s", ("🟢 Al Día" if l_data[1] >= l_data[0] else "🔴 Debe", row["Niño"]))
                run_update("DELETE FROM asistencias WHERE id=%s", (del_a,))
                st.rerun()

    # --- PESTAÑA 4: TESORERÍA ---
    with tab_tes:
        fondo = run_query("SELECT valor FROM configuracion WHERE clave='fondo_previo'")
        fondo_val = float(fondo[0][0]) if fondo else 0.0
        
        total_movs = sum([float(m[1]) if m[0] == "Ingreso" else -float(m[1]) for m in run_query("SELECT tipo, monto FROM movimientos") or []])
        balance_total = fondo_val + total_movs
        clases, tot_prof, saldo_prof = calcular_deuda_profesor()
        
        c1, c2 = st.columns(2)
        c1.metric("📊 Balance Total", f"S/ {balance_total:.2f}")
        c2.metric("👨‍🏫 Deuda a Profesor", f"S/ {saldo_prof:.2f}", f"{clases} clases dadas", delta_color="inverse")
        st.divider()

        col_ing, col_eg = st.columns(2)
        with col_ing:
            with st.expander("📥 Registrar Ingreso", expanded=True):
                alum_ing = st.selectbox("Alumno", ["-"] + lista_todos_nombres)
                fecha_pago = st.date_input("F. Pago", format="DD/MM/YYYY")
                monto_ing = st.number_input("Monto (S/)", min_value=0.0)
                fecha_tras = st.date_input("F. Traslado", format="DD/MM/YYYY")
                per_ing = st.selectbox("Periodo (Mensual)", ["-"] + lista_periodos)
                clases_ing = st.number_input("+ N° Clases (Si Libre)", min_value=0)
                
                if st.button("Guardar Ingreso", type="primary") and alum_ing != "-" and monto_ing > 0:
                    info = f"Mes: {per_ing}" if clases_ing == 0 else f"+{clases_ing} Clases"
                    run_update("INSERT INTO movimientos VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               (generar_id(), "Ingreso", alum_ing, fecha_pago.strftime("%d/%m/%Y"), str(monto_ing), fecha_tras.strftime("%d/%m/%Y"), info))
                    if clases_ing > 0:
                        run_update("UPDATE alumnos_libres SET pagadas = pagadas + %s WHERE nino=%s", (clases_ing, alum_ing))
                        ld = run_query("SELECT asistidas, pagadas FROM alumnos_libres WHERE nino=%s", (alum_ing,))[0]
                        run_update("UPDATE alumnos_libres SET estado=%s WHERE nino=%s", ("🟢 Al Día" if ld[1] >= ld[0] else "🔴 Debe", alum_ing))
                    elif per_ing != "-":
                        run_update("UPDATE alumnos_mensuales SET pago='Sí' WHERE nino=%s AND periodo=%s", (alum_ing, per_ing))
                    st.rerun()

        with col_eg:
            with st.expander("📤 Pagar a Profesor", expanded=True):
                fp = st.date_input("F. Pago Prof.", format="DD/MM/YYYY")
                mp = st.number_input("Pago (S/)", min_value=0.0)
                if st.button("Registrar Salida", type="primary") and mp > 0:
                    run_update("INSERT INTO movimientos VALUES (%s, %s, %s, %s, %s, %s, %s)",
                               (generar_id(), "Egreso", "Pago Profesor", fp.strftime("%d/%m/%Y"), str(mp), "-", "-"))
                    st.rerun()
            with st.expander("💰 Configurar Saldo Inicial"):
                fondo_in = st.number_input("Fondo Previo", value=fondo_val)
                if st.button("Actualizar Fondo"):
                    run_update("INSERT INTO configuracion (clave, valor) VALUES ('fondo_previo', %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor", (str(fondo_in),))
                    st.rerun()

        st.subheader("📋 Tabla Movimientos")
        movimientos_db = run_query("SELECT id, tipo, detalle, fecha_op, monto, f_traslado, info_extra FROM movimientos")
        if movimientos_db:
            ml = sorted(list(movimientos_db), key=lambda x: datetime.strptime(x[3], "%d/%m/%Y") if x[3] else datetime.min, reverse=True)
            df_mov = pd.DataFrame(ml, columns=["ID", "Tipo", "Detalle", "Fecha Op.", "Monto", "F. Traslado", "Info Extra"])
            st.dataframe(df_mov.style.apply(lambda r: [f"background-color: {'#065f46' if r['Tipo']=='Ingreso' else '#7f1d1d'}; color: white"] * len(r), axis=1), use_container_width=True, hide_index=True)
            del_mov = st.selectbox("Eliminar (ID):", ["-"] + df_mov["ID"].tolist(), key="dmov")
            if st.button("🗑️ Borrar Movimiento"):
                run_update("DELETE FROM movimientos WHERE id=%s", (del_mov,))
                st.rerun()

    # --- PESTAÑA 5: REPORTES ---
    with tab_rep:
        st.header("📊 Reporte Visual Rápido")
        per_rep = st.selectbox("Evaluar Periodo:", ["-"] + lista_periodos)
        
        if per_rep != "-":
            hoy = datetime.now().date()
            dias_db = run_query("SELECT fecha FROM periodos WHERE periodo=%s", (per_rep,))
            dias_periodo = sorted([d[0] for d in dias_db], key=lambda x: datetime.strptime(x, "%d/%m/%Y")) if dias_db else []
            
            asis_per = run_query("SELECT nino, dia FROM asistencias WHERE periodo=%s", (per_rep,))
            asis_set = set((a[0], a[1]) for a in asis_per) if asis_per else set()
            
            mensuales_per = run_query("SELECT nino, pago FROM alumnos_mensuales WHERE periodo=%s", (per_rep,))
            libres_todos = run_query("SELECT nino, pagadas, estado FROM alumnos_libres")
            nombres_libres_asis = set(a[0] for a in asis_per) if asis_per else set()
            libres_filtrados = [l for l in libres_todos if l[0] in nombres_libres_asis] if libres_todos else []

            if mensuales_per or libres_filtrados:
                html = '<div style="overflow-x: auto;"><table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px; text-align: center;">'
                html += '<tr style="background-color: #1f2937; color: white;">'
                for col in ["Alumno", "Mod", "Pago/Saldo"] + dias_periodo: html += f'<th style="padding: 10px; border: 1px solid #444;">{col}</th>'
                html += '</tr>'
                
                if mensuales_per:
                    for m in mensuales_per:
                        nino, pago = m[0], m[1]
                        bg_fila = '#1e3a8a' if pago == 'Sí' else '#991b1b'
                        html += f'<tr><td style="background-color: {bg_fila}; color: white; padding: 8px; border: 1px solid #444; font-weight: bold; text-align: left;">{nino}</td>'
                        html += f'<td style="background-color: {bg_fila}; color: white; border: 1px solid #444;">Mensual</td>'
                        html += f'<td style="background-color: {bg_fila}; color: white; border: 1px solid #444;">Pagó: {pago}</td>'
                        
                        for dia in dias_periodo:
                            try: f_clase = datetime.strptime(dia, "%d/%m/%Y").date()
                            except: f_clase = hoy
                            if f_clase > hoy: html += f'<td style="background-color: {bg_fila}; border: 1px solid #444;"></td>'
                            else:
                                if (nino, dia) in asis_set: html += f'<td style="background-color: #059669; color: white; border: 1px solid #444; font-weight: bold;">Asistió</td>'
                                else: html += f'<td style="background-color: {"#ea580c" if pago=="Sí" else bg_fila}; color: white; border: 1px solid #444; font-weight: bold;">Faltó</td>'
                        html += '</tr>'
                        
                if libres_filtrados:
                    for l in libres_filtrados:
                        nino, pagadas, estado = l[0], l[1], l[2]
                        bg_fila = '#065f46' if 'Al Día' in estado else '#991b1b'
                        html += f'<tr><td style="background-color: {bg_fila}; color: white; padding: 8px; border: 1px solid #444; font-weight: bold; text-align: left;">{nino}</td>'
                        html += f'<td style="background-color: {bg_fila}; color: white; border: 1px solid #444;">Libre</td>'
                        html += f'<td style="background-color: {bg_fila}; color: white; border: 1px solid #444;">Pagadas: {pagadas}</td>'
                        
                        for dia in dias_periodo:
                            try: f_clase = datetime.strptime(dia, "%d/%m/%Y").date()
                            except: f_clase = hoy
                            if f_clase > hoy: html += f'<td style="background-color: {bg_fila}; border: 1px solid #444;"></td>'
                            else:
                                if (nino, dia) in asis_set: html += f'<td style="background-color: #059669; color: white; border: 1px solid #444; font-weight: bold;">Asistió</td>'
                                else: html += f'<td style="background-color: {bg_fila}; border: 1px solid #444;"></td>'
                        html += '</tr>'
                        
                html += '</table></div>'
                st.markdown(html, unsafe_allow_html=True)
                st.write("") 
                
                total_per = sum([float(m[0]) for m in run_query("SELECT monto FROM movimientos WHERE tipo='Ingreso' AND info_extra LIKE %s", (f"%Mes: {per_rep}%",)) or []])
                st.success(f"💰 Recaudación exacta del Periodo '{per_rep}': **S/ {total_per:.2f}**")
            else:
                st.info("No hay alumnos con asistencia en este periodo.")