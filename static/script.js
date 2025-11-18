let data = [];
const root = document.documentElement;
const savedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
setTheme(savedTheme || (prefersDark ? 'dark' : 'light'));
const COLUMNAS = JSON.parse(
    document.getElementById("columnas-data").textContent
);


document.getElementById('themeToggle').addEventListener('click', () => {
  const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  setTheme(next);
});
function setTheme(mode){
  if(mode === 'dark') root.setAttribute('data-theme','dark');
  else root.removeAttribute('data-theme');
  localStorage.setItem('theme', mode);
}

// Build UI for selector columns and table
const resultEl = document.getElementById('result');
function crearUIResultados() {
  const html = `
    <div class="resultados">
      <div id="estadisticas" class="estadisticas"></div>
      <div class="selector-columnas">
        <h3>Selecciona las columnas a mostrar</h3>
        <div id="gridColumnas" class="grid-columnas"></div>
      </div>
      <div class="contenedor-tabla">
        <table>
          <thead><tr id="cabeceraTabla"></tr></thead>
          <tbody id="cuerpoTabla"></tbody>
        </table>
      </div>
      <div class="acciones">
        <button id="botonLimpiar" class="boton">Nuevo análisis</button>
        <button id="botonExportar" class="boton">Exportar CSV</button>
      </div>
    </div>
  `;
  resultEl.innerHTML = html;
  document.getElementById('botonLimpiar').addEventListener('click', limpiar);
  document.getElementById('botonExportar').addEventListener('click', exportarCSV);
}

// Inicializar UI con COLUMNAS
crearUIResultados();
const gridColumnas = document.getElementById('gridColumnas');
const cabeceraTabla = document.getElementById('cabeceraTabla');
const cuerpoTabla = document.getElementById('cuerpoTabla');
const estadisticas = document.getElementById('estadisticas');

let columnasVisibles = ['titulo']; // por defecto

function crearSelectorColumnas() {
  gridColumnas.innerHTML = '';
  Object.keys(COLUMNAS).forEach(clave => {
    const div = document.createElement('div');
    div.className = 'opcion-columna';
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `col-${clave}`;
    checkbox.value = clave;
    checkbox.checked = columnasVisibles.includes(clave);
    checkbox.addEventListener('change', actualizarTabla);
    const label = document.createElement('label');
    label.htmlFor = `col-${clave}`;
    label.textContent = COLUMNAS[clave];
    div.appendChild(checkbox);
    div.appendChild(label);
    gridColumnas.appendChild(div);
  });
}

function actualizarTabla() {
  columnasVisibles = [];
  document.querySelectorAll('#gridColumnas input[type="checkbox"]:checked').forEach(cb => columnasVisibles.push(cb.value));

  // Cabecera
  cabeceraTabla.innerHTML = '';
  columnasVisibles.forEach(col => {
    const th = document.createElement('th');
    th.textContent = COLUMNAS[col] || col;
    cabeceraTabla.appendChild(th);
  });

  // Cuerpo: múltiples filas (data)
  cuerpoTabla.innerHTML = '';
  for (const filaData of data) {
    const tr = document.createElement('tr');
    columnasVisibles.forEach(col => {
      const td = document.createElement('td');
      let valor = filaData[col] || '';
      valor = String(valor).replace(/\n/g, '<br>');
      td.innerHTML = `<div class="valor-campo">${valor || '<span class="valor-vacio">No disponible</span>'}</div>`;
      tr.appendChild(td);
    });
    cuerpoTabla.appendChild(tr);
  }
}

function mostrarEstadisticas() {
  const camposExtraidos = data.length ? Object.keys(data[0]).filter(k => data[0][k]).length : 0;
  estadisticas.innerHTML = `
    <div class="tarjeta-estadistica"><div class="etiqueta-estadistica">Documentos</div><div class="valor-estadistica">${data.length}</div></div>
    <div class="tarjeta-estadistica"><div class="etiqueta-estadistica">Campos extraídos (ej)</div><div class="valor-estadistica">${camposExtraidos}</div></div>
  `;
}

function limpiar() {
    location.reload();
}


// Exportar CSV
function exportarCSV() {
  if (!data.length) return alert('No hay datos para exportar');
  let csv = columnasVisibles.map(c => `"${(COLUMNAS[c]||c).replace(/"/g,'""')}"`).join(',') + '\n';
  for (const fila of data) {
    const valores = columnasVisibles.map(c => `"${(fila[c] || '').toString().replace(/"/g,'""')}"`);
    csv += valores.join(',') + '\n';
  }
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'datos_extraidos.csv';
  a.click();
  URL.revokeObjectURL(url);
}

// Manejo del formulario: enviar cada archivo al backend (secuencial)
document.getElementById('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const files = document.getElementById('pdf').files;
  if (!files.length) return alert('Selecciona uno o más PDF');
  const maxp = document.getElementById('maxp').value;

  // limpiar resultados previos
  data = [];
  crearSelectorColumnas();

  for (const f of files) {
    const fd = new FormData();
    fd.append('pdf', f);
    fd.append('maxp', maxp);

    try {
      const res = await fetch('/analizar', { method: 'POST', body: fd });
      if (!res.ok) {
        const err = await res.json().catch(()=>({error:'error'}));
        console.error('error', err);
        alert('Error analizando ' + f.name);
        continue;
      }
      const info = await res.json();
      // normalizar nombres de claves (el backend ya devuelve en camelCase)
      info.archivo = f.name;
      data.push(info);
      // permitir que el usuario active nuevas columnas conforme se agregan datos
      crearSelectorColumnas();
      actualizarTabla();
      mostrarEstadisticas();
    } catch (err) {
      console.error(err);
      alert('Fallo al analizar ' + f.name);
    }
  }

  // mostrar resultados completos
  resultEl.querySelector('.resultados').classList.add('mostrar');
});

// Inicializar controles
crearSelectorColumnas();
actualizarTabla();
mostrarEstadisticas();
