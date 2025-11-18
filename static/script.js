let data = null;

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
  const res = await fetch('/analizar', {method:'POST', body: fd});
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
