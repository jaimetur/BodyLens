// Prueba de arranque: levanta el servidor con una base vacía, crea una cuenta, entra y carga la página servida
// (con la capa claude-shim.js y las librerías locales) en jsdom. Falla si hay errores de JavaScript.
// Uso: node tests/frontend/smoke.mjs   (necesita las dependencias del backend y `npm ci` en src/frontend/)
import { spawn, execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, copyFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
// jsdom se instala con las dependencias de src/frontend (npm ci)
const { JSDOM, VirtualConsole, ResourceLoader, CookieJar } = createRequire(path.join(ROOT, 'src', 'frontend', 'package.json'))('jsdom');
const PY = process.env.PYTHON || 'python3';
const PORT = 8000 + Math.floor(Math.random() * 900) + 50;
const BASE = `http://127.0.0.1:${PORT}`;
const tmp = mkdtempSync(path.join(tmpdir(), 'bodylens-smoke-'));
const vendor = path.join(tmp, 'vendor'); mkdirSync(vendor);
const nm = path.join(ROOT, 'src', 'frontend', 'node_modules');
copyFileSync(path.join(nm, 'xlsx/dist/xlsx.full.min.js'), path.join(vendor, 'xlsx.full.min.js'));
copyFileSync(path.join(nm, 'jspdf/dist/jspdf.umd.min.js'), path.join(vendor, 'jspdf.umd.min.js'));
copyFileSync(path.join(nm, 'html2canvas-pro/dist/html2canvas-pro.min.js'), path.join(vendor, 'html2canvas-pro.min.js'));

const env = { ...process.env, DATA_DIR: path.join(tmp, 'data'), FRONTEND_DIR: path.join(ROOT, 'src', 'frontend'),
  BRANDING_DIR: path.join(ROOT, 'assets', 'branding'), VENDOR_DIR: vendor, COOKIE_SECURE: '0', SCHEDULER_ENABLED: '0',
  BODYLENS_NEW_PASSWORD: 'contraseña-de-prueba' };
const cwd = path.join(ROOT, 'src', 'backend');
execFileSync(PY, ['-m', 'app.accounts.cli', 'crear-admin', 'prueba', 'Persona Prueba'], { cwd, env, stdio: 'inherit' });
const srv = spawn(PY, ['-m', 'uvicorn', 'app.main:app', '--port', String(PORT)], { cwd, env, stdio: ['ignore', 'inherit', 'inherit'] });
const done = code => { try { srv.kill() } catch (e) { } rmSync(tmp, { recursive: true, force: true }); process.exit(code); };

try {
  for (let i = 0; ; i++) { try { if ((await fetch(BASE + '/healthz')).ok) break } catch (e) { } if (i > 80) throw new Error('el servidor no arranca'); await new Promise(r => setTimeout(r, 250)); }
  const jar = new CookieJar();
  const login = await fetch(BASE + '/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-BodyLens': '1' },
    body: JSON.stringify({ username: 'prueba', password: env.BODYLENS_NEW_PASSWORD }) });
  if (!login.ok) throw new Error('login: ' + login.status);
  for (const c of login.headers.getSetCookie()) jar.setCookieSync(c, BASE);
  const cookie = jar.getCookieStringSync(BASE);
  // un documento guardado de antes para comprobar que la colección llega a la página
  await fetch(BASE + '/api/docs/bascula/medidas', { method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-BodyLens': '1', cookie }, body: JSON.stringify({ v: 1, e: {} }) });
  const html = await (await fetch(BASE + '/', { headers: { cookie } })).text();

  const errors = [];
  const vc = new VirtualConsole();
  vc.on('jsdomError', e => { if (!/scrollTo|Not implemented/.test(e.message)) errors.push('jsdomError: ' + (e.detail && e.detail.stack || e.stack || e.message)); });
  vc.on('error', (...a) => errors.push('console.error: ' + a.map(x => x && x.stack || x).join(' ')));
  class LocalOnly extends ResourceLoader { fetch(url, o) { return url.startsWith(BASE) ? super.fetch(url, o) : Promise.resolve(Buffer.from('')); } }
  const dom = new JSDOM(html, { url: BASE + '/#resumen', runScripts: 'dangerously', resources: new LocalOnly(), cookieJar: jar, pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) {
      w.ResizeObserver = class { observe() { } unobserve() { } disconnect() { } };
      w.matchMedia = () => ({ matches: false, addEventListener() { }, removeEventListener() { }, addListener() { } });
      w.scrollTo = () => { };
      // fetch del navegador con la cookie de la sesión
      w.fetch = (u, o = {}) => fetch(new URL(u, BASE), { ...o, headers: { ...(o.headers || {}), cookie } });
    } });
  const w = dom.window;
  await new Promise(r => setTimeout(r, 4000));
  const $ = id => w.document.getElementById(id);
  const checks = {
    shim: typeof w.claude === 'object' && w.BODYLENS_SERVER === true,
    xlsx: typeof w.XLSX === 'object' && typeof w.XLSX.read === 'function',
    perfil: ($('pfBtn') && $('pfBtn').textContent || '').includes('Persona'),
    noViewer: !w.document.body.classList.contains('viewer'),
    pill: $('syncPill') && $('syncPill').textContent,
  };
  console.log('comprobaciones', JSON.stringify(checks));
  if (!checks.shim || !checks.xlsx || !checks.perfil || !checks.noViewer) errors.push('comprobación fallida');
  console.log(errors.length ? 'ERRORES\n' + errors.join('\n') : 'Arranque correcto, sin errores');
  w.close();
  done(errors.length ? 1 : 0);
} catch (e) { console.error(e); done(1); }
