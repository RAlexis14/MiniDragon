let page = 1;

// Guard session
(async function ensureAuth() {
  const res = await fetch("/auth/me", { credentials: "include" });
  if (!res.ok) window.location.href = "/";
})();

// Buttons
document.getElementById("btnSearch").addEventListener("click", () => confirmSearch());
document.getElementById("prev").addEventListener("click", () => { if (page > 1) { page--; confirmSearch(false); } });
document.getElementById("next").addEventListener("click", () => { page++; confirmSearch(false); });
document.getElementById("btnLogout").addEventListener("click", async () => {
  await fetch("/auth/logout", { method: "POST", credentials: "include" });
  window.location.href = "/";
});
document.getElementById("btnHistory").addEventListener("click", loadHistory);

// Enter confirma búsqueda
document.getElementById("q").addEventListener("keydown", (e)=>{
  if(e.key === "Enter"){ e.preventDefault(); confirmSearch(); }
});

// Debounced live search (no log)
function debounce(fn, ms=300){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), ms); }; }
document.getElementById("q").addEventListener("input", debounce(()=>{ page=1; liveSearch(); }, 300));

async function liveSearch(){
  await search(/*shouldLog=*/false);
  // Además, filtro “empieza con” en cliente
  const needle = document.getElementById("q").value.trim().toLowerCase();
  if (needle) {
    document.querySelectorAll(".char-card").forEach(card=>{
      const name = card.dataset.name.toLowerCase();
      card.parentElement.style.display = name.startsWith(needle) ? "" : "none";
    });
  }
}

function confirmSearch(log = true){
  search(/*shouldLog=*/log);
}

async function search(shouldLog){
  const q = document.getElementById("q").value.trim();
  const url = new URL("/api/characters", window.location.origin);
  if (q) url.searchParams.set("q", q);
  url.searchParams.set("page", String(page));
  url.searchParams.set("log", shouldLog ? "1" : "0"); // ← clave

  const grid = document.getElementById("grid");
  grid.innerHTML = `<div class="text-center text-muted">Cargando...</div>`;

  try {
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) { grid.innerHTML = `<div class="text-danger">No autorizado o error del servidor.</div>`; return; }
    const payload = await res.json();
    const list = Array.isArray(payload.data?.items || payload.data?.characters || payload.data?.results)
      ? (payload.data.items || payload.data.characters || payload.data.results)
      : (Array.isArray(payload.data) ? payload.data : []);
    grid.innerHTML = list.map(renderCard).join("") || `<div class="text-center text-muted">Sin resultados</div>`;
    attachCardClicks();
  } catch {
    grid.innerHTML = `<div class="text-danger">Error de red.</div>`;
  }
}

function renderCard(c){
  const id   = c.id || c._id || c.slug || "";   // algunos APIs no traen id
  const name = c.name || c.character || c.nickname || "Unknown";
  const img  = c.image || c.img || c.photo || "";
  const desc = c.race ? `Race: ${c.race}` : (c.ki ? `Ki: ${c.ki}` : (c.gender ? `Gender: ${c.gender}` : "Dragon Ball character"));
  return `
  <div class="col-12 col-sm-6 col-md-4 col-lg-3">
    <div class="card h-100 shadow-sm char-card" data-id="${id}" data-name="${name}">
      ${img ? `<div class="img-box"><img src="${img}" class="card-img-top" alt="${name}"></div>` : ""}
      <div class="card-body">
        <h5 class="card-title">${name}</h5>
        <p class="card-text small text-muted">${desc}</p>
      </div>
    </div>
  </div>`;
}

function attachCardClicks(){
  document.querySelectorAll(".char-card").forEach(el=>{
    el.addEventListener("click", ()=>openDetail(el.dataset.id, el.dataset.name));
  });
}

async function openDetail(id, fallbackName){
  const modalEl = document.getElementById('charModal');
  const title = document.getElementById('charTitle');
  const body  = document.getElementById('charBody');

  title.textContent = fallbackName || "Detalle";
  body.innerHTML = `<div class="text-center text-muted">Cargando...</div>`;

  let data;
  try{
    if(id){
      const res = await fetch(`/api/characters/${id}`, { credentials:"include" });
      if(res.ok){
        const payload = await res.json();
        data = payload.data || {};
      }
    }
  }catch{}

  const name = (data?.name || data?.character || fallbackName || "Personaje");
  const img  = data?.image || data?.img || "";
  const race = data?.race || data?.species || "";
  const ki   = data?.ki || data?.power || "";
  const gender = data?.gender || "";
  const origin = data?.originPlanet?.name || data?.affiliation || "";

  body.innerHTML = `
    <div class="row g-3 align-items-start">
      <div class="col-md-4 text-center">${img ? `<img src="${img}" alt="${name}" class="img-fluid">` : ""}</div>
      <div class="col-md-8">
        <h5>${name}</h5>
        <ul class="list-unstyled small mb-1">
          ${race?`<li><b>Race:</b> ${race}</li>`:""}
          ${gender?`<li><b>Gender:</b> ${gender}</li>`:""}
          ${ki?`<li><b>Ki/Power:</b> ${ki}</li>`:""}
          ${origin?`<li><b>Origin/Affiliation:</b> ${origin}</li>`:""}
        </ul>
        <div class="text-muted small">ID: ${id || "-"}</div>
      </div>
    </div>
  `;
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();

  // Siempre registra vista (si el API no soporta detalle por id, igual queda el log)
  try{
    await fetch("/api/view/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ id, name })
    });
    loadHistory(); // refresca tabla de vistos
  }catch{}
}

async function loadHistory(){
  // searches
  const r1 = await fetch("/api/search/logs?limit=20", { credentials:"include" });
  const logs = r1.ok ? (await r1.json()).logs : [];
  const tb1 = document.querySelector("#tblHistory tbody");
  tb1.innerHTML = logs.map((r,i)=>{
    const when = new Date(r.created_at).toLocaleString('es-EC'); // formatea en cliente
    return `<tr>
      <td>${i+1}</td><td>${r.query}</td><td>${r.results_count}</td>
      <td>${r.sample_names}</td><td><span class="text-muted">${when}</span></td>
    </tr>`;
  }).join('') || `<tr><td colspan="5" class="text-center text-muted">Sin registros</td></tr>`;

  // views
  const r2 = await fetch("/api/view/logs?limit=20", { credentials:"include" });
  const views = r2.ok ? (await r2.json()).logs : [];
  const tb2 = document.querySelector("#tblViews tbody");
  tb2.innerHTML = views.map((r,i)=>{
    const when = new Date(r.created_at).toLocaleString('es-EC');
    return `<tr>
      <td>${i+1}</td><td>${r.character_id ?? "-"}</td><td>${r.character_name}</td>
      <td><span class="text-muted">${when}</span></td>
    </tr>`;
  }).join('') || `<tr><td colspan="4" class="text-center text-muted">Sin vistas</td></tr>`;
}

// initial load
confirmSearch(false); // primera carga, sin log
loadHistory();
