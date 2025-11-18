# app.py
from flask import Flask, request, jsonify, render_template_string
import io, re
from PyPDF2 import PdfReader

app = Flask(__name__)

FIELDS = [
    "titulo"
]

def normalize_whitespace(s):
    if not s:
        return s
    s = re.sub(r'\r', '\n', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = re.sub(r'[ \t]{2,}', ' ', s)
    return s.strip()

def extract_text_from_pdf_stream(file_stream, max_pages=None):
    try:
        reader = PdfReader(file_stream)
    except Exception:
        return "", {}
    pages = []
    metadata = {}
    try:
        metadata = {'info': reader.metadata or {}}
    except Exception:
        metadata = {}
    num_pages = len(reader.pages)
    limit = num_pages if not max_pages else min(num_pages, max_pages)
    for i in range(limit):
        try:
            pages.append(reader.pages[i].extract_text() or "")
        except Exception:
            pages.append("")
    text = "\n".join(pages)
    text = normalize_whitespace(text)
    return text, metadata

def extract_title(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    skip_words = [
        "resumen", "abstract", "summary", "palabras clave", "keywords",
        "issn", "doi", "vol", "número", "universidad", "facultad",
        "editor", "página", "copyright", "fecha de recepción",
        "receipt", "revista", "agosto", "enero", "junio"
    ]

    clean = []
    for line in lines[:40]:
        lower = line.lower()
        if any(word in lower for word in skip_words):
            continue
        if re.match(r"^\d{4}", line): 
            continue
        if re.match(r".*\d{4}.*", line) and len(line) < 20:
            continue
        clean.append(line)

    title_block = []
    for i, line in enumerate(clean[:15]):
        lower = line.lower()

        if "," in line and not line.isupper():
            continue
        if len(line) < 6:
            continue

        title_block.append(line)

        j = i + 1
        while j < len(clean):
            next_line = clean[j].strip()
            if not next_line:
                break
            lower2 = next_line.lower()

            if any(lower2.startswith(w) for w in ["resumen", "abstract", "summary"]):
                break

            if len(next_line) > 5 and not next_line.endswith("."):
                title_block.append(next_line)
                j += 1
                if len(title_block) >= 4:
                    break
            else:
                break
        break

    return " ".join(title_block).strip()


def extract_fields(text, metadata=None):
    data = {}
    meta_title = None
    if metadata and isinstance(metadata, dict):
        info = metadata.get('info') or {}
        meta_title = info.get('Title') or info.get('title') or None

    data['titulo'] = extract_title(text) or meta_title or ""

    for k in FIELDS:
        if k not in data:
            data[k] = ""
    return data

HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Extractor de PDF</title>
  <style>
    :root{
      --bg:#f6f7fb;
      --card:#ffffff;
      --text:#0f172a;
      --muted:#64748b;
      --primary:#0d6efd;
      --primary-contrast:#ffffff;
      --border:#e5e7eb;
      --shadow:0 10px 30px rgba(0,0,0,.08);
      --input-bg:#ffffff;
    }
    [data-theme="dark"]{
      --bg:#0b1220;
      --card:#0f172a;
      --text:#e5e7ef;
      --muted:#9aa3b2;
      --primary:#60a5fa;
      --primary-contrast:#0b1220;
      --border:#1f2937;
      --shadow:0 12px 30px rgba(0,0,0,.45);
      --input-bg:#0b1220;
    }
    *{box-sizing:border-box}
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;padding:24px;background:var(--bg);color:var(--text);transition:background-color .35s ease,color .35s ease}
    .wrap{max-width:980px;margin:auto;background:var(--card);padding:24px 28px;border-radius:14px;box-shadow:var(--shadow);border:1px solid var(--border);transition:background-color .35s ease,color .35s ease,border-color .35s ease,box-shadow .35s ease}
    .topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}
    h2{margin:0;font-size:22px}
    .controls{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-top:10px}
    .file{display:inline-block}
    input[type="file"]{background:var(--input-bg);border:1px dashed var(--border);padding:10px;border-radius:10px;color:var(--text);transition:background-color .35s ease,color .35s ease,border-color .35s ease}
    select{background:var(--input-bg);color:var(--text);border:1px solid var(--border);padding:10px 12px;border-radius:10px;transition:background-color .35s ease,color .35s ease,border-color .35s ease}
    button{background:var(--primary);color:var(--primary-contrast);border:none;padding:10px 16px;border-radius:10px;cursor:pointer;font-weight:600;transition:transform .05s ease,opacity .2s ease}
    button:active{transform:translateY(1px)}
    .icon-btn{display:inline-flex;align-items:center;gap:8px}
    .muted{color:var(--muted);font-size:13px}
    .right{display:flex;align-items:center;gap:10px}
    .toggle{position:relative;width:54px;height:30px;background:var(--border);border-radius:999px;cursor:pointer;border:1px solid var(--border);transition:background-color .25s ease,border-color .25s ease}
    .knob{position:absolute;top:50%;left:3px;transform:translateY(-50%);width:24px;height:24px;background:#fff;border-radius:50%;transition:left .22s ease,background-color .22s ease}
    [data-theme="dark"] .knob{left:27px;background:#111827}
    .labels{display:flex;align-items:center;gap:6px;font-size:13px}
    .result{margin-top:18px}
    table{border-collapse:separate;border-spacing:0;width:100%;margin-top:12px;border:1px solid var(--border);border-radius:12px;overflow:hidden;transition:border-color .35s ease}
    thead th{background:linear-gradient(180deg, rgba(13,110,253,.95), rgba(13,110,253,.85));color:#fff;text-align:left;padding:12px 14px;transition:background-color .35s ease,color .35s ease}
    tbody td{border-top:1px solid var(--border);padding:12px 14px;vertical-align:top;background:var(--card);color:var(--text);transition:background-color .35s ease,color .35s ease,border-color .35s ease}
    @media (prefers-reduced-motion: reduce){
      *, *::before, *::after{transition:none !important}
    }
    .empty{padding:14px;border:1px dashed var(--border);border-radius:12px;text-align:center}
    .footer{margin-top:10px}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <h2>Subir PDF y extraer Título</h2>
      <div class="right">
        <div class="labels muted">Modo</div>
        <div id="themeToggle" class="toggle" title="Cambiar tema">
          <div class="knob"></div>
        </div>
      </div>
    </div>

    <form id="form" enctype="multipart/form-data">
      <div class="controls">
        <div class="file">
          <input type="file" id="pdf" name="pdf" accept="application/pdf">
        </div>
        <select id="maxp" aria-label="Páginas a analizar">
          <option value="5">5 páginas</option>
          <option value="10" selected>10 páginas</option>
          <option value="20">20 páginas</option>
        </select>
        <button id="go" class="icon-btn" type="submit">Analizar</button>
        <div class="muted">Solo se extrae el campo <strong>título</strong>.</div>
      </div>
    </form>

    <div id="result" class="result">
      <div class="empty muted">Sube un archivo PDF y presiona Analizar.</div>
    </div>

    <div class="footer muted">Consejo: el tema se guarda y respeta tu preferencia del sistema.</div>
  </div>

<script>
const FIELDS = {{ fields|tojson }};
let data = null;

// Tema: respeta preferencia y persiste en localStorage
const root = document.documentElement;
const savedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
setTheme(savedTheme || (prefersDark ? 'dark' : 'light'));
document.getElementById('themeToggle').addEventListener('click', () => {
  const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  setTheme(next);
});

function setTheme(mode){
  if(mode === 'dark') root.setAttribute('data-theme','dark');
  else root.removeAttribute('data-theme');
  localStorage.setItem('theme', mode);
}

document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = document.getElementById('pdf').files[0];
  if(!f) return alert('Selecciona un PDF');
  const fd = new FormData();
  fd.append('pdf', f);
  fd.append('maxp', document.getElementById('maxp').value);
  const res = await fetch('/parse', {method:'POST', body: fd});
  data = await res.json();
  if(data && !data.error){
    renderTable(['titulo']);
  }else{
    renderError(data && data.error ? data.error : 'Error al procesar el PDF');
  }
});

function renderTable(cols){
  const r = document.getElementById('result');
  let html = '<table><thead><tr>';
  for(const c of cols) html += `<th>${c}</th>`;
  html += '</tr></thead><tbody><tr>';
  for(const c of cols){
    const key = c.toLowerCase();
    let v = data[key] || '';
    v = v.replace(/\n/g,'<br>');
    html += `<td>${v}</td>`;
  }
  html += '</tr></tbody></table>';
  r.innerHTML = html;
}

function renderError(message){
  const r = document.getElementById('result');
  r.innerHTML = `<div class="empty" style="color:#ef4444;border-color:#ef4444">${message}</div>`;
}
</script>
</body></html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, fields=FIELDS)

@app.route('/parse', methods=['POST'])
def parse():
    f = request.files.get('pdf')
    if not f:
        return jsonify({"error": "No file"}), 400
    try:
        maxp = int(request.form.get('maxp') or 10)
    except Exception:
        maxp = 10
    data_stream = io.BytesIO(f.read())
    text, metadata = extract_text_from_pdf_stream(data_stream, max_pages=maxp)
    fields = extract_fields(text, metadata=metadata)
    normalized = {k.lower(): (v if isinstance(v, str) else str(v)) for k, v in fields.items()}
    return jsonify(normalized)

if __name__ == '__main__':
    app.run(debug=True)
