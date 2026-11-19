/* utilidades comunes de las páginas del servidor */
// dentro de la app (sección «Tu cuenta» o «Administración») la página va sin cabecera y a todo el ancho
const EMBED = window.top !== window || new URLSearchParams(location.search).has('embed');
if (EMBED) document.documentElement.classList.add('embed');
const TOP = EMBED ? window.top : window;
const $ = id => document.getElementById(id);
async function api(method, url, body) {
  const opt = { method, headers: { 'X-BodyLens': '1' }, credentials: 'same-origin' };
  if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
  const r = await fetch(url, opt);
  let data = null; try { data = await r.json() } catch (e) { }
  if (!r.ok) { const d = data && data.detail; throw new Error(typeof d === 'string' ? d : 'Algo ha fallado (' + r.status + ').'); }
  return data;
}
function say(el, text, kind) { el.textContent = text || ''; el.className = 'msg' + (kind ? ' ' + kind : ''); }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]); }
function when(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}
function safeNext() {
  const n = new URLSearchParams(location.search).get('next') || '/';
  return n.startsWith('/') && !n.startsWith('//') ? n : '/';
}
// idioma: selector con los idiomas disponibles (los nombres no se traducen)
function setLangCookie(l) { document.cookie = 'bl_lang=' + l + ';path=/;max-age=157680000;samesite=lax'; }
function langPicker(sel, onPick) {
  if (!sel) return;
  const L = window.BL_LANGS || { es: 'Español' };
  sel.setAttribute('data-noi18n', '');
  sel.innerHTML = Object.entries(L).map(([k, v]) => `<option value="${k}"${k === (window.BL_LANG || 'es') ? ' selected' : ''}>${esc(v)}</option>`).join('');
  sel.addEventListener('change', () => onPick(sel.value));
}
// en las páginas sin sesión (entrar, pedir cuenta, registro): se guarda en una cookie
langPicker(document.getElementById('langPick'), l => { setLangCookie(l); location.reload(); });
// language of a new account (access request, invitation): changing it also shows the page in that language,
// keeping what was typed (except passwords)
function langField(sel, keep) {
  if (!sel) return;
  const K = 'bl-form';
  try { const saved = JSON.parse(sessionStorage.getItem(K) || 'null'); sessionStorage.removeItem(K);
    if (saved) for (const id of keep) { const el = document.getElementById(id); if (el && saved[id] != null) el.value = saved[id]; } } catch (e) { }
  langPicker(sel, l => {
    try { const v = {}; for (const id of keep) { const el = document.getElementById(id); if (el) v[id] = el.value; } sessionStorage.setItem(K, JSON.stringify(v)); } catch (e) { }
    setLangCookie(l); location.reload();
  });
}
// inside the app, the page fits its frame to the height of its content (also when it gets shorter)
function blFitFrame() {
  const f = window.frameElement, m = document.querySelector('main');
  if (!f || !m) return;
  f.style.height = Math.max(480, Math.ceil(m.getBoundingClientRect().bottom + (window.scrollY || 0) + 24)) + 'px';
}
if (EMBED && window.frameElement) {
  const m = document.querySelector('main');
  if (m) new ResizeObserver(blFitFrame).observe(m);
  addEventListener('load', blFitFrame);
}
