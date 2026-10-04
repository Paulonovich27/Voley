import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from PIL import ImageGrab 
import json
import os
import time

# ==========================================
# GESTIÓN DE DATOS LOCALES
# ==========================================
ARCHIVO_DATOS = "datos_voley.json"

def generar_id():
    return str(int(time.time() * 1000))

def cargar_datos():
    datos_por_defecto = {
        "fondo_previo": None, 
        "periodos": {},          
        "mensuales": [],         
        "libres": [],            
        "movimientos": [],       
        "asistencias_detalle": []
    }
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as file:
                datos = json.load(file)
                for key in datos_por_defecto:
                    if key not in datos: datos[key] = datos_por_defecto[key]
                return datos
        except: pass
    return datos_por_defecto

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as file:
        json.dump(datos, file, indent=4)

datos_locales = cargar_datos()
id_alumno_editando = None

# ==========================================
# LÓGICA DEL PAGO AL PROFESOR (S/ 80 x CLASE)
# ==========================================
def calcular_deuda_profesor():
    hoy = datetime.now().date()
    clases_pasadas = 0
    
    for per, dias in datos_locales["periodos"].items():
        for dia in dias:
            try:
                fecha_clase = datetime.strptime(dia, "%d/%m/%Y").date()
                if fecha_clase <= hoy:
                    clases_pasadas += 1
            except: pass
            
    total_generado = clases_pasadas * 80.0
    
    total_pagado = 0.0
    for mov in datos_locales["movimientos"]:
        if mov[1] == "Egreso" and "Profesor" in mov[2]:
            try: total_pagado += float(mov[4])
            except: pass
            
    saldo_pendiente = total_generado - total_pagado
    return clases_pasadas, total_generado, saldo_pendiente

# ==========================================
# ACTUALIZACIONES GLOBALES DE UI
# ==========================================
def recargar_combos():
    per = list(datos_locales["periodos"].keys())
    if not per: per = ["-"]
    
    combo_editar_per.configure(values=["-- Nuevo Periodo --"] + per)
    combo_per_crear.configure(values=per)
    combo_per_asis.configure(values=per)
    combo_per_t.configure(values=per)
    combo_per_rep.configure(values=per) 
    
    nombres_m = [m[1] for m in datos_locales["mensuales"]]
    nombres_l = [l[1] for l in datos_locales["libres"]]
    todos_nombres = nombres_m + nombres_l
    
    combo_alum_asis.configure(values=todos_nombres if todos_nombres else ["-"])
    combo_alum_t.configure(values=todos_nombres if todos_nombres else ["-"])

# ==========================================
# ESTILO PARA EL DATEENTRY (CALENDARIO MEJORADO)
# ==========================================
estilo_calendario = {
    "width": 14,
    "font": ('Arial', 14),
    "background": '#1e3a8a',
    "foreground": 'white',
    "borderwidth": 0,
    "date_pattern": 'dd/mm/yyyy',
    "headersbackground": '#1f2937',     # Fondo oscurecido para los dias de la semana
    "headersforeground": 'white',
    "selectbackground": '#059669',      # Verde al seleccionar
    "selectforeground": 'white',
    "normalbackground": '#374151',      # Fondo gris oscuro para dias normales
    "normalforeground": 'white',
    "weekendbackground": '#4b5563',     # Fondo gris ligeramente distinto para fin de semana
    "weekendforeground": 'white',
    "othermonthforeground": '#9ca3af',
    "othermonthbackground": '#374151'
}

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("1400x850") 
app.title("Sistema Integral de Vóley")

ctk.CTkLabel(app, text="🏐 Sistema de Gestión - Vóley", font=("Arial", 24, "bold")).pack(pady=10)

tabview = ctk.CTkTabview(app)
tabview.pack(padx=10, pady=5, fill="both", expand=True) 

tab_0 = tabview.add("1. Periodos")
tab_1 = tabview.add("2. Alumnos")
tab_2 = tabview.add("3. Asistencia")
tab_3 = tabview.add("4. Tesorería")
tab_4 = tabview.add("5. Reportes")

# --- ESTILOS DE TABLA MEJORADOS (MÁS ALTURA Y FUENTE GRANDE) ---
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", 
                background="#2b2b2b", 
                foreground="white", 
                rowheight=38,           # Filas más altas
                fieldbackground="#2b2b2b", 
                borderwidth=0, 
                font=('Arial', 12))     # Fuente más grande en filas
style.map('Treeview', background=[('selected', '#1f538d')])
style.configure("Treeview.Heading", 
                font=('Arial', 13, 'bold'), # Fuente grande en encabezados
                background="#1f2937", 
                foreground="white", 
                padding=6)


# ==========================================
# PESTAÑA 0: PERIODOS
# ==========================================
frame_left = ctk.CTkFrame(tab_0, fg_color="transparent")
frame_left.pack(side="left", fill="y", padx=(20, 10), pady=20)

frame_right = ctk.CTkFrame(tab_0, fg_color="transparent")
frame_right.pack(side="right", fill="both", expand=True, padx=(10, 20), pady=20)

