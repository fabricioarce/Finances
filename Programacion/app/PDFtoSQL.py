import pymupdf
import re
import sqlite3
from datetime import datetime


title = "Detalle de compras del período"
ignore = ["Detalle de compras del período", "Fecha de transacción", "Concepto / Descripción", "Transacciones en", "US dólares", "Transacciones en", "colones", "EDWIN DAVID ARCE MATA", "***********42008"]
headers = ["Fecha de transacción", "Concepto / Descripción", "Transacciones en colones", "Transacciones en US dólares"]


pathPDF = "./data/x.pdf"
doc = pymupdf.Document(pathPDF)
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

def pays(doc): 
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

    mes = obtener_mes(data)
    # Insertar cada fila
    if mes and comprobar_mes(mes):
        print(f"⚠️ Ya existen registros para el mes {mes}. No se insertaron datos.")
    else:
        latoiso(data)
        cursor.executemany("""
        INSERT INTO transacciones (fecha, descripcion, monto_colones, monto_dolares)
        VALUES (?, ?, ?, ?)
        """, data)

        # Guardar cambios y cerrar conexión
        conn.commit()
    conn.close()

    print("✅ Datos insertados correctamente.")

def obtener_mes(data):
    match = re.search(r"\d{2}/(\d{2})/\d{4}", data[0][0])
    if match:
        print(match.group(1))
        return match.group(1)
    else: 
        return None

def comprobar_mes(mes):
    conn = sqlite3.connect("pagos.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fecha FROM transacciones")
    fechas = cursor.fetchall()
    for f in fechas:
        if f[0][5:7] == mes:
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

if __name__ == "__main__":
    crear()
    pays(doc)
    toSQL(data)
