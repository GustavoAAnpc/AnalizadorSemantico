from flask import Flask, request, jsonify, render_template
import io
from pdf_utils import extraer_texto_desde_pdf, extraer_campos, CAMPOS

app = Flask(__name__, static_folder="static", template_folder="templates")

# Etiquetas legibles para el frontend
COLUMNAS = {
    "titulo": "Título",
    "url": "URL",
    "fuente": "Fuente",
    "anio": "Año",
    "paises": "Países",
    "issn": "ISSN",
    "tipoPublicacion": "Tipo Publicación",
    "nombrePublicacion": "Nombre Publicación",
    "autores": "Autores",
    "filiaciones": "Filiaciones",
    "quartil": "Quartil",
    "indiceH": "Índice H",
    "numeroCitas": "Nº Citas",
    "resumen": "Resumen",
    "palabrasClave": "Palabras Clave",
    "introduccion": "Introducción",
    "metodologia": "Metodología",
    "conclusion": "Conclusión"
}

@app.route('/')
def inicio():
    return render_template("index.html", columnas=COLUMNAS)

@app.route('/analizar', methods=['POST'])
def analizar():
    archivo = request.files.get('pdf')
    if not archivo:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    try:
        max_paginas = int(request.form.get('maxp') or 10)
    except Exception:
        max_paginas = 10

    flujo = io.BytesIO(archivo.read())
    texto, metadatos = extraer_texto_desde_pdf(flujo, max_paginas=max_paginas)
    campos = extraer_campos(texto, metadatos=metadatos)

    # Normalizar keys a lower camelCase ya están así en pdf_utils; devolver JSON
    return jsonify(campos)

if __name__ == '__main__':
    app.run(debug=True)