card_controles = ctk.CTkFrame(frame_left, fg_color="#1f2937", corner_radius=10)
card_controles.pack(fill="x", expand=False, ipadx=15, ipady=15)

ctk.CTkLabel(card_controles, text="📅 Gestor de Periodos", font=("Arial", 18, "bold"), text_color="#facc15").pack(pady=(10, 20))

ctk.CTkLabel(card_controles, text="1. Seleccionar o Crear:", font=("Arial", 13, "bold")).pack(anchor="w", padx=10)
# Aumento de height y font en combos y entries
combo_editar_per = ctk.CTkOptionMenu(card_controles, values=["-- Nuevo Periodo --"], width=260, height=35, font=("Arial", 14), dropdown_font=("Arial", 13))
combo_editar_per.pack(pady=(5, 15), padx=10)

ctk.CTkLabel(card_controles, text="2. Nombre del Periodo:", font=("Arial", 13, "bold")).pack(anchor="w", padx=10)
entry_nom_per = ctk.CTkEntry(card_controles, placeholder_text="Ej. Octubre", width=260, height=35, font=("Arial", 14))
entry_nom_per.pack(pady=(5, 15), padx=10)

ctk.CTkLabel(card_controles, text="3. Agregar Fecha:", font=("Arial", 13, "bold")).pack(anchor="w", padx=10)
frame_add_dia = ctk.CTkFrame(card_controles, fg_color="transparent")
frame_add_dia.pack(pady=(5, 10), padx=10, fill="x")

cal_per = DateEntry(frame_add_dia, **estilo_calendario)
cal_per.pack(side="left", padx=(0, 10), ipady=4) # ipady para igualar altura con el botón

