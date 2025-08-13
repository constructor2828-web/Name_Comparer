import streamlit as st
import re
import fitz  # PyMuPDF
import unicodedata

st.set_page_config(page_title="Comparador de Nombres", page_icon="🔍")

st.title("🔍 Comparador de Nombres en Listados PDF")

# ------------------------------
# Función para normalizar texto (quitar tildes y pasar a mayúsculas)
# ------------------------------
def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.upper())
        if unicodedata.category(c) != 'Mn'
    ).strip()

# ------------------------------
# Función para leer el primer archivo y unir apellidos + nombre
# ------------------------------
def leer_archivo1(archivo):
    extension = archivo.name.split(".")[-1].lower()
    if extension == "txt":
        lineas = archivo.read().decode("utf-8", errors="ignore").splitlines()
    elif extension == "pdf":
        texto = ""
        with fitz.open(stream=archivo.read(), filetype="pdf") as pdf:
            for pagina in pdf:
                texto += pagina.get_text()
        lineas = texto.splitlines()
    else:
        return []

    # Quitar líneas vacías y espacios
    lineas = [l.strip() for l in lineas if l.strip()]

    # Quitar cabecera si está
    if "APELLIDOS" in lineas[0].upper():
        lineas = lineas[1:]

    nombres = []
    i = 0
    while i < len(lineas) - 2:
        apellidos = lineas[i].strip()
        nombre = lineas[i+1].strip()

        # Unir apellidos y nombre
        nombres.append(normalizar(f"{apellidos} {nombre}"))

        # Saltar situación administrativa
        i += 3

    return nombres

# ------------------------------
# Función para leer el segundo archivo y extraer nombres
# ------------------------------
def leer_archivo2(archivo):
    texto = ""
    with fitz.open(stream=archivo.read(), filetype="pdf") as pdf:
        for pagina in pdf:
            texto += pagina.get_text()

    lineas = texto.splitlines()
    nombres_pdf = []
    captura = False
    for linea in lineas:
        if "APELLIDOS Y NOMBRE" in linea.upper():
            captura = True
            continue
        if captura:
            # Cortar si se llega a una línea que parece DNI o si es vacía
            if re.match(r"\d{8}", linea) or linea.strip() == "":
                captura = False
            else:
                nombres_pdf.append(normalizar(linea))
    return nombres_pdf

# ------------------------------
# Subida de archivos
# ------------------------------
archivo1 = st.file_uploader("📄 Sube el primer documento (nombres a buscar)", type=["txt", "pdf"])
archivo2 = st.file_uploader("📄 Sube el segundo documento (listado PDF)", type=["pdf"])

if archivo1 and archivo2:
    lista1 = leer_archivo1(archivo1)
    lista2 = leer_archivo2(archivo2)

    # Comparación
    presentes = sorted([n for n in lista1 if n in lista2])
    ausentes = sorted([n for n in lista1 if n not in lista2])

    # Mostrar resultados
    st.subheader("✅ Nombres encontrados")
    st.write(presentes)

    st.subheader("❌ Nombres NO encontrados")
    st.write(ausentes)

    # Botón para descargar
    resultado = (
        "Nombres encontrados:\n" + "\n".join(presentes) +
        "\n\nNombres NO encontrados:\n" + "\n".join(ausentes)
    )
    st.download_button(
        "💾 Descargar resultados",
        data=resultado,
        file_name="resultado_comparacion.txt",
        mime="text/plain"
    )
