// Prueba del traductor de la página (src/frontend/i18n/i18n.js) en jsdom, con un diccionario de prueba.
// Uso: node tests/frontend/i18n.mjs   (necesita `npm ci` en src/frontend/)
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import assert from 'node:assert/strict';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const { JSDOM } = createRequire(path.join(ROOT, 'src', 'frontend', 'package.json'))('jsdom');
const runtime = readFileSync(path.join(ROOT, 'src', 'frontend', 'i18n', 'i18n.js'), 'utf8');
const dict = { 'Entrar': 'Sign in', '{0} pasos': '{0} steps', 'Peso de hoy': "Today's weight",
  'Tu contraseña': 'Your password', 'Usuario': 'Username', 'el {0}': 'on {0}', '¿Seguro?': 'Sure?',
  'De {0} días{1}, {2} anotados.': 'Of {0} days{1}, {2} logged.', 'Máximo {0} kg.': 'Highest {0} kg.',
  '{0} días con pesada. Máximo {1} kg.': '{0} days weighed. Max {1} kg.', 'Tu cuenta.': 'Your account.' };

const dom = new JSDOM(`<!doctype html><html lang="es"><head>
<script>window.BL_LANG='en';window.BL_I18N=${JSON.stringify(dict)};</script><script>${runtime}</script></head>
<body><h1>Peso de hoy</h1><p id="a">  Entrar: </p><input id="u" placeholder="Usuario"><textarea>Entrar</textarea>
<p id="n" data-noi18n>Entrar</p></body></html>`, { runScripts: 'dangerously', pretendToBeVisual: true });
const w = dom.window, d = w.document;
const tick = () => new Promise(r => setTimeout(r, 0));
await tick();

assert.equal(d.documentElement.lang, 'en');
assert.equal(d.querySelector('h1').textContent, "Today's weight");
assert.equal(d.getElementById('a').textContent, ' Sign in: ');
assert.equal(d.getElementById('u').placeholder, 'Username');
assert.equal(d.querySelector('textarea').value, 'Entrar', 'lo que escribe la persona no se toca');
assert.equal(d.getElementById('n').textContent, 'Entrar', 'data-noi18n no se traduce');

// lo que la app pinta después también, con patrones y fechas
d.body.insertAdjacentHTML('beforeend', '<div id="b"><span>1234 pasos</span> · <b>el 19 nov</b><i title="Tu contraseña">x</i></div>');
await tick();
assert.equal(d.querySelector('#b span').textContent, '1234 steps');
assert.equal(d.querySelector('#b b').textContent, 'on 19 Nov');
assert.equal(d.querySelector('#b i').title, 'Your password');
const t = d.createTextNode('martes 3 de marzo'); d.body.appendChild(t); await tick();
assert.equal(t.data, 'Tuesday 3 March');
d.querySelector('h1').firstChild.data = 'Entrar'; await tick();
assert.equal(d.querySelector('h1').textContent, 'Sign in');

// números: lo que la app pide en es-ES sale con el formato del idioma
assert.equal(w.eval("(1234.5).toLocaleString('es-ES')"), '1,234.5');
assert.equal(new w.Intl.NumberFormat('es-ES').format(1234.5), '1,234.5');
assert.equal(w.blT('¿Seguro?'), 'Sure?');
// varias frases juntas, partes vacías y un «. » delante
assert.equal(w.blT('De 84 días, 0 anotados. Máximo 60 kg.'), 'Of 84 days, 0 logged. Highest 60 kg.');
assert.equal(w.blT('. Máximo 60 kg.'), '. Highest 60 kg.');
assert.equal(w.blT('De 84 días, 0 anotados. Máximo 60 kg. Sin traducir.'), 'Of 84 days, 0 logged. Highest 60 kg. Sin traducir.');
assert.equal(w.blT('3 días con pesada. Máximo 60 kg. Tu cuenta.'), '3 days weighed. Max 60 kg. Your account.');
console.log('i18n.js: OK');