def cargar_dias_en_tabla(periodo_nombre):
    for item in tabla_dias.get_children(): tabla_dias.delete(item)
    if periodo_nombre in datos_locales["periodos"]:
        dias = datos_locales["periodos"][periodo_nombre]
        try:
            dias.sort(key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            guardar_datos(datos_locales)
        except ValueError: pass
            
        for dia in dias: tabla_dias.insert("", "end", values=(dia,))
        lbl_cont_dias.configure(text=f"📋 Días Asignados (Total: {len(dias)})")
        if 'actualizar_deuda_prof' in globals(): actualizar_deuda_prof()

def al_seleccionar_periodo(choice):
    if choice == "-- Nuevo Periodo --":
        entry_nom_per.configure(state="normal")
        entry_nom_per.delete(0, "end")
        for item in tabla_dias.get_children(): tabla_dias.delete(item)
        lbl_cont_dias.configure(text="📋 Días Asignados (Total: 0)")
    else:
        entry_nom_per.configure(state="normal")
        entry_nom_per.delete(0, "end")
        entry_nom_per.insert(0, choice)
        entry_nom_per.configure(state="disabled") 
        cargar_dias_en_tabla(choice)

combo_editar_per.configure(command=al_seleccionar_periodo)

def agregar_dia_per():
    nom = entry_nom_per.get()
    if not nom: return
    dia = cal_per.get()
    if nom not in datos_locales["periodos"]: datos_locales["periodos"][nom] = []
    if dia not in datos_locales["periodos"][nom]:
        datos_locales["periodos"][nom].append(dia)
        guardar_datos(datos_locales)
        cargar_dias_en_tabla(nom)
        recargar_combos()

def eliminar_dia_per():
    nom = entry_nom_per.get()
    seleccion = tabla_dias.selection()
    if seleccion and nom in datos_locales["periodos"]:
        dia_sel = tabla_dias.item(seleccion[0])['values'][0]
        datos_locales["periodos"][nom].remove(dia_sel)
        guardar_datos(datos_locales)
        cargar_dias_en_tabla(nom)

ctk.CTkButton(frame_add_dia, text="+ Añadir", width=90, height=35, font=("Arial", 14, "bold"), fg_color="#059669", command=agregar_dia_per).pack(side="left")

card_tabla = ctk.CTkFrame(frame_right, fg_color="#1f2937", corner_radius=10)
card_tabla.pack(fill="both", expand=True, ipadx=10, ipady=10)

lbl_cont_dias = ctk.CTkLabel(card_tabla, text="📋 Días Asignados (Total: 0)", font=("Arial", 16, "bold"))
lbl_cont_dias.pack(pady=(15, 5), padx=20, anchor="w")

tabla_dias = ttk.Treeview(card_tabla, columns=("Día"), show="headings", height=15)
tabla_dias.heading("Día", text="Fechas de Clase Registradas")
tabla_dias.column("Día", anchor="center")
tabla_dias.pack(fill="both", expand=True, padx=20, pady=10)

ctk.CTkButton(card_tabla, text="🗑️ Borrar Fecha Seleccionada", fg_color="#991b1b", width=250, height=35, font=("Arial", 14, "bold"), command=eliminar_dia_per).pack(pady=(5, 10))


# ==========================================
# PESTAÑA 1: ALUMNOS
# ==========================================
frame_fa = ctk.CTkFrame(tab_1)
frame_fa.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(frame_fa, text="➕ Formulario de Alumno", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=15)

# Campos más amplios
entry_nino = ctk.CTkEntry(frame_fa, placeholder_text="Niño", width=200, height=35, font=("Arial", 13))
entry_nino.grid(row=0, column=1, padx=5)
entry_padre = ctk.CTkEntry(frame_fa, placeholder_text="Padre", width=200, height=35, font=("Arial", 13))
entry_padre.grid(row=0, column=2, padx=5)
combo_mod = ctk.CTkOptionMenu(frame_fa, values=["Mensual", "Libre"], width=130, height=35, font=("Arial", 13), dropdown_font=("Arial", 13))
combo_mod.grid(row=0, column=3, padx=5)
ctk.CTkLabel(frame_fa, text="Periodo (Si Mensual):", font=("Arial", 13)).grid(row=0, column=4, padx=(10,2))
combo_per_crear = ctk.CTkOptionMenu(frame_fa, values=["-"], width=150, height=35, font=("Arial", 13), dropdown_font=("Arial", 13))
combo_per_crear.grid(row=0, column=5, padx=5)

def registrar_alumno():
    global id_alumno_editando
    nino = entry_nino.get()
    padre = entry_padre.get()
    mod = combo_mod.get()
    per = combo_per_crear.get()
    
    if not nino or not padre: return
    accion = "actualizar" if id_alumno_editando else "guardar"

    if id_alumno_editando:
        viejo_m = next((m for m in datos_locales["mensuales"] if str(m[0]) == str(id_alumno_editando)), None)
        viejo_l = next((l for l in datos_locales["libres"] if str(l[0]) == str(id_alumno_editando)), None)
        datos_locales["mensuales"] = [m for m in datos_locales["mensuales"] if str(m[0]) != str(id_alumno_editando)]
        datos_locales["libres"] = [l for l in datos_locales["libres"] if str(l[0]) != str(id_alumno_editando)]
        
        if mod == "Mensual" and per in datos_locales["periodos"]:
            asis = viejo_m[4] if viejo_m else 0
            rest = viejo_m[5] if viejo_m else len(datos_locales["periodos"][per])
            pago = viejo_m[6] if viejo_m else "No"
            datos_locales["mensuales"].append([id_alumno_editando, nino, padre, per, asis, rest, pago])
        else:
            asis = viejo_l[3] if viejo_l else 0
            pagadas = viejo_l[4] if viejo_l else 0
            est = "🟢 Al Día" if pagadas >= asis else "🔴 Debe"
            datos_locales["libres"].append([id_alumno_editando, nino, padre, asis, pagadas, est])
        id_alumno_editando = None
        btn_reg_alumno.configure(text="Guardar Alumno")
    else:
        if mod == "Mensual" and per in datos_locales["periodos"]:
            datos_locales["mensuales"].append([generar_id(), nino, padre, per, 0, len(datos_locales["periodos"][per]), "No"])
        else:
            datos_locales["libres"].append([generar_id(), nino, padre, 0, 0, "🔴 Debe"])
            
    guardar_datos(datos_locales)
    entry_nino.delete(0, "end")
    entry_padre.delete(0, "end")
    recargar_tablas_alumnos()
    recargar_combos()

btn_reg_alumno = ctk.CTkButton(frame_fa, text="Guardar Alumno", fg_color="#2563eb", height=35, font=("Arial", 13, "bold"), command=registrar_alumno)
btn_reg_alumno.grid(row=0, column=6, padx=15)

marco_tablas = ctk.CTkFrame(tab_1, fg_color="transparent")
marco_tablas.pack(fill="both", expand=True, padx=5, pady=5)

lbl_cont_m = ctk.CTkLabel(marco_tablas, text="📋 Mensuales (Total: 0)", font=("Arial", 14, "bold"))
lbl_cont_m.pack(anchor="w", pady=(5,0))
columnas_m = ("ID", "Niño", "Padre", "Periodo", "Asistidas", "Restantes", "Pagó Mes")
tabla_m = ttk.Treeview(marco_tablas, columns=columnas_m, show="headings", height=5)
for col in columnas_m: tabla_m.heading(col, text=col)
tabla_m.column("ID", width=0, stretch=False)
for col, w in zip(columnas_m[1:], [180, 180, 120, 100, 100, 100]): tabla_m.column(col, width=w, anchor="center")
tabla_m.pack(fill="both", expand=True, pady=(0, 10))
tabla_m.tag_configure("pago_si", background="#1e3a8a")
tabla_m.tag_configure("pago_no", background="#7f1d1d")

lbl_cont_l = ctk.CTkLabel(marco_tablas, text="📋 Libres (Total: 0)", font=("Arial", 14, "bold"))
lbl_cont_l.pack(anchor="w")
columnas_l = ("ID", "Niño", "Padre", "Asistidas", "Clases Pagadas", "Estado")
tabla_l = ttk.Treeview(marco_tablas, columns=columnas_l, show="headings", height=5)
for col in columnas_l: tabla_l.heading(col, text=col)
tabla_l.column("ID", width=0, stretch=False)
for col, w in zip(columnas_l[1:], [180, 180, 100, 120, 150]): tabla_l.column(col, width=w, anchor="center")
tabla_l.pack(fill="both", expand=True, pady=(0, 5))
tabla_l.tag_configure("aldia", background="#065f46")
tabla_l.tag_configure("debe", background="#991b1b")

def recargar_tablas_alumnos():
    for i in tabla_m.get_children(): tabla_m.delete(i)
    for m in datos_locales["mensuales"]:
        tag = "pago_si" if m[6] == "Sí" else "pago_no"
        tabla_m.insert("", "end", values=m, tags=(tag,))
    lbl_cont_m.configure(text=f"📋 Mensuales (Total: {len(datos_locales['mensuales'])})")
        
    for i in tabla_l.get_children(): tabla_l.delete(i)
    for l in datos_locales["libres"]:
        l[5] = "🟢 Al Día" if l[4] >= l[3] else "🔴 Debe"
        tag = "aldia" if "Al Día" in l[5] else "debe"
        tabla_l.insert("", "end", values=l, tags=(tag,))
    lbl_cont_l.configure(text=f"📋 Libres (Total: {len(datos_locales['libres'])})")

frame_edit_alum = ctk.CTkFrame(tab_1, fg_color="transparent")
frame_edit_alum.pack(fill="x", padx=10, pady=5)

def cargar_edicion(tipo):
    global id_alumno_editando
    tabla = tabla_m if tipo == "m" else tabla_l
    sel = tabla.selection()
    if not sel: return
    valores = tabla.item(sel[0])['values']
    id_alumno_editando = str(valores[0])
    entry_nino.delete(0, "end")
    entry_nino.insert(0, valores[1])
    entry_padre.delete(0, "end")
    entry_padre.insert(0, valores[2])
    if tipo == "m":
        combo_mod.set("Mensual")
        combo_per_crear.set(valores[3])
    else: combo_mod.set("Libre")
    btn_reg_alumno.configure(text="Actualizar Alumno")

def eliminar_alumno(tipo):
    tabla = tabla_m if tipo == "m" else tabla_l
    lista = "mensuales" if tipo == "m" else "libres"
    sel = tabla.selection()
    if sel:
        id_sel = tabla.item(sel[0])['values'][0]
        datos_locales[lista] = [a for a in datos_locales[lista] if str(a[0]) != str(id_sel)]
        guardar_datos(datos_locales)
        recargar_tablas_alumnos()
        recargar_combos()

ctk.CTkButton(frame_edit_alum, text="✏️ Editar Mensual", fg_color="#d97706", height=35, font=("Arial", 13, "bold"), command=lambda: cargar_edicion("m")).pack(side="left", padx=5)
ctk.CTkButton(frame_edit_alum, text="🗑️ Eliminar Mensual", fg_color="#991b1b", height=35, font=("Arial", 13, "bold"), command=lambda: eliminar_alumno("m")).pack(side="left", padx=(5, 30))
ctk.CTkButton(frame_edit_alum, text="✏️ Editar Libre", fg_color="#d97706", height=35, font=("Arial", 13, "bold"), command=lambda: cargar_edicion("l")).pack(side="left", padx=5)
ctk.CTkButton(frame_edit_alum, text="🗑️ Eliminar Libre", fg_color="#991b1b", height=35, font=("Arial", 13, "bold"), command=lambda: eliminar_alumno("l")).pack(side="left", padx=5)


# ==========================================
# PESTAÑA 2: ASISTENCIA
# ==========================================
frame_asis = ctk.CTkFrame(tab_2, fg_color="#374151")
frame_asis.pack(fill="x", padx=10, pady=10)
ctk.CTkLabel(frame_asis, text="✅ Registro de Asistencia por Día", font=("Arial", 18, "bold"), text_color="#6ee7b7").pack(pady=10)

frame_filtros = ctk.CTkFrame(frame_asis, fg_color="transparent")
frame_filtros.pack(pady=5)

ctk.CTkLabel(frame_filtros, text="1. Periodo:", font=("Arial", 14)).grid(row=0, column=0, padx=5)
combo_per_asis = ctk.CTkOptionMenu(frame_filtros, values=["-"], width=180, height=35, font=("Arial", 14), dropdown_font=("Arial", 13))
combo_per_asis.grid(row=0, column=1, padx=5)

ctk.CTkLabel(frame_filtros, text="2. Día de clase:", font=("Arial", 14)).grid(row=0, column=2, padx=5)
combo_dia_asis = ctk.CTkOptionMenu(frame_filtros, values=["-"], width=180, height=35, font=("Arial", 14), dropdown_font=("Arial", 13))
combo_dia_asis.grid(row=0, column=3, padx=5)

ctk.CTkLabel(frame_filtros, text="3. Alumno:", font=("Arial", 14)).grid(row=0, column=4, padx=5)
combo_alum_asis = ctk.CTkOptionMenu(frame_filtros, values=["-"], width=180, height=35, font=("Arial", 14), dropdown_font=("Arial", 13))
combo_alum_asis.grid(row=0, column=5, padx=5)

def actualizar_dias_asis(choice):
    if choice in datos_locales["periodos"] and datos_locales["periodos"][choice]:
        combo_dia_asis.configure(values=datos_locales["periodos"][choice])
        combo_dia_asis.set(datos_locales["periodos"][choice][0])
    else:
        combo_dia_asis.configure(values=["-"])
        combo_dia_asis.set("-")

combo_per_asis.configure(command=actualizar_dias_asis)

def marcar_asistencia():
    per = combo_per_asis.get()
    dia = combo_dia_asis.get()
    alum = combo_alum_asis.get()
    
    if dia == "-" or alum == "-": return
    for a in datos_locales["asistencias_detalle"]:
        if a[1] == alum and a[2] == per and a[3] == dia:
            messagebox.showwarning("Aviso", "Este niño ya tiene asistencia marcada en esta fecha.")
            return

    modalidad = ""
    for m in datos_locales["mensuales"]:
        if m[1] == alum:
            m[4] += 1
            m[5] -= 1
            modalidad = "Mensual"
            break
    if not modalidad:
        for l in datos_locales["libres"]:
            if l[1] == alum:
                l[3] += 1
                modalidad = "Libre"
                break
    if modalidad:
        datos_locales["asistencias_detalle"].append([generar_id(), alum, per, dia, modalidad])
        guardar_datos(datos_locales)
        recargar_tablas_alumnos()
        cargar_tabla_asistencias()

ctk.CTkButton(frame_asis, text="✅ Marcar Asistencia", fg_color="#059669", height=45, font=("Arial", 15, "bold"), command=marcar_asistencia).pack(pady=15)

lbl_cont_asis = ctk.CTkLabel(tab_2, text="📋 Historial (Total: 0)", font=("Arial", 14, "bold"))
lbl_cont_asis.pack(anchor="w", padx=10)
columnas_asis = ("ID", "Niño", "Periodo", "Día", "Modalidad")
tabla_asis = ttk.Treeview(tab_2, columns=columnas_asis, show="headings", height=10)
for col in columnas_asis: tabla_asis.heading(col, text=col)
tabla_asis.column("ID", width=0, stretch=False)
for col, w in zip(columnas_asis[1:], [250, 180, 180, 180]): tabla_asis.column(col, width=w, anchor="center")
tabla_asis.pack(fill="both", expand=True, padx=10, pady=5)

def cargar_tabla_asistencias():
    for i in tabla_asis.get_children(): tabla_asis.delete(i)
    for a in reversed(datos_locales["asistencias_detalle"]): tabla_asis.insert("", "end", values=a)
    lbl_cont_asis.configure(text=f"📋 Historial (Total: {len(datos_locales['asistencias_detalle'])})")

def borrar_asistencia():
    seleccion = tabla_asis.selection()
    if seleccion:
        id_sel = tabla_asis.item(seleccion[0])['values'][0]
        alum = tabla_asis.item(seleccion[0])['values'][1]
        for m in datos_locales["mensuales"]:
            if m[1] == alum:
                m[4] -= 1
                m[5] += 1
        for l in datos_locales["libres"]:
            if l[1] == alum: l[3] -= 1
        datos_locales["asistencias_detalle"] = [a for a in datos_locales["asistencias_detalle"] if str(a[0]) != str(id_sel)]
        guardar_datos(datos_locales)
        recargar_tablas_alumnos()
        cargar_tabla_asistencias()

ctk.CTkButton(tab_2, text="🗑️ Deshacer Asistencia", fg_color="#991b1b", height=35, font=("Arial", 13, "bold"), command=borrar_asistencia).pack(pady=5)


# ==========================================
# PESTAÑA 3: TESORERÍA (PAGOS)
# ==========================================
marco_saldos = ctk.CTkFrame(tab_3, fg_color="#1f2937")
marco_saldos.pack(fill="x", padx=10, pady=5)
lbl_total = ctk.CTkLabel(marco_saldos, text="📊 TOTAL EN CUENTA: S/ 0.00", font=("Arial", 18, "bold"), text_color="#38bdf8")
lbl_total.pack(side="right", padx=20, pady=10)
entry_fondo = ctk.CTkEntry(marco_saldos, width=100, height=35, font=("Arial", 14), placeholder_text="S/ Inicial")
entry_fondo.pack(side="left", padx=10, pady=10)
def fijar_fondo():
    if entry_fondo.get():
        datos_locales["fondo_previo"] = entry_fondo.get()
        guardar_datos(datos_locales)
        recargar_tabla_t()
ctk.CTkButton(marco_saldos, text="Fijar Inicial", width=80, height=35, font=("Arial", 13, "bold"), fg_color="#d97706", command=fijar_fondo).pack(side="left", padx=5)

frame_ft = ctk.CTkFrame(tab_3)
frame_ft.pack(fill="x", padx=10, pady=5)
ctk.CTkLabel(frame_ft, text="📥 Nuevo Pago/Ingreso:", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=5, pady=10)

combo_alum_t = ctk.CTkOptionMenu(frame_ft, values=["-"], width=180, height=35, font=("Arial", 13), dropdown_font=("Arial", 13))
combo_alum_t.grid(row=0, column=1, padx=5)

cal_pago = DateEntry(frame_ft, **estilo_calendario)
cal_pago.grid(row=0, column=2, padx=5, ipady=4)

entry_monto_t = ctk.CTkEntry(frame_ft, placeholder_text="Monto", width=100, height=35, font=("Arial", 14))
entry_monto_t.grid(row=0, column=3, padx=5)

cal_tras = DateEntry(frame_ft, **estilo_calendario)
cal_tras.grid(row=0, column=4, padx=5, ipady=4)

ctk.CTkLabel(frame_ft, text="Enlazar a (Elige uno):", font=("Arial", 13)).grid(row=1, column=0, pady=5)
combo_per_t = ctk.CTkOptionMenu(frame_ft, values=["-"], width=180, height=35, font=("Arial", 13), dropdown_font=("Arial", 13))
combo_per_t.grid(row=1, column=1, padx=5)
entry_clases_t = ctk.CTkEntry(frame_ft, placeholder_text="+ N° Clases (Si Libre)", width=180, height=35, font=("Arial", 14))
entry_clases_t.grid(row=1, column=2, columnspan=2, padx=5, sticky="w")

def registrar_mov():
    alum = combo_alum_t.get()
    monto = entry_monto_t.get()
    per = combo_per_t.get()
    clases = entry_clases_t.get()
    
    if alum and monto:
        info = f"Mes: {per}" if not clases else f"+{clases} Clases"
        datos_locales["movimientos"].append([generar_id(), "Ingreso", alum, cal_pago.get(), monto, cal_tras.get(), info])
        if clases.isdigit(): 
            for l in datos_locales["libres"]:
                if l[1] == alum: l[4] += int(clases)
        else: 
            for m in datos_locales["mensuales"]:
                if m[1] == alum and m[3] == per: m[6] = "Sí"
        guardar_datos(datos_locales)
        recargar_tablas_alumnos()
        recargar_tabla_t()
        entry_monto_t.delete(0, "end")
        entry_clases_t.delete(0, "end")

ctk.CTkButton(frame_ft, text="Guardar Ingreso", fg_color="#16a34a", height=35, font=("Arial", 13, "bold"), command=registrar_mov).grid(row=0, column=5, rowspan=2, padx=15)

frame_prof = ctk.CTkFrame(tab_3, fg_color="#451a03")
frame_prof.pack(fill="x", padx=10, pady=5)

lbl_deuda_prof = ctk.CTkLabel(frame_prof, text="Calculando deuda...", font=("Arial", 14, "bold"), text_color="#fde047")
lbl_deuda_prof.pack(side="left", padx=15, pady=10)

def actualizar_deuda_prof():
    clases, total, saldo = calcular_deuda_profesor()
    lbl_deuda_prof.configure(text=f"📚 Clases dictadas (a hoy): {clases} | 💰 Generado (S/80xClase): S/{total} | ❗ Saldo a Pagar: S/{saldo:.2f}")

cal_prof = DateEntry(frame_prof, **estilo_calendario)
cal_prof.pack(side="left", padx=10, pady=10, ipady=4)
entry_monto_prof = ctk.CTkEntry(frame_prof, placeholder_text="Monto a Pagar", width=120, height=35, font=("Arial", 14))
entry_monto_prof.pack(side="left", padx=5)

def registrar_prof():
    if entry_monto_prof.get():
        datos_locales["movimientos"].append([generar_id(), "Egreso", "Pago Profesor", cal_prof.get(), entry_monto_prof.get(), "-", "-"])
        guardar_datos(datos_locales)
        recargar_tabla_t()
        entry_monto_prof.delete(0, "end")
        
ctk.CTkButton(frame_prof, text="Registrar Pago a Profesor", fg_color="#ea580c", height=35, font=("Arial", 13, "bold"), command=registrar_prof).pack(side="left", padx=10)

lbl_cont_mov = ctk.CTkLabel(tab_3, text="📋 Movimientos de Tesorería (Total: 0)", font=("Arial", 14, "bold"))
lbl_cont_mov.pack(anchor="w", padx=10, pady=(10, 0))
columnas_t = ("ID", "Tipo", "Detalle", "Fecha Op.", "Monto", "F. Traslado", "Info Extra")
tabla_t = ttk.Treeview(tab_3, columns=columnas_t, show="headings", height=8)
for col in columnas_t: tabla_t.heading(col, text=col)
tabla_t.column("ID", width=0, stretch=False)
for col, w in zip(columnas_t[1:], [100, 180, 120, 100, 120, 180]): tabla_t.column(col, width=w, anchor="center")
tabla_t.pack(pady=5, padx=10, fill="both", expand=True)
tabla_t.tag_configure("in", background="#065f46")
tabla_t.tag_configure("out", background="#7f1d1d")

def recargar_tabla_t():
    for item in tabla_t.get_children(): tabla_t.delete(item)
    total = float(datos_locales["fondo_previo"]) if datos_locales["fondo_previo"] else 0.0
    lista = []
    for mov in datos_locales["movimientos"]:
        try: f = datetime.strptime(mov[3], "%d/%m/%Y")
        except: f = datetime.min
        lista.append({"f": f, "d": mov})
        try:
            m = float(mov[4])
            if mov[1] == "Ingreso": total += m
            elif mov[1] == "Egreso": total -= m
        except: pass
    lista.sort(key=lambda x: x["f"], reverse=True)
    for item in lista:
        tag = "in" if item["d"][1] == "Ingreso" else "out"
        tabla_t.insert("", "end", values=item["d"], tags=(tag,))
    lbl_total.configure(text=f"📊 TOTAL EN CUENTA: S/ {total:.2f}")
    lbl_cont_mov.configure(text=f"📋 Movimientos (Total: {len(datos_locales['movimientos'])})")
    actualizar_deuda_prof()

def eliminar_mov():
    seleccion = tabla_t.selection()
    if seleccion:
        id_sel = tabla_t.item(seleccion[0])['values'][0]
        datos_locales["movimientos"] = [m for m in datos_locales["movimientos"] if str(m[0]) != str(id_sel)]
        guardar_datos(datos_locales)
        recargar_tabla_t()

ctk.CTkButton(tab_3, text="🗑️ Eliminar Movimiento Sel.", fg_color="#991b1b", height=35, font=("Arial", 13, "bold"), command=eliminar_mov).pack(pady=5)


# ==========================================
# PESTAÑA 5: REPORTES
# ==========================================
frame_rep_top = ctk.CTkFrame(tab_4, fg_color="transparent")
frame_rep_top.pack(fill="x", padx=10, pady=10)

ctk.CTkLabel(frame_rep_top, text="📊 Reporte Visual Detallado", font=("Arial", 16, "bold")).pack(side="left", padx=10)
combo_per_rep = ctk.CTkOptionMenu(frame_rep_top, values=["-"], width=180, height=35, font=("Arial", 14), dropdown_font=("Arial", 13))
combo_per_rep.pack(side="left", padx=10)

ctk.CTkButton(frame_rep_top, text="Generar Cuadro", fg_color="#2563eb", height=35, font=("Arial", 13, "bold"), command=lambda: generar_reporte()).pack(side="left", padx=10)

def capturar_pantalla():
    per = combo_per_rep.get()
    if per == "-": return
    x = frame_rep_contenedor.winfo_rootx()
    y = frame_rep_contenedor.winfo_rooty()
    w = frame_rep_contenedor.winfo_width()
    h = frame_rep_contenedor.winfo_height()
    try:
        img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
        nombre_archivo = f"Reporte_Voley_{per}.png"
        img.save(nombre_archivo)
        messagebox.showinfo("Éxito", f"¡Captura guardada!\n\nArchivo: {nombre_archivo}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al capturar: {e}")

ctk.CTkButton(frame_rep_top, text="📷 Capturar Área del Reporte", fg_color="#d97706", height=35, font=("Arial", 13, "bold"), command=capturar_pantalla).pack(side="left", padx=10)

frame_rep_contenedor = ctk.CTkFrame(tab_4, fg_color="#1f2937")
frame_rep_contenedor.pack(fill="both", expand=True, padx=10, pady=5)

tabla_rep_scroll = ctk.CTkScrollableFrame(frame_rep_contenedor, fg_color="transparent")
tabla_rep_scroll.pack(fill="both", expand=True, padx=5, pady=5)

frame_totales_rep = ctk.CTkFrame(frame_rep_contenedor, fg_color="#111827", height=50)
frame_totales_rep.pack(fill="x", side="bottom")

lbl_recaudado_rep = ctk.CTkLabel(frame_totales_rep, text="💰 Recaudación del Periodo: S/ 0.00", font=("Arial", 14, "bold"), text_color="#10b981")
lbl_recaudado_rep.pack(side="left", padx=15, pady=12)

lbl_prof_rep = ctk.CTkLabel(frame_totales_rep, text="👨‍🏫 Profesor: Calculando...", font=("Arial", 14, "bold"), text_color="#facc15")
lbl_prof_rep.pack(side="right", padx=15, pady=12)

def generar_reporte():
    per = combo_per_rep.get()
    if per == "-" or per not in datos_locales["periodos"]: return
    hoy = datetime.now().date()

    for widget in tabla_rep_scroll.winfo_children():
        widget.destroy()

    dias_periodo = datos_locales["periodos"][per]
    
    columnas = ["Alumno", "Modalidad", "Pago/Saldo"] + dias_periodo
    for col_idx, col_name in enumerate(columnas):
        w = 150 if col_name == "Alumno" else (90 if col_name in ["Modalidad", "Pago/Saldo"] else 80)
        lbl = ctk.CTkLabel(tabla_rep_scroll, text=col_name, width=w, height=35, fg_color="#333333", font=("Arial", 12, "bold"))
        lbl.grid(row=0, column=col_idx, padx=1, pady=1)
        
    asis_per = [a for a in datos_locales["asistencias_detalle"] if a[2] == per]
    fila_actual = 1
    
    alumnos_mensuales = [m for m in datos_locales["mensuales"] if m[3] == per]
    for m in alumnos_mensuales:
        pago = m[6]
        bg_nom = "#1e3a8a" if pago == "Sí" else "#991b1b" 
        
        ctk.CTkLabel(tabla_rep_scroll, text=m[1], width=150, height=35, font=("Arial", 12), fg_color=bg_nom).grid(row=fila_actual, column=0, padx=1, pady=1)
        ctk.CTkLabel(tabla_rep_scroll, text="Mensual", width=90, height=35, font=("Arial", 12), fg_color=bg_nom).grid(row=fila_actual, column=1, padx=1, pady=1)
        ctk.CTkLabel(tabla_rep_scroll, text=f"Pagó: {pago}", width=90, height=35, font=("Arial", 12), fg_color=bg_nom).grid(row=fila_actual, column=2, padx=1, pady=1)
        
        for c_idx, dia in enumerate(dias_periodo, start=3):
            try: fecha_clase = datetime.strptime(dia, "%d/%m/%Y").date()
            except ValueError: fecha_clase = hoy
            
            asistio = any(a[1] == m[1] and a[3] == dia for a in asis_per)
            
            if fecha_clase > hoy:
                texto_celda = ""
                bg_celda = bg_nom 
            else:
                if asistio:
                    texto_celda = "Asistió"
                    bg_celda = "#059669" 
                else:
                    texto_celda = "Faltó"
                    bg_celda = "#ea580c" if pago == "Sí" else bg_nom 
            
            ctk.CTkLabel(tabla_rep_scroll, text=texto_celda, width=80, height=35, font=("Arial", 12, "bold"), fg_color=bg_celda).grid(row=fila_actual, column=c_idx, padx=1, pady=1)
            
        fila_actual += 1
        
    nombres_libres_asis = set([a[1] for a in asis_per if a[4] == "Libre"])
    alumnos_libres = [l for l in datos_locales["libres"] if l[1] in nombres_libres_asis]
    
    for l in alumnos_libres:
        estado = l[5]
        bg_nom = "#065f46" if "Al Día" in estado else "#991b1b"
        
        ctk.CTkLabel(tabla_rep_scroll, text=l[1], width=150, height=35, font=("Arial", 12), fg_color=bg_nom).grid(row=fila_actual, column=0, padx=1, pady=1)
        ctk.CTkLabel(tabla_rep_scroll, text="Libre", width=90, height=35, font=("Arial", 12), fg_color=bg_nom).grid(row=fila_actual, column=1, padx=1, pady=1)
        ctk.CTkLabel(tabla_rep_scroll, text=f"Pagadas: {l[4]}", width=90, height=35, font=("Arial", 12), fg_color=bg_nom).grid(row=fila_actual, column=2, padx=1, pady=1)
        
        for c_idx, dia in enumerate(dias_periodo, start=3):
            try: fecha_clase = datetime.strptime(dia, "%d/%m/%Y").date()
            except ValueError: fecha_clase = hoy
            
            asistio = any(a[1] == l[1] and a[3] == dia for a in asis_per)
            
            if fecha_clase > hoy:
                texto_celda = ""
                bg_celda = bg_nom
            else:
                if asistio:
                    texto_celda = "Asistió"
                    bg_celda = "#059669" 
                else:
                    texto_celda = "" 
                    bg_celda = bg_nom
            
            ctk.CTkLabel(tabla_rep_scroll, text=texto_celda, width=80, height=35, font=("Arial", 12, "bold"), fg_color=bg_celda).grid(row=fila_actual, column=c_idx, padx=1, pady=1)
            
        fila_actual += 1

    total_periodo = 0.0
    for mov in datos_locales["movimientos"]:
        if mov[1] == "Ingreso" and f"Mes: {per}" in mov[6]:
            try: total_periodo += float(mov[4])
            except: pass
            
    clases, _, saldo = calcular_deuda_profesor()
    
    lbl_recaudado_rep.configure(text=f"💰 Recaudación del Periodo '{per}': S/ {total_periodo:.2f}")
    lbl_prof_rep.configure(text=f"👨‍‍🏫 Profesor | Clases dadas a hoy: {clases} | Saldo Pendiente General: S/ {saldo:.2f}")

recargar_combos()
recargar_tablas_alumnos()
cargar_tabla_asistencias()
recargar_tabla_t()
actualizar_deuda_prof()

app.mainloop()