import re
from PyPDF2 import PdfReader

# Lista de campos que devolverá el backend
CAMPOS = [
    "titulo", "url", "fuente", "anio", "paises", "issn", "tipoPublicacion",
    "nombrePublicacion", "autores", "filiaciones", "quartil", "indiceH",
    "numeroCitas", "resumen", "palabrasClave", "introduccion", "metodologia",
    "conclusion"
]

def normalizar_espacios(texto):
    if not texto:
        return texto
    texto = re.sub(r'\r', '\n', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{2,}', '\n\n', texto)
    texto = re.sub(r' +\n', '\n', texto)
    return texto.strip()

def extraer_texto_desde_pdf(flujo_archivo, max_paginas=None):
    try:
        lector = PdfReader(flujo_archivo)
    except Exception:
        return "", {}

    try:
        metadatos = {"info": lector.metadata or {}}
    except Exception:
        metadatos = {}

    num_paginas = len(lector.pages)
    limite = num_paginas if not max_paginas else min(num_paginas, max_paginas)
    paginas = []
    for i in range(limite):
        try:
            texto_pagina = lector.pages[i].extract_text() or ""
            paginas.append(texto_pagina)
        except Exception:
            paginas.append("")

    texto = "\n".join(paginas)
    texto = normalizar_espacios(texto)
    return texto, metadatos

# --- Mantener la función de título existente (no tocar su lógica) ---
def extraer_titulo(texto):
    lineas = [linea.strip() for linea in texto.split("\n") if linea.strip()]
    palabras_omitidas = [
        "resumen", "abstract", "summary", "palabras clave", "keywords",
        "issn", "doi", "vol", "número", "universidad", "facultad",
        "editor", "página", "copyright", "fecha", "recibido",
        "revista", "licencia", "autor", "autores", "profesor", "departamento"
    ]
    limpias = []
    for linea in lineas[:60]:
        minuscula = linea.lower()
        if any(palabra in minuscula for palabra in palabras_omitidas):
            continue
        if re.match(r"^\d{4}", linea):
            continue
        if re.search(r"\b\d{4}\b", linea):
            continue
        if len(linea) < 5:
            continue
        limpias.append(linea)

    candidato = ""
    for i in range(min(20, len(limpias))):
        linea = limpias[i]
        if "," in linea and not linea.isupper():
            continue
        if len(linea.split()) >= 4 and linea.count(".") <= 1:
            bloque = [linea]
            j = i + 1
            while j < len(limpias) and len(limpias[j].split()) >= 3 and len(limpias[j]) < 120:
                if any(p in limpias[j].lower() for p in palabras_omitidas):
                    break
                bloque.append(limpias[j])
                j += 1
                if len(bloque) >= 3:
                    break
            candidato = " ".join(bloque)
            break

    if not candidato:
        mayusculas = [l for l in limpias[:20] if l.isupper() and len(l.split()) >= 3]
        if mayusculas:
            candidato = max(mayusculas, key=len)

    return candidato.strip()

# --- Nuevas funciones de extracción portadas desde JS ---
def extraer_autores(texto):
    patrones = [
        r'AUTOR(?:ES)?\s*:?\s*([^\n]{5,150})',
        r'PRESENTADO\s+POR\s*:?\s*([^\n]{5,150})',
        r'([A-ZÁÉÍÓÚÑ][a-záéíóúñÁÉÍÓÚÑ\.,\s]+)\s*\n(?:UNIVERSIDAD|FACULTAD|RESUMEN|ABSTRACT)'
    ]
    for patron in patrones:
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            return re.sub(r'\s+', ' ', m.group(1)).strip()
    # fallback: buscar línea con formato "Apellido, Nombre"
    m = re.search(r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)', texto)
    return m.group(1).strip() if m else ''

def extraer_universidad(texto):
    m = re.search(r'(UNIVERSIDAD\s+[^\n]{5,150})', texto, re.IGNORECASE)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''

def extraer_anio(texto):
    # buscar años razonables 1980-2029
    anios = re.findall(r'\b(19[8-9]\d|20[0-2]\d)\b', texto)
    if anios:
        try:
            anios_int = [int(a) for a in anios]
            return str(max(anios_int))
        except Exception:
            return anios[-1]
    return ''

def extraer_resumen(texto):
    m = re.search(r'(?:RESUMEN|ABSTRACT)\s*:?\s*([\s\S]{100,2000}?)(?:\n{2,}|INTRODUCCI|INTRODUCTION|CAPÍTULO|PALABRAS\s+CLAVE)', texto, re.IGNORECASE)
    if m:
        resumen = re.sub(r'\s+', ' ', m.group(1)).strip()
        return resumen if len(resumen) <= 1000 else resumen[:1000] + '...'
    return ''

def extraer_palabras_clave(texto):
    m = re.search(r'(?:PALABRAS\s+CLAVE|KEYWORDS)\s*:?\s*([^\n]{5,300})', texto, re.IGNORECASE)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()
    return ''

def extraer_introduccion(texto):
    m = re.search(r'INTRODUCCI[ÓO]N\s*([\s\S]{100,1500}?)(?:\n{2,}|CAPÍTULO|MARCO\s+TEÓRICO|OBJETIVOS)', texto, re.IGNORECASE)
    if m:
        intro = re.sub(r'\s+', ' ', m.group(1)).strip()
        return intro if len(intro) <= 800 else intro[:800] + '...'
    return ''

def extraer_metodologia(texto):
    m = re.search(r'(?:METODOLOG[IÍ]A|M[ÉE]TODOS?)\s*([\s\S]{100,1500}?)(?:\n{2,}|RESULTADOS|CAPÍTULO)', texto, re.IGNORECASE)
    if m:
        metod = re.sub(r'\s+', ' ', m.group(1)).strip()
        return metod if len(metod) <= 800 else metod[:800] + '...'
    return ''

def extraer_conclusion(texto):
    m = re.search(r'CONCLUSI[OÓ]N(?:ES)?\s*([\s\S]{100,1500}?)(?:\n{2,}|RECOMENDACIONES|REFERENCIAS|BIBLIOGRAF)', texto, re.IGNORECASE)
    if m:
        concl = re.sub(r'\s+', ' ', m.group(1)).strip()
        return concl if len(concl) <= 800 else concl[:800] + '...'
    return ''

def extraer_issn(texto):
    m = re.search(r'ISSN\s*:?\s*(\d{4}-\d{3}[\dXx])', texto, re.IGNORECASE)
    return m.group(1).upper() if m else ''

def extraer_tipo_publicacion(texto):
    if re.search(r'\bTESIS\b', texto, re.IGNORECASE):
        return 'Tesis'
    if re.search(r'\bARTÍCULO\b|\bARTICLE\b', texto, re.IGNORECASE):
        return 'Artículo'
    if re.search(r'\bCONFERENCIA\b|\bCONFERENCE\b', texto, re.IGNORECASE):
        return 'Conferencia'
    return ''

# Campos vacíos por defecto: nombrePublicacion, url, paises, quartil, indiceH, numeroCitas
def extraer_campos(texto, metadatos=None):
    datos = {}
    titulo_meta = None
    if metadatos and isinstance(metadatos, dict):
        info = metadatos.get("info") or {}
        titulo_meta = info.get("Title") or info.get("title") or None

    # título: conservar la lógica existente (no cambia)
    datos["titulo"] = extraer_titulo(texto) or titulo_meta or ""

    # resto de campos
    datos["autores"] = extraer_autores(texto)
    datos["filiaciones"] = extraer_universidad(texto)
    datos["anio"] = extraer_anio(texto)
    datos["resumen"] = extraer_resumen(texto)
    datos["palabrasClave"] = extraer_palabras_clave(texto)
    datos["introduccion"] = extraer_introduccion(texto)
    datos["metodologia"] = extraer_metodologia(texto)
    datos["conclusion"] = extraer_conclusion(texto)
    datos["issn"] = extraer_issn(texto)
    datos["tipoPublicacion"] = extraer_tipo_publicacion(texto)

    # campos que no se extraen del texto por ahora (dejar vacíos)
    datos["url"] = ""
    datos["paises"] = ""
    datos["nombrePublicacion"] = ""
    datos["quartil"] = ""
    datos["indiceH"] = ""
    datos["numeroCitas"] = ""
    datos["fuente"] = (metadatos.get("info", {}).get("Creator") if metadatos else "") or ""

    # asegurar todas las claves de CAMPOS existan
    for campo in CAMPOS:
        if campo not in datos:
            datos[campo] = ""

    # normalizar strings
    for k, v in list(datos.items()):
        datos[k] = v if isinstance(v, str) else str(v)

    return datos
