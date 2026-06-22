async function jsonFetch(path, opts={}){
  const url = (API_BASE||'') + path;
  const res = await fetch(url, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function elt(tag, props={}, ...children){
  const e = document.createElement(tag);
  Object.assign(e, props);
  for (const c of children) e.append(c instanceof Node ? c : document.createTextNode(c));
  return e;
}

async function loadList(){
  try{
    const data = await jsonFetch('/api/urls');
    const tbody = document.querySelector('#urlsTable tbody');
    tbody.innerHTML = '';
    for (const u of data){
      const tr = elt('tr', {},
        elt('td', {}, u.title || u.long_url.slice(0,60)),
        elt('td', {}, elt('a', {href: (API_BASE||'')+u.short_code, target:'_blank'}, (API_BASE||'')+u.short_code)),
        elt('td', {}, String(u.clicks||0)),
        elt('td', {}, u.tags||''),
        elt('td', {}, u.description||''),
        elt('td', {}, u.created_at||'')
      );
      tbody.appendChild(tr);
    }
    document.getElementById('exportLink').href = (API_BASE||'') + '/api/export';
  }catch(e){
    console.error(e);
    alert('Failed to load list: '+e.message);
  }
}

document.getElementById('addForm').addEventListener('submit', async (ev)=>{
  ev.preventDefault();
  const f = ev.target;
  const data = {
    long_url: f.long_url.value,
    title: f.title.value,
    description: f.description.value,
    tags: f.tags.value,
    custom_code: f.custom_code.value
  };
  try{
    const res = await jsonFetch('/api/add', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    const d = document.getElementById('shortResult');
    d.classList.remove('hidden');
    d.innerHTML = `<p>Short URL: <a href="${res.short_url}" target="_blank">${res.short_url}</a></p><p><img src="${res.qr_data_uri}" alt="QR"></p>`;
    f.reset();
    loadList();
  }catch(e){
    alert('Add failed: '+e.message);
  }
});

document.getElementById('searchForm').addEventListener('submit', async (ev)=>{
  ev.preventDefault();
  const q = ev.target.q.value.trim();
  if(!q){ loadList(); return }
  try{
    const data = await jsonFetch('/api/search?q='+encodeURIComponent(q));
    const tbody = document.querySelector('#urlsTable tbody');
    tbody.innerHTML = '';
    for (const u of data) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${u.title||u.long_url.slice(0,60)}</td><td><a href="${(API_BASE||'')+u.short_code}" target="_blank">${(API_BASE||'')+u.short_code}</a></td><td>${u.clicks||0}</td><td>${u.tags||''}</td><td>${u.description||''}</td><td>${u.created_at||''}</td>`;
      tbody.appendChild(tr);
    }
  }catch(e){ alert('Search failed: '+e.message) }
});

document.getElementById('clearBtn').addEventListener('click', ()=>{ document.getElementById('searchForm').q.value=''; loadList(); });

loadList();
