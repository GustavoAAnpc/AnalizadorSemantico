let data = [];


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
  const files = document.getElementById('pdf').files;
  if (!files.length) return alert('Selecciona uno o más PDF');

  const maxp = document.getElementById('maxp').value;

  for (const f of files) {
    const fd = new FormData();
    fd.append('pdf', f);
    fd.append('maxp', maxp);

    const res = await fetch('/analizar', { method: 'POST', body: fd });
    const info = await res.json();

    // <<<<< ESTE ES EL CAMBIO CLAVE >>>>>
    data.push({ archivo: f.name, ...info });
  }

  renderTable(['archivo', 'titulo']);
});



function renderTable(cols){
  const r = document.getElementById('result');
  let html = '<table><thead><tr>';
  for(const c of cols) html += `<th>${c}</th>`;
  html += '</tr></thead><tbody>';

  for(const row of data){
    html += '<tr>';
    for(const c of cols){
      const key = c.toLowerCase();
      let v = row[key] || '';
      v = String(v).replace(/\n/g,'<br>');
      html += `<td>${v}</td>`;
    }
    html += '</tr>';
  }

  html += '</tbody></table>';
  r.innerHTML = html;
}


function renderError(message){
  const r = document.getElementById('result');
  r.innerHTML = `<div class="empty" style="color:#ef4444;border-color:#ef4444">${message}</div>`;
}
