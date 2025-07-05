import pymupdf
import re
import sqlite3
from datetime import datetime
import streamlit as st
import plotly.express as px


title = "Detalle de compras del período"
ignore = ["Detalle de compras del período", "Fecha de transacción", "Concepto / Descripción", "Transacciones en", "US dólares", "Transacciones en", "colones", "EDWIN DAVID ARCE MATA", "***********42008"]
headers = ["Fecha de transacción", "Concepto / Descripción", "Transacciones en colones", "Transacciones en US dólares"]

flist = []
data = []
lcategorias = ["Luz", "TV y teléfonos", "Municipalidad", "Diario", "Combustible", "Periódico", "San Antonio", "Restaurantes", "U Pablo", "Coope cesantia", "Gimnasio Poliza", "Gastos médicos", "Mejoras Casa", "Aguinaldo", "Escolar", "Para gastar", "Intereses", "Poliza incendio", "Inversion ahorro plazo"]

regex_fecha = r"\d{2}/\d{2}/\d{4}$"
new_regex_fecha = r"\d{4}-\d{2}-\d{2}$"

def latoiso(data):
    for i in range(len(data)):
        fecha_original = data[i][0]  # día/mes/año
        data[i][0] = datetime.strptime(fecha_original, "%d/%m/%Y").strftime("%Y-%m-%d")

def limpiar_pago(pago):
    # Usar "" si el campo es None, luego strip
    fecha = (pago[0] or "").strip()
    descripcion = (pago[1] or "").strip()

    colones_str = (pago[3] or "").strip()
    dolares_str = (pago[5] or "").strip()

    # Quitar comas si existen
    colones_str = colones_str.replace(",", "")
    dolares_str = dolares_str.replace(",", "")

    # Convertir a float si hay número, si no dejar como 0
    if colones_str != '':
        colones = float(colones_str)
    else:
        colones = 0

    if dolares_str != '':
        dolares = float(dolares_str)
    else:
        dolares = 0

    # # Convertir a float si hay número, si no dejar como 0
    # colones = float(colones_str.replace(",", "")) if colones_str else 0
    # dolares = float(dolares_str.replace(",", "")) if dolares_str else 0

    return [fecha, descripcion, colones, dolares]

def pays(doc, data): 
    for page in doc:
        lines = page.get_text().split('\n')
        
        for line in lines:
            if line == title:
                table = page.find_tables()
                table = table[0]
                table_data = table.extract()
                # print(table_data)
                for pago in table_data:
                    if re.match(regex_fecha, pago[0]):
                        data.append(limpiar_pago(pago))

def toSQL(data):

    if not data:
        print("No hay datos para insertar")
        return

    # Crear conexión a la base de datos (archivo local)
    conn = sqlite3.connect("pagos.db")
    cursor = conn.cursor()

    mes, year = obtener_mes_y_year(data)
    # Insertar cada fila
    if mes and comprobar_mes(mes, year):
        print(f"⚠️ Ya existen registros para el mes {mes}. No se insertaron datos.")
    else:
        latoiso(data)
        cursor.executemany("""
        INSERT INTO transacciones (fecha, descripcion, monto_colones, monto_dolares)
        VALUES (?, ?, ?, ?)
        """, data)

        # Guardar cambios y cerrar conexión
        print("✅ Datos insertados correctamente.")
        conn.commit()
    conn.close()

def obtener_mes_y_year(data):
    fecha = data[0][0] if data and data[0] else ""
    match = re.search(r"\d{2}/(\d{2})/(\d{4})", fecha)

    if not match:
        print(f"⚠️ No se pudo extraer la fecha de: {fecha}")
        return None, None

    else: 
        mes = match.group(1)
        year = match.group(2)
        print(f"📅 Fecha detectada → Mes: {mes}, Año: {year}")
        return mes, year

def comprobar_mes(mes, year):
    conn = sqlite3.connect("pagos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fecha FROM transacciones")
    fechas = cursor.fetchall()
    for f in fechas:
        if f[0][5:7] == mes and f[0][0:4] == year:
            print(f)
            return True
    return False

    # cerrar conexión
    conn.close()

def crear():
        # Crear conexión a la base de datos (archivo local)
    conn = sqlite3.connect("pagos.db")
    cursor = conn.cursor()

    # Crear tabla (si no existe)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY,
        nombre TEXT UNIQUE NOT NULL
    )
    """)
    for cat in lcategorias:
        cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (cat,))

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comercios (
        id INTEGER PRIMARY KEY,
        nombre TEXT UNIQUE NOT NULL,
        categoria_id INTEGER,
        FOREIGN KEY(categoria_id) REFERENCES categorias(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacciones (
        fecha TEXT,
        descripcion TEXT,
        monto_colones REAL,
        monto_dolares REAL,
        categoria_id INTEGER,
        FOREIGN KEY(categoria_id) REFERENCES categorias(id)
    )
    """)



    # ✅ Guardar los cambios
    conn.commit()
    # ✅ Cerrar la conexión
    conn.close()

def clasificar():
    conn = sqlite3.connect("pagos.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, descripcion FROM transacciones
    WHERE categoria_id IS NULL
    """)
    transacciones_sin_categoria = cursor.fetchall()

    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()

def datos(file):
    crear()
    doc = pymupdf.Document(stream=file, filetype="pdf")
    pays(doc, data)
    toSQL(data)

## mostrar web
st.set_page_config(page_title="Finace", page_icon="💰", layout="wide")

def main():
    st.title("Test 1")

    uploaded_file = st.file_uploader("Upload your transaction PDF file",type=["pdf", "csv"])

    if uploaded_file is not None:
        file = uploaded_file.read()
        st.success("Archivo subido correctamente.")
        
        datos(file)

main()