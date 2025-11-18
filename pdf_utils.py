import re
from PyPDF2 import PdfReader

CAMPOS = ["titulo"]

def normalizar_espacios(texto):
    if not texto:
        return texto
    texto = re.sub(r'\r', '\n', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{2,}', '\n', texto)
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

def extraer_campos(texto, metadatos=None):
    datos = {}
    titulo_meta = None
    if metadatos and isinstance(metadatos, dict):
        info = metadatos.get("info") or {}
        titulo_meta = info.get("Title") or info.get("title") or None

    datos["titulo"] = extraer_titulo(texto) or titulo_meta or ""

    for campo in CAMPOS:
        if campo not in datos:
            datos[campo] = ""
    return datos