/* utilidades comunes de las páginas del servidor */
// dentro de la app (sección «Tu cuenta» o «Administración») la página va sin cabecera y a todo el ancho
const EMBED = window.top !== window || new URLSearchParams(location.search).has('embed');
if (EMBED) document.documentElement.classList.add('embed');
// inside the app (phones): a sideways swipe changes tab, as in the app's own modules
if (EMBED) {
  let sx = 0, sy = 0, st = 0, ok = false;
  const scrolls = n => { for (; n && n !== document.body; n = n.parentElement) if (n.scrollWidth > n.clientWidth + 2 && /auto|scroll/.test(getComputedStyle(n).overflowX)) return true; return false; };
  addEventListener('touchstart', e => { const t = e.touches[0]; ok = e.touches.length === 1 && !e.target.closest('input,select,textarea,dialog,[data-noswipe]') && !scrolls(e.target); sx = t.clientX; sy = t.clientY; st = Date.now(); }, { passive: true });
  addEventListener('touchend', e => { if (!ok) return; ok = false; const t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 2 || Date.now() - st > 700) return;
    try { if (parent.blStripSwipe) parent.blStripSwipe(dx < 0); } catch (_) {} }, { passive: true });
}
const TOP = EMBED ? window.top : window;
const $ = id => document.getElementById(id);
// no zoom on phones: pinch, which iOS allows even with user-scalable=no (double tap: touch-action in pages.css); a page
// that a browser zoomed anyway (some ignore the limits) goes back to its normal size, and can always be pinched back out
(()=>{const vv=window.visualViewport,zoomed=()=>!!vv&&vv.scale>1.01;for(const t of ['gesturestart','gesturechange'])document.addEventListener(t,e=>{if(!zoomed()&&!(e.scale<1))e.preventDefault()},{passive:false});document.addEventListener('touchmove',e=>{if(e.touches.length>1&&!zoomed())e.preventDefault()},{passive:false});let T;const unzoom=()=>{if(!zoomed())return;const m=document.querySelector('meta[name=viewport]');if(!m)return;const c=m.content;m.content='width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover';setTimeout(()=>{m.content=c},80)};if(vv)vv.addEventListener('resize',()=>{clearTimeout(T);T=setTimeout(unzoom,400)});addEventListener('pageshow',unzoom);document.addEventListener('visibilitychange',()=>{if(!document.hidden)unzoom()});window.blUnzoom=unzoom})();
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
// activity inside a page shown in the app keeps the profile from locking itself for inactivity
if (EMBED) for (const ev of ['pointerdown', 'pointermove', 'keydown', 'wheel', 'touchstart', 'scroll'])
  addEventListener(ev, () => { try { if (TOP.blActivity) TOP.blActivity(); } catch (e) { /* other origin */ } }, { passive: true, capture: true });
if (EMBED && window.frameElement) {
  const m = document.querySelector('main');
  if (m) new ResizeObserver(blFitFrame).observe(m);
  addEventListener('load', blFitFrame);
  addEventListener('resize', blFitFrame);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(blFitFrame);
}
