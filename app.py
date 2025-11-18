from flask import Flask, request, jsonify, render_template
import io
from pdf_utils import extraer_texto_desde_pdf, extraer_campos, CAMPOS

app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template("index.html", campos=CAMPOS)

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
    normalizados = {k.lower(): (v if isinstance(v, str) else str(v)) for k, v in campos.items()}

    return jsonify(normalizados)

if __name__ == '__main__':
    app.run(debug=True)
