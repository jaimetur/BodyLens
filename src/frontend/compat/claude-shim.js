/* BodyLens en servidor: capa de compatibilidad con window.claude.
   La página es la misma que el artefacto de claude.ai; aquí se implementan las capacidades que usa
   (user, db, mcp, downloads, artifact, permissions) contra la API del servidor. */
(function () {
  'use strict';
  const ME = window.BODYLENS_USER || {};
  const DOC_POLL = 30e3, WB_POLL = 60e3;
  const HDR = { 'X-BodyLens': '1' };

  // Los datos de la app también se guardan en este navegador (claves «bascula:…»). Si entra otra persona,
  // se borran para que no vea los datos de la anterior.
  try {
    const k = 'bodylens:user';
    if (localStorage.getItem(k) !== String(ME.id)) {
      for (const key of Object.keys(localStorage)) if (key.startsWith('bascula:')) localStorage.removeItem(key);
      for (const key of Object.keys(sessionStorage)) if (key.startsWith('bascula:')) sessionStorage.removeItem(key);
      localStorage.setItem(k, String(ME.id));
    }
  } catch (e) { }

  async function api(method, url, body) {
    const opt = { method, headers: { ...HDR }, credentials: 'same-origin' };
    if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
    const r = await fetch(url, opt);
    if (r.status === 401) { location.href = '/login?next=' + encodeURIComponent(location.pathname + location.hash); throw err('unauthenticated'); }
    if (!r.ok) { let m = ''; try { m = (await r.json()).detail || '' } catch (e) { } throw err('server_error', m || ('HTTP ' + r.status)); }
    return r.status === 204 ? null : r.json();
  }
  function err(code, message) { const e = new Error(message || code); e.code = code; return e; }
  const enc = s => encodeURIComponent(s);
  const snap = (id, data) => ({ id, exists: data != null, data: () => (data == null ? undefined : JSON.parse(JSON.stringify(data))) });
  const onWake = fn => {
    document.addEventListener('visibilitychange', () => { if (!document.hidden) fn(); });
    window.addEventListener('focus', fn); window.addEventListener('online', fn);
  };

  /* ---------- db: colección de documentos ---------- */
  function collection(name) {
    // migración antigua del artefacto (espacio privado del usuario): aquí no existe
    if (String(name).includes('/')) {
      const empty = { docs: [], empty: true, size: 0, metadata: { fromCache: false } };
      return { get: async () => empty, onSnapshot: cb => { setTimeout(() => cb(empty), 0); return () => { }; }, doc: id => docRef(null, id) };
    }
    const base = '/api/docs/' + enc(name);
    const state = { docs: new Map(), rev: 0, mine: new Map(), subs: new Set(), timer: null, busy: false };
    const emit = () => {
      const qs = { docs: [...state.docs.entries()].map(([id, d]) => snap(id, d)), metadata: { fromCache: false, hasPendingWrites: false } };
      qs.size = qs.docs.length; qs.empty = !qs.size;
      for (const s of state.subs) try { s.cb(qs) } catch (e) { console.error(e) }
    };
    async function poll(full) {
      if (state.busy) return; state.busy = true;
      try {
        const res = await api('GET', base + (full ? '' : '?since=' + state.rev));
        let changed = !!full;
        if (full) state.docs.clear();
        for (const d of res.docs) {
          // lo que acabo de guardar yo no se vuelve a pintar
          if (!full && state.mine.get(d.id) === d.rev) continue;
          if (d.deleted) { if (state.docs.delete(d.id)) changed = true; }
          else { state.docs.set(d.id, d.data); changed = true; }
        }
        state.rev = Math.max(state.rev, res.rev);
        if (changed) emit();
      } catch (e) { for (const s of state.subs) if (s.err && full) try { s.err(e) } catch (_) { } }
      finally { state.busy = false; }
    }
    const coll = {
      doc: id => docRef(coll, id),
      get: async () => { await poll(true); return { docs: [...state.docs.entries()].map(([id, d]) => snap(id, d)), metadata: { fromCache: false } }; },
      onSnapshot(cb, errCb) {
        const sub = { cb, err: errCb }; state.subs.add(sub);
        if (state.subs.size === 1) {
          poll(true);
          state.timer = setInterval(() => { if (!document.hidden) poll(false) }, DOC_POLL);
          onWake(() => poll(false));
        } else if (state.docs.size) setTimeout(emit, 0);
        return () => { state.subs.delete(sub); if (!state.subs.size) clearInterval(state.timer); };
      },
      _state: state, _base: base,
    };
    return coll;
  }
  function docRef(coll, id) {
    const url = coll ? coll._base + '/' + enc(id) : null;
    const remember = (res, data) => { if (coll && res) { coll._state.mine.set(id, res.rev); if (data === null) coll._state.docs.delete(id); else coll._state.docs.set(id, data); } };
    return {
      id,
      async get() { if (!url) return snap(id, null); try { const r = await api('GET', url); return snap(id, r.data); } catch (e) { if (/404/.test(e.message)) return snap(id, null); throw e; } },
      async set(data) { if (!url) return; const res = await api('PUT', url, data); remember(res, data); },
      async update(patch) { if (!url) return; const res = await api('PATCH', url, patch); remember(res, res && res.data); },
      async delete() { if (!url) return; const res = await api('DELETE', url); remember(res, null); },
    };
  }

  /* ---------- mcp: el libro XLSX de los datos (en vez de Google Drive) ---------- */
  async function fetchWorkbook() {
    const r = await fetch('/api/workbook.xlsx', { headers: HDR, credentials: 'same-origin', cache: 'no-store' });
    if (r.status === 401) { location.href = '/login'; throw err('unauthenticated'); }
    if (r.status === 404) throw err('no_workbook', 'Todavía no hay datos de la báscula ni de Apple Salud en tu cuenta.');
    if (!r.ok) throw err('server_unavailable', 'El servidor no responde.');
    const buf = new Uint8Array(await r.arrayBuffer());
    let s = ''; for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
    return { etag: r.headers.get('ETag'), result: { payload: { content: btoa(s) }, cache: null } };
  }
  let lastEtag = null;
  const mcp = {
    async callTool() { const w = await fetchWorkbook(); lastEtag = w.etag; return w.result; },
    watchTool(server, tool, args, cb) {
      let stop = false, busy = false;
      async function check(force) {
        if (stop || busy) return; busy = true;
        try {
          const m = await api('GET', '/api/workbook/meta');
          // cuenta sin datos sincronizados todavía: se dice en el indicador en vez de quedarse en «Conectando…»
          if (!m.etag && force) try { setPill('', m.lastSync ? 'Sin datos de las fuentes' : 'Sin sincronizar todavía') } catch (e) { }
          if (m.etag && (force || '"' + m.etag + '"' !== lastEtag)) { const w = await fetchWorkbook(); lastEtag = w.etag; if (!stop) cb({ type: 'data', result: w.result }); }
        } catch (e) { if (!stop && e.code !== 'unauthenticated') cb({ type: 'error', error: e }); }
        finally { busy = false; }
      }
      check(true);
      const t = setInterval(() => { if (!document.hidden) check(false) }, WB_POLL);
      onWake(() => check(false));
      return () => { stop = true; clearInterval(t); };
    },
  };

  /* ---------- descargas ---------- */
  const downloads = {
    async save({ filename, data, mimeType }) {
      const blob = data instanceof Blob ? data : new Blob([data], { type: mimeType || 'application/octet-stream' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = filename || 'bodylens';
      document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    },
  };

  const user = { isOwner: async () => true, id: async () => String(ME.id) };
  const caps = { user, downloads, mcp, db: { collection }, artifact: null, permissions: { manage: async () => { } } };
  window.claude = { use: async name => (name in caps ? caps[name] : null) };

  /* ---------- aviso de servidor actualizado (como en DriveTest Analyzer) ----------
     La página sabe con qué versión del servidor se cargó; si el servidor responde con otra, avisa para recargar.
     No recarga sola: lo que se esté escribiendo se guarda igualmente (cada cambio se manda al momento). */
  (function updates() {
    const mine = window.BODYLENS_BUILD || '';
    let shown = null, dismissed = '';
    const css = document.createElement('style');
    css.textContent = '.bl-update{position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom));transform:translateX(-50%);z-index:9999;display:flex;align-items:center;gap:10px;max-width:min(560px,calc(100vw - 24px));padding:10px 12px 10px 14px;border-radius:14px;background:#121a26;color:#fff;box-shadow:0 8px 28px rgba(0,0,0,.28);font:14px/1.35 "Instrument Sans",-apple-system,sans-serif}' +
      '.bl-update b{display:block}.bl-update span{opacity:.85}.bl-update button{font:inherit;font-weight:600;border:0;border-radius:10px;padding:8px 12px;cursor:pointer}' +
      '.bl-update .go{background:#3B7BF2;color:#fff;white-space:nowrap}.bl-update .x{background:transparent;color:#fff;opacity:.7;padding:6px 8px;font-size:18px;line-height:1}';
    document.head.appendChild(css);
    function show(build) {
      if (!mine || !build || build === mine || build === dismissed || shown) return;
      shown = document.createElement('div'); shown.className = 'bl-update'; shown.setAttribute('role', 'alert');
      shown.innerHTML = '<div><b>BodyLens se ha actualizado.</b><span>Recarga la página para ver los últimos cambios.</span></div>';
      const go = document.createElement('button'); go.className = 'go'; go.type = 'button'; go.textContent = 'Recargar';
      go.onclick = () => location.reload();
      const x = document.createElement('button'); x.className = 'x'; x.type = 'button'; x.setAttribute('aria-label', 'Cerrar'); x.title = 'Recordármelo luego'; x.textContent = '×';
      x.onclick = () => { dismissed = build; shown.remove(); shown = null; };
      shown.append(go, x); document.body.appendChild(shown);
    }
    async function check() {
      try { const r = await fetch('/api/version', { cache: 'no-store' }); if (r.ok) show((await r.json()).build); } catch (e) { }
    }
    setInterval(() => { if (!document.hidden) check(); }, 60e3);
    onWake(check);
  })();

  /* ---------- enganches que usa la página en modo servidor ---------- */
  window.BL = {
    // perfil principal con el nombre de la cuenta
    profDef: () => [{ id: '', name: ME.name || ME.username || 'Yo', col: '#3f51e0' }],
    // botón «Actualizar»: sincroniza ya en el servidor y vuelve a leer los datos
    async pull() {
      const b = document.getElementById('pullBtn');
      try { setPill('', 'Sincronizando…') } catch (e) { }
      b && b.classList.add('spin');
      try {
        const r = await api('POST', '/api/sync');
        try { toast(r.message || (r.ok ? 'Datos al día ✓' : 'No se pudo sincronizar.'), 5000) } catch (e) { }
        try { syncNow() } catch (e) { b && b.classList.remove('spin') }
      } catch (e) {
        b && b.classList.remove('spin');
        try { toast('No se pudo sincronizar: ' + (e.message || 'error'), 6000); setPill('err', 'Sin sincronizar') } catch (_) { }
      }
    },
  };
})();
