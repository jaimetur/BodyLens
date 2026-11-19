/**
 * Withings -> "Control Diario" (columna C "Peso (Kg)")
 * Rellena SOLO celdas vacías de la columna C, con la primera pesada de cada día.
 * No toca ninguna otra columna.
 */

// ====== CONFIGURACIÓN ======
const SHEET_NAME = 'Control Diario';   // nombre de la pestaña
const DATE_COL = 2;                    // B = fecha
const WEIGHT_COL = 3;                  // C = Peso (Kg)
const DAYS_BACK = 30;                  // días hacia atrás a revisar
const AUTH_URL = 'https://account.withings.com/oauth2_user/authorize2';
const TOKEN_URL = 'https://wbsapi.withings.net/v2/oauth2';
const MEASURE_URL = 'https://wbsapi.withings.net/measure';

// ====== CREDENCIALES (se guardan en Propiedades del script, no en el código) ======
// Ejecuta UNA vez guardarCredenciales() tras rellenar los dos valores, y luego borra tus datos de aquí.
function guardarCredenciales() {
  const CLIENT_ID = 'REDACTADO';
  const CLIENT_SECRET = 'REDACTADO';
  PropertiesService.getScriptProperties().setProperties({
    CLIENT_ID: CLIENT_ID,
    CLIENT_SECRET: CLIENT_SECRET,
  });
  Logger.log('REDACTADO');
}

// ====== AUTORIZACIÓN (una sola vez) ======
function redirectUri_() {
  return 'https://script.google.com/macros/s/AKfycbyq4X7M4IRxqFM7ez4BYQ9SelLUPo1Wauc9zm4YgCfD8wubBL-rVKe5rytquF4D-7Ac/exec';
}

// Ejecuta esta función y abre en el navegador la URL que aparece en el registro.
function mostrarUrlAutorizacion() {
  const p = PropertiesService.getScriptProperties();
  const url = AUTH_URL +
    '?response_type=code' +
    '&client_id=' + encodeURIComponent(p.getProperty('CLIENT_ID')) +
    '&scope=user.metrics,user.activity' +
    '&state=peso2026' +
    '&redirect_uri=' + encodeURIComponent(redirectUri_());
  Logger.log('Redirect URI (regístrala en Withings): ' + redirectUri_());
  Logger.log('Abre esta URL para autorizar:\n' + url);
}

// Withings redirige aquí con ?code=...
function doGet(e) {
  // Botón «Traer de Withings ahora» de la app de la báscula: sincroniza al momento
  if (e && e.parameter && e.parameter.accion === 'sincronizar') return sincronizarDesdeWeb_();
  // Pesos de las hojas antiguas (se puede abrir desde el móvil)
  if (e && e.parameter && e.parameter.accion === 'pesos') {
    extraerPesosAntiguos(); const log = PESOS_LOG;
    return HtmlService.createHtmlOutput('<meta name="viewport" content="width=device-width,initial-scale=1"><div style="font:16px -apple-system,sans-serif;padding:20px;line-height:1.5"><h3>Pesos históricos</h3>' + log.map(s => '<p style="margin:4px 0">' + s + '</p>').join('') + '<p>Ya puedes cerrar esta pestaña.</p></div>');
  }
  // Recuperar notas antiguas del historial de versiones (se puede abrir desde el móvil)
  if (e && e.parameter && e.parameter.accion === 'notas') {
    if (e.parameter.reiniciar) reiniciarNotasHistoricas();
    const msg = recuperarNotasHistoricas();
    const url = ScriptApp.getService().getUrl() + '?accion=notas';
    return HtmlService.createHtmlOutput('<meta name="viewport" content="width=device-width,initial-scale=1"><div style="font:16px -apple-system,sans-serif;padding:20px;line-height:1.5"><h3>Notas históricas</h3><p>' + msg + '</p>' + (/pendientes: [1-9]/.test(msg) ? '<p><a target="_top" href="' + url + '" style="display:inline-block;padding:12px 18px;background:#5b6cf0;color:#fff;border-radius:10px;text-decoration:none">Seguir recuperando</a></p>' : '<p>Ya puedes cerrar esta pestaña.</p>') + '</div>');
  }
  if (!e || !e.parameter || e.parameter.state !== 'peso2026' || !e.parameter.code) {
    return HtmlService.createHtmlOutput('Falta el código de autorización.');
  }
  const ok = pedirToken_({
    action: 'requesttoken',
    grant_type: 'authorization_code',
    code: e.parameter.code,
    redirect_uri: redirectUri_(),
  });
  return HtmlService.createHtmlOutput(
    ok ? 'Autorización completada. Ya puedes cerrar esta pestaña.'
       : 'Error al obtener el token. Revisa el registro de ejecución.');
}

function pedirToken_(extra) {
  const p = PropertiesService.getScriptProperties();
  const payload = Object.assign({
    client_id: p.getProperty('CLIENT_ID'),
    client_secret: p.getProperty('CLIENT_SECRET'),
  }, extra);
  const res = UrlFetchApp.fetch(TOKEN_URL, { method: 'post', payload: payload, muteHttpExceptions: true });
  const json = JSON.parse(res.getContentText());
  if (json.status !== 0) {
    Logger.log('Error token Withings: ' + res.getContentText());
    return false;
  }
  p.setProperties({
    ACCESS_TOKEN: json.body.access_token,
    REFRESH_TOKEN: json.body.refresh_token,   // Withings rota el refresh token: hay que guardarlo siempre
    TOKEN_EXPIRES: String(Date.now() + (json.body.expires_in - 120) * 1000),
  });
  return true;
}

function tokenValido_() {
  const p = PropertiesService.getScriptProperties();
  if (!p.getProperty('REFRESH_TOKEN')) throw new Error('No autorizado todavía: ejecuta mostrarUrlAutorizacion().');
  if (Date.now() > Number(p.getProperty('TOKEN_EXPIRES') || 0)) {
    const ok = pedirToken_({
      action: 'requesttoken',
      grant_type: 'refresh_token',
      refresh_token: p.getProperty('REFRESH_TOKEN'),
    });
    if (!ok) throw new Error('No se pudo renovar el token de Withings. Repite la autorización.');
  }
  return p.getProperty('ACCESS_TOKEN');
}

// ====== LECTURA DE WITHINGS ======
// Devuelve { 'yyyy-MM-dd': peso } con la PRIMERA medición de cada día.
function pesosWithings_() {
  const tz = SpreadsheetApp.getActive().getSpreadsheetTimeZone();
  const ahora = Math.floor(Date.now() / 1000);
  const desde = ahora - (DAYS_BACK + 2) * 86400;
  const res = UrlFetchApp.fetch(MEASURE_URL, {
    method: 'post',
    headers: { Authorization: 'Bearer ' + tokenValido_() },
    payload: { action: 'getmeas', meastype: 1, category: 1, startdate: desde, enddate: ahora },
    muteHttpExceptions: true,
  });
  const json = JSON.parse(res.getContentText());
  if (json.status !== 0) throw new Error('Withings devolvió error: ' + res.getContentText());

  const primeras = {}; // dia -> {t, kg}
  (json.body.measuregrps || []).forEach(function (g) {
    const m = g.measures.filter(function (x) { return x.type === 1; })[0];
    if (!m) return;
    const kg = Math.round(m.value * Math.pow(10, m.unit) * 10) / 10;
    const dia = Utilities.formatDate(new Date(g.date * 1000), tz, 'yyyy-MM-dd');
    if (!primeras[dia] || g.date < primeras[dia].t) primeras[dia] = { t: g.date, kg: kg };
  });
  const out = {};
  Object.keys(primeras).forEach(function (d) { out[d] = primeras[d].kg; });
  return out;
}

// ====== HOJA ======
const MESES_ = { ene:0, jan:0, feb:1, mar:2, abr:3, apr:3, may:4, jun:5, jul:6, ago:7, aug:7,
                 sep:8, set:8, oct:9, nov:10, dic:11, dec:11 };

function claveDia_(v, tz) {
  if (v instanceof Date) return Utilities.formatDate(v, tz, 'yyyy-MM-dd');
  const m = String(v).trim().match(/^(\d{1,2})[-\/ ]([A-Za-zÁ-úñ]{3})[A-Za-z.]*[-\/ ](\d{4})$/);
  if (!m) return null;
  const mes = MESES_[m[2].toLowerCase()];
  if (mes === undefined) return null;
  const d = new Date(Number(m[3]), mes, Number(m[1]));
  return Utilities.formatDate(d, tz, 'yyyy-MM-dd');
}

// ====== PROCESO PRINCIPAL (esta es la que programa el disparador diario) ======
function sincronizarPeso() {
  const ss = SpreadsheetApp.getActive();
  const sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) throw new Error('No existe la pestaña ' + SHEET_NAME);
  const tz = ss.getSpreadsheetTimeZone();
  const hoy = Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
  const pesos = pesosWithings_();

  const ultima = sh.getLastRow();
  if (ultima < 2) return;
  const rango = sh.getRange(1, 1, ultima, WEIGHT_COL);
  const valores = rango.getValues();

  const anadidos = [];
  for (let i = 0; i < valores.length; i++) {
    const clave = claveDia_(valores[i][DATE_COL - 1], tz);
    if (!clave || clave > hoy) continue;
    const celda = valores[i][WEIGHT_COL - 1];
    if (celda !== '' && celda !== null) continue;      // NUNCA sobrescribir
    if (pesos[clave] === undefined) continue;
    sh.getRange(i + 1, WEIGHT_COL).setValue(pesos[clave]);
    anadidos.push(clave + ': ' + pesos[clave]);
  }
  Logger.log(anadidos.length ? 'Añadidos: ' + anadidos.join(', ') : 'Nada nuevo que añadir');
}

// ====== HISTORIAL COMPLETO DE WITHINGS -> pestaña "Withings" ======
// Una fila por medición, sin límite de filas. El panel de peso de Claude lee esta pestaña.
// Columnas: Fecha y hora | Timestamp | Peso (kg) | Grasa (%) | Masa grasa (kg) | Músculo (kg) | Agua (kg) | Hueso (kg) | grpid | attrib
// attrib es el origen que da Withings (0 báscula, 1 dudosa: quizá otra persona, 2 manual…).
const RAW_SHEET_NAME = 'Withings';
const RAW_HEADERS = ['Fecha y hora', 'Timestamp', 'Peso (kg)', 'Grasa (%)', 'Masa grasa (kg)',
                     'Músculo (kg)', 'Agua (kg)', 'Hueso (kg)', 'grpid', 'attrib'];
// tipo de medida Withings -> columna (índice dentro de RAW_HEADERS)
const RAW_TYPES = { 1: 2, 6: 3, 8: 4, 76: 5, 77: 6, 88: 7 };
const HISTORY_START = 1199145600; // 1 ene 2008: antes de cualquier báscula Withings

// Descarga todas las mediciones entre dos instantes (segundos), paginando con "offset".
function medicionesWithings_(desde, hasta) {
  const grupos = [];
  let offset = null;
  for (let pagina = 0; pagina < 200; pagina++) {
    const payload = {
      action: 'getmeas',
      meastypes: Object.keys(RAW_TYPES).join(','),
      category: 1,                       // solo mediciones reales, no objetivos
      startdate: desde,
      enddate: hasta,
    };
    if (offset !== null) payload.offset = offset;
    const res = UrlFetchApp.fetch(MEASURE_URL, {
      method: 'post',
      headers: { Authorization: 'Bearer ' + tokenValido_() },
      payload: payload,
      muteHttpExceptions: true,
    });
    const json = JSON.parse(res.getContentText());
    if (json.status !== 0) throw new Error('Withings devolvió error: ' + res.getContentText());
    (json.body.measuregrps || []).forEach(function (g) { grupos.push(g); });
    if (!json.body.more) break;
    offset = json.body.offset;
  }
  return grupos;
}

// Convierte grupos de Withings en filas para la pestaña, ordenadas por fecha.
function filasDesdeGrupos_(grupos) {
  const filas = [];
  grupos.forEach(function (g) {
    const fila = [new Date(g.date * 1000), g.date, '', '', '', '', '', '', String(g.grpid), g.attrib];
    let alguna = false;
    g.measures.forEach(function (m) {
      const col = RAW_TYPES[m.type];
      if (col === undefined) return;
      fila[col] = Math.round(m.value * Math.pow(10, m.unit) * 100) / 100;
      alguna = true;
    });
    if (alguna) filas.push(fila);
  });
  filas.sort(function (a, b) { return a[1] - b[1]; });
  return filas;
}

// Prepara (o crea) la pestaña con su cabecera.
function hojaHistorial_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(RAW_SHEET_NAME);
  if (!sh) sh = ss.insertSheet(RAW_SHEET_NAME, ss.getSheets().length);
  sh.getRange(1, 1, 1, RAW_HEADERS.length).setValues([RAW_HEADERS]).setFontWeight('bold');
  sh.setFrozenRows(1);
  return sh;
}

// EJECUTAR UNA VEZ (o cuando quieras rehacerla): descarga todo el historial y reescribe la pestaña.
function descargarHistorialCompleto() {
  const sh = hojaHistorial_();
  const filas = filasDesdeGrupos_(medicionesWithings_(HISTORY_START, Math.floor(Date.now() / 1000)));
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, RAW_HEADERS.length).clearContent();
  if (filas.length) {
    sh.getRange(2, 1, filas.length, RAW_HEADERS.length).setValues(filas);
    sh.getRange(2, 1, filas.length, 1).setNumberFormat('yyyy-mm-dd hh:mm');
  }
  Logger.log('Historial descargado: ' + filas.length + ' mediciones' + (filas.length ? ' desde ' +
    Utilities.formatDate(filas[0][0], SpreadsheetApp.getActive().getSpreadsheetTimeZone(), 'yyyy-MM-dd') : ''));
}

// DIARIA: añade al final de la pestaña las mediciones nuevas (sin duplicar por grpid).
function actualizarHistorialWithings() {
  const sh = hojaHistorial_();
  const ultima = sh.getLastRow();
  if (ultima < 2) { descargarHistorialCompleto(); return; }
  const existentes = sh.getRange(2, 2, ultima - 1, 8).getValues(); // Timestamp .. grpid
  const ids = {};
  let maxTs = 0;
  existentes.forEach(function (r) {
    ids[String(r[7])] = true;
    if (Number(r[0]) > maxTs) maxTs = Number(r[0]);
  });
  const desde = Math.max(HISTORY_START, maxTs - 7 * 86400);   // margen de 7 días por sincronizaciones tardías
  const nuevas = filasDesdeGrupos_(medicionesWithings_(desde, Math.floor(Date.now() / 1000)))
    .filter(function (f) { return !ids[f[8]]; });
  if (nuevas.length) {
    sh.getRange(ultima + 1, 1, nuevas.length, RAW_HEADERS.length).setValues(nuevas);
    sh.getRange(ultima + 1, 1, nuevas.length, 1).setNumberFormat('yyyy-mm-dd hh:mm');
  }
  Logger.log(nuevas.length ? 'Historial: ' + nuevas.length + ' mediciones nuevas' : 'Historial: nada nuevo');
}

// La que lanza el disparador diario: rellena "Control Diario" y amplía el historial.
// Si una de las dos falla, la otra se ejecuta igualmente.
function sincronizarTodo() {
  const errores = [];
  try { sincronizarPeso(); } catch (e) { errores.push('Control Diario: ' + e.message); }
  try { actualizarHistorialWithings(); } catch (e) { errores.push('Historial: ' + e.message); }
  try { actualizarActividad_(); } catch (e) { errores.push('Actividad: ' + e.message); }
  try { actualizarSueno_(); } catch (e) { errores.push('Sueño: ' + e.message); }
  try { actualizarCorazon_(); } catch (e) { errores.push('Corazón: ' + e.message); }
  if (errores.length) throw new Error(errores.join(' | '));
}

// Crea el disparador (ejecútala una vez): sincroniza cada 4 horas.
// Sustituye los disparadores anteriores de sincronizarPeso o sincronizarTodo.
function crearDisparador() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    const f = t.getHandlerFunction();
    if (f === 'sincronizarPeso' || f === 'sincronizarTodo') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('sincronizarTodo').timeBased().everyHours(6).create();
  Logger.log('Disparador creado: sincronizarTodo cada 6 horas.');
}

// Sincronización a mano desde la app (la aplicación web solo la puedes abrir tú, con tu cuenta de Google)
function sincronizarDesdeWeb_() {
  const lock = LockService.getScriptLock();
  let ok = true, msg, detalle = '';
  if (!lock.tryLock(60000)) {
    ok = false; msg = 'Ya había una sincronización en marcha. Prueba otra vez en un minuto.';
  } else {
    try {
      const ss = SpreadsheetApp.getActive();
      const filas = function (n) { const s = ss.getSheetByName(n); return s ? s.getLastRow() : 0; };
      const antes = [filas(RAW_SHEET_NAME), filas('Actividad'), filas('Sueño')];
      sincronizarTodo();
      try { const d = []; for (let i = 0; i < 3; i++) d.push(sumarDias_(hoyK_(), -i)); guardarNochesSalud_(d); } catch (e) {} // rehace las últimas noches con lo último que haya llegado de Salud
      SpreadsheetApp.flush();
      const nuevas = [filas(RAW_SHEET_NAME) - antes[0], filas('Actividad') - antes[1], filas('Sueño') - antes[2]];
      const sh = ss.getSheetByName(RAW_SHEET_NAME);
      const u = sh.getRange(sh.getLastRow(), 1, 1, 3).getValues()[0];
      const ult = Utilities.formatDate(u[0], tz_(), 'd/M HH:mm') + ' · ' + String(u[2]).replace('.', ',') + ' kg';
      msg = (nuevas[0] ? nuevas[0] + (nuevas[0] === 1 ? ' pesada nueva' : ' pesadas nuevas') : 'Ninguna pesada nueva en Withings') +
        '. Última pesada: ' + ult + '.';
      detalle = resumenDatos_();
    }
    catch (err) { ok = false; msg = 'Hubo un problema: ' + err.message; }
    finally { lock.releaseLock(); }
  }
  const hora = Utilities.formatDate(new Date(), tz_(), 'HH:mm');
  const html = '<div style="font-family:-apple-system,system-ui,sans-serif;max-width:420px;margin:15vh auto;padding:24px;text-align:center">' +
    '<div style="font-size:48px">' + (ok ? '✓' : '!') + '</div>' +
    '<h2 style="margin:8px 0">' + msg + '</h2>' + detalle +
    '<p style="color:#666">' + hora + (ok ? ' · Vuelve a BodyLens: se actualizará sola en unos segundos.' : '') + '</p></div>';
  return HtmlService.createHtmlOutput(html).setTitle('BodyLens · Sincronizar')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}




// ====== ACTIVIDAD, ENTRENAMIENTOS Y SUEÑO -> pestañas "Actividad", "Entrenamientos" y "Sueño" ======
// Necesitan el permiso user.activity. Los datos vienen de lo que Withings recibe (también de tu Apple Watch).
const V2_MEASURE_URL = 'https://wbsapi.withings.net/v2/measure';
const V2_SLEEP_URL = 'https://wbsapi.withings.net/v2/sleep';
const ACT_SHEET = 'Actividad';
const WO_SHEET = 'Entrenamientos';
const SLEEP_SHEET = 'Sueño';
const ACT_HEADERS = ['Fecha', 'Pasos', 'Distancia (m)', 'Desnivel (m)', 'Actividad suave (min)', 'Actividad moderada (min)',
                     'Actividad intensa (min)', 'Calorías activas', 'Calorías totales', 'FC media', 'FC mínima', 'FC máxima', 'Origen'];
const WO_HEADERS = ['ID', 'Fecha', 'Inicio', 'Fin', 'Duración (min)', 'Tipo', 'Calorías', 'Pasos', 'Distancia (m)',
                    'FC media', 'FC mínima', 'FC máxima', 'Intensidad'];
const SLEEP_HEADERS = ['Fecha', 'Acostarse', 'Levantarse', 'En cama (min)', 'Dormido (min)', 'Ligero (min)', 'Profundo (min)',
                       'REM (min)', 'Despierto (min)', 'Despertares', 'Eficiencia (%)', 'FC media', 'FC mínima', 'Origen', 'Desvelos'];
const SLEEP_FROM = '2020-08-15';   // no hay actividad registrada antes de esta fecha
const WO_TYPES = { 1: 'Caminar', 2: 'Correr', 3: 'Senderismo', 4: 'Patinaje', 5: 'BMX', 6: 'Bicicleta', 7: 'Natación', 8: 'Surf',
  9: 'Kitesurf', 10: 'Windsurf', 11: 'Bodyboard', 12: 'Tenis', 13: 'Pimpón', 14: 'Squash', 15: 'Bádminton', 16: 'Pesas',
  17: 'Calistenia', 18: 'Elíptica', 19: 'Pilates', 20: 'Baloncesto', 21: 'Fútbol', 22: 'Fútbol americano', 23: 'Rugby',
  24: 'Voleibol', 25: 'Waterpolo', 26: 'Hípica', 27: 'Golf', 28: 'Yoga', 29: 'Baile', 30: 'Boxeo', 31: 'Esgrima', 32: 'Lucha',
  33: 'Artes marciales', 34: 'Esquí', 35: 'Snowboard', 36: 'Otro', 187: 'Remo', 188: 'Zumba', 191: 'Béisbol', 192: 'Balonmano',
  193: 'Hockey', 194: 'Hockey sobre hielo', 195: 'Escalada', 196: 'Patinaje sobre hielo', 272: 'Multideporte',
  306: 'Caminar en interior', 307: 'Correr en interior', 308: 'Bicicleta en interior' };

function llamarV2_(url, payload) {
  const res = UrlFetchApp.fetch(url, { method: 'post', headers: { Authorization: 'Bearer ' + tokenValido_() }, payload: payload, muteHttpExceptions: true });
  const json = JSON.parse(res.getContentText());
  if (json.status !== 0) throw new Error('Withings devolvió error: ' + res.getContentText().slice(0, 300));
  return json.body;
}
function todasLasPaginas_(url, base, clave) {
  const out = [];
  let offset = null;
  for (let i = 0; i < 100; i++) {
    const p = Object.assign({}, base);
    if (offset !== null) p.offset = offset;
    const b = llamarV2_(url, p);
    (b[clave] || []).forEach(function (x) { out.push(x); });
    if (!b.more) break;
    offset = b.offset;
  }
  return out;
}
function tz_() { return SpreadsheetApp.getActive().getSpreadsheetTimeZone(); }
function hojaCon_(nombre, cabecera) {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(nombre);
  if (!sh) sh = ss.insertSheet(nombre, ss.getSheets().length);
  sh.getRange(1, 1, 1, cabecera.length).setValues([cabecera]).setFontWeight('bold');
  sh.setFrozenRows(1);
  return sh;
}
function leerFilas_(sh, cabecera, colClave) {
  const out = {};
  const n = sh.getLastRow() - 1;
  if (n < 1) return out;
  const tz = tz_();
  sh.getRange(2, 1, n, cabecera.length).getValues().forEach(function (r) {
    const v = r[colClave];
    const k = v instanceof Date ? Utilities.formatDate(v, tz, 'yyyy-MM-dd') : String(v);
    if (k) out[k] = r;
  });
  return out;
}
// Mezcla filas nuevas con las de la pestaña y la reescribe ordenada (por la columna colOrden),
// con bloqueo para no pisar otra ejecución que esté escribiendo a la vez.
function guardarFilas_(nombre, cabecera, colClave, nuevas, formatos, colOrden, mezcla, quitar) {
  const lock = LockService.getScriptLock();
  lock.waitLock(60000);
  try {
    const sh = hojaCon_(nombre, cabecera);
    const filas = leerFilas_(sh, cabecera, colClave);
    Object.keys(nuevas).forEach(function (k) { const v = mezcla ? mezcla(filas[k], nuevas[k], k) : nuevas[k]; if (v) filas[k] = v; });
    if (quitar) Object.keys(filas).forEach(function (k) { if (!nuevas[k] && quitar(filas[k])) delete filas[k]; });
    const co = colOrden == null ? colClave : colOrden;
    const val = function (r) { const v = r[co]; return v instanceof Date ? v.getTime() : String(v); };
    const datos = Object.keys(filas).map(function (k) { return filas[k]; })
      .sort(function (a, b) { const x = val(a), y = val(b); return x < y ? -1 : x > y ? 1 : 0; });
    if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, cabecera.length).clearContent();
    if (datos.length) {
      const nC = cabecera.length; datos.forEach(function (r, i) { if (r.length < nC) datos[i] = r.concat(new Array(nC - r.length).fill('')); else if (r.length > nC) datos[i] = r.slice(0, nC); });
      sh.getRange(2, 1, datos.length, cabecera.length).setValues(datos);
      (formatos || []).forEach(function (f) { sh.getRange(2, f[0], datos.length, 1).setNumberFormat(f[1]); });
    }
    return datos.length;
  } finally { lock.releaseLock(); }
}
function fechaComoDia_(k) { return Utilities.parseDate(k + ' 12:00', tz_(), 'yyyy-MM-dd HH:mm'); }
function sumarDias_(k, n) { const d = fechaComoDia_(k); d.setTime(d.getTime() + n * 86400000); return Utilities.formatDate(d, tz_(), 'yyyy-MM-dd'); }
function hoyK_() { return Utilities.formatDate(new Date(), tz_(), 'yyyy-MM-dd'); }
const r1_ = function (x) { return x == null ? '' : Math.round(x * 10) / 10; };

// --- Actividad diaria ---
function filasActividad_(acts) {
  const porDia = {};
  acts.forEach(function (a) {   // si un día llega de dos fuentes, se queda la de más pasos
    const cur = porDia[a.date];
    if (!cur || (a.steps || 0) > (cur.steps || 0) || ((a.steps || 0) === (cur.steps || 0) && a.hr_average && !cur.hr_average)) porDia[a.date] = a;
  });
  const out = {};
  Object.keys(porDia).forEach(function (k) {
    const a = porDia[k];
    out[k] = [fechaComoDia_(k), a.steps || 0, Math.round(a.distance || 0), r1_(a.elevation || 0), Math.round((a.soft || 0) / 60),
      Math.round((a.moderate || 0) / 60), Math.round((a.intense || 0) / 60), Math.round(a.calories || 0), Math.round(a.totalcalories || 0),
      a.hr_average || '', a.hr_min || '', a.hr_max || '', a.model || ''];
  });
  return out;
}
function descargarActividad_(desde, hasta) {
  return todasLasPaginas_(V2_MEASURE_URL, { action: 'getactivity', startdateymd: desde, enddateymd: hasta,
    data_fields: 'steps,distance,elevation,soft,moderate,intense,active,calories,totalcalories,hr_average,hr_min,hr_max' }, 'activities');
}
// --- Entrenamientos ---
function filasEntrenamientos_(ws) {
  const out = {};
  ws.forEach(function (w) {
    const d = w.data || {};
    const dur = Math.max(0, (w.enddate - w.startdate - (d.pause_duration || 0)) / 60);
    out[String(w.id)] = [String(w.id), fechaComoDia_(w.date), new Date(w.startdate * 1000), new Date(w.enddate * 1000), Math.round(dur),
      WO_TYPES[w.category] || ('Tipo ' + w.category), Math.round(d.calories || 0), d.steps || '', Math.round(d.distance || 0) || '',
      d.hr_average || '', d.hr_min || '', d.hr_max || '', d.intensity || ''];
  });
  return out;
}
function descargarEntrenamientos_(desde, hasta) {
  return todasLasPaginas_(V2_MEASURE_URL, { action: 'getworkouts', startdateymd: desde, enddateymd: hasta }, 'series');
}
// --- Sueño: se mira el día entero, sin huecos: del día k van las 24 horas que acaban a las 17:00 del día k ---
// Se queda con la fuente que más sueño registra y junta los ratos de sueño en episodios (separados por más de 90 min despierto).
// El episodio más largo (de 1 h o más) es la noche del día k; los demás son siestas o ratos de sueño por la tarde-noche
// y van a la pestaña «Siestas», cada uno con su hora de inicio y fin.
const SIESTA_SHEET = 'Siestas';
const SIESTA_HEADERS = ['ID', 'Fecha', 'Inicio', 'Fin', 'Dormido (min)', 'Profundo (min)', 'REM (min)', 'FC media', 'Origen'];
const SIESTA_FMT = [[3, 'yyyy-mm-dd hh:mm'], [4, 'yyyy-mm-dd hh:mm']];
function suenoDia_(k) {
  const fin = Math.floor(Utilities.parseDate(k + ' 17:00', tz_(), 'yyyy-MM-dd HH:mm').getTime() / 1000);
  const b = llamarV2_(V2_SLEEP_URL, { action: 'get', startdate: fin - 24 * 3600, enddate: fin, data_fields: 'hr' });
  const segs = (b.series || []).filter(function (s) { return s.startdate >= fin - 24 * 3600 - 6 * 3600; });
  if (!segs.length) return null;
  const porFuente = {};
  segs.forEach(function (s) { const f = s.model_id || s.model || 'x'; (porFuente[f] || (porFuente[f] = [])).push(s); });
  let mejor = null, mejorSueno = -1;
  Object.keys(porFuente).forEach(function (f) {
    const t = porFuente[f].reduce(function (a, s) { return a + (s.state > 0 ? s.enddate - s.startdate : 0); }, 0);
    if (t > mejorSueno) { mejorSueno = t; mejor = porFuente[f]; }
  });
  mejor.sort(function (a, c) { return a.startdate - c.startdate; });
  const dormidos = mejor.filter(function (s) { return s.state > 0; });
  if (!dormidos.length) return null;
  const eps = []; let ep = null;
  dormidos.forEach(function (s) {
    if (!ep || s.startdate - ep.fin > 90 * 60) { ep = { ini: s.startdate, fin: s.enddate, sueno: 0 }; eps.push(ep); }
    ep.fin = Math.max(ep.fin, s.enddate); ep.sueno += s.enddate - s.startdate;
  });
  const principal = eps.reduce(function (a, e) { return e.sueno > a.sueno ? e : a; });
  const fuente = mejor[0].model || '';
  const fases = function (e) {
    const dentro = mejor.filter(function (s) { return s.startdate >= e.ini && s.enddate <= e.fin; });
    let ligero = 0, profundo = 0, rem = 0, otro = 0, despiertoSegs = 0; const fc = [];
    dentro.forEach(function (s) {
      const d = s.enddate - s.startdate;
      if (s.state === 1) ligero += d; else if (s.state === 2) profundo += d; else if (s.state === 3) rem += d; else if (s.state > 3) otro += d;
      else despiertoSegs++;
      if (s.state > 0 && s.hr) Object.keys(s.hr).forEach(function (t) { fc.push(s.hr[t]); });
    });
    const enCama = e.fin - e.ini, dormido = Math.min(enCama, ligero + profundo + rem + otro);
    return { enCama: enCama, dormido: dormido, ligero: ligero + otro, profundo: profundo, rem: rem, desp: despiertoSegs,
      fcMedia: fc.length ? Math.round(fc.reduce(function (a, x) { return a + x; }, 0) / fc.length) : '', fcMin: fc.length ? Math.min.apply(null, fc) : '' };
  };
  let fila = null;
  if (principal.sueno >= 3600) {
    const f = fases(principal);
    fila = [fechaComoDia_(k), new Date(principal.ini * 1000), new Date(principal.fin * 1000), Math.round(f.enCama / 60), Math.round(f.dormido / 60),
      Math.round(f.ligero / 60), Math.round(f.profundo / 60), Math.round(f.rem / 60), Math.round((f.enCama - f.dormido) / 60),
      f.desp, Math.round(f.dormido / f.enCama * 100), f.fcMedia, f.fcMin, fuente];
  }
  const siestas = {};
  eps.forEach(function (e) {
    if ((fila && e === principal) || e.sueno < 10 * 60) return; // los ratos de menos de 10 minutos no cuentan
    const f = fases(e), dia = Utilities.formatDate(new Date(e.ini * 1000), tz_(), 'yyyy-MM-dd');
    siestas[String(e.ini)] = [String(e.ini), fechaComoDia_(dia), new Date(e.ini * 1000), new Date(e.fin * 1000), Math.round(f.dormido / 60),
      Math.round(f.profundo / 60), Math.round(f.rem / 60), f.fcMedia, fuente];
  });
  return { fila: fila, siestas: siestas };
}
// Compatibilidad: la noche principal del día k
function nocheSueno_(k) { const r = suenoDia_(k); return r ? r.fila : null; }
const SLEEP_FMT = [[2, 'yyyy-mm-dd hh:mm'], [3, 'yyyy-mm-dd hh:mm']];
const WO_FMT = [[3, 'yyyy-mm-dd hh:mm'], [4, 'yyyy-mm-dd hh:mm']];

// EJECUTAR UNA VEZ: descarga toda la actividad diaria y todos los entrenamientos.
function descargarActividadCompleta() {
  const hasta = hoyK_();
  const nA = guardarFilas_(ACT_SHEET, ACT_HEADERS, 0, filasActividad_(descargarActividad_('2008-01-01', hasta)));
  const nW = guardarFilas_(WO_SHEET, WO_HEADERS, 0, filasEntrenamientos_(descargarEntrenamientos_('2008-01-01', hasta)), WO_FMT, 2);
  Logger.log('Actividad: ' + nA + ' días. Entrenamientos: ' + nW + ' sesiones.');
}
// Rellena el historial de sueño hacia atrás, noche a noche, en tandas de 4,5 minutos.
function rellenarSueno() {
  const p = PropertiesService.getScriptProperties();
  if (p.getProperty('SUENO_COMPLETO')) { borrarDisparador_('rellenarSueno'); return; }
  const gen = p.getProperty('SUENO_GEN') || '';
  let cursor = p.getProperty('SUENO_CURSOR') || hoyK_();
  const nuevas = {}, siestasT = {};
  const t0 = Date.now();
  let noches = 0;
  while (cursor >= SLEEP_FROM && Date.now() - t0 < 270000) {
    const r = suenoDia_(cursor);
    if (r) { if (r.fila) { nuevas[cursor] = r.fila; noches++; } Object.assign(siestasT, r.siestas); }
    cursor = sumarDias_(cursor, -1);
    Utilities.sleep(400);
  }
  const total = guardarFilas_(SLEEP_SHEET, SLEEP_HEADERS, 0, nuevas, SLEEP_FMT, null, mezclaWithings_(13));
  guardarFilas_(SIESTA_SHEET, SIESTA_HEADERS, 0, siestasSinSalud_(siestasT), SIESTA_FMT, 2);
  if ((p.getProperty('SUENO_GEN') || '') !== gen) { Logger.log('Relleno reiniciado mientras corría esta tanda: no se mueve el cursor.'); return; }
  if (cursor < SLEEP_FROM) {
    p.setProperty('SUENO_COMPLETO', '1');
    p.deleteProperty('SUENO_CURSOR');
    borrarDisparador_('rellenarSueno');
    Logger.log('Sueño completo: ' + total + ' noches en total.');
  } else {
    p.setProperty('SUENO_CURSOR', cursor);
    Logger.log('Sueño: ' + noches + ' noches nuevas en esta tanda (' + total + ' en total); sigue desde ' + cursor + '.');
  }
}
// EJECUTAR UNA VEZ: programa el relleno del sueño cada 10 minutos hasta terminar (se borra solo) y lanza la primera tanda.
function programarRellenoSueno() {
  borrarDisparador_('rellenarSueno');
  ScriptApp.newTrigger('rellenarSueno').timeBased().everyMinutes(10).create();
  rellenarSueno();
}
// EJECUTAR UNA VEZ si cambia el cálculo de la noche: vuelve a calcular todo el historial de sueño, de hoy hacia atrás.
// Solo reprograma el disparador; la primera tanda empieza a los 10 minutos.
function reiniciarRellenoSueno() {
  const p = PropertiesService.getScriptProperties();
  p.setProperty('SUENO_GEN', String(Date.now()));
  p.deleteProperty('SUENO_CURSOR'); p.deleteProperty('SUENO_COMPLETO');
  borrarDisparador_('rellenarSueno');
  ScriptApp.newTrigger('rellenarSueno').timeBased().everyMinutes(10).create();
  Logger.log('Relleno del sueño reiniciado: la primera tanda empieza en unos 10 minutos.');
}
function borrarDisparador_(fn) {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === fn) ScriptApp.deleteTrigger(t); });
}
// --- Actualización periódica (la llama sincronizarTodo) ---
function actualizarActividad_() {
  const hasta = hoyK_(), desde = sumarDias_(hasta, -10);
  guardarFilas_(ACT_SHEET, ACT_HEADERS, 0, filasActividad_(descargarActividad_(desde, hasta)), null, null, mezclaWithings_(12));
  guardarFilas_(WO_SHEET, WO_HEADERS, 0, sinCopiasDeSalud_(filasEntrenamientos_(descargarEntrenamientos_(sumarDias_(hasta, -14), hasta))), WO_FMT, 2);
}
function actualizarSueno_() {
  const nuevas = {}, siestas = {};
  for (let i = 0; i < 3; i++) {
    const k = sumarDias_(hoyK_(), -i); const r = suenoDia_(k);
    if (r) { if (r.fila) nuevas[k] = r.fila; Object.assign(siestas, r.siestas); }
  }
  // hoy hasta mañana a las 17:00: recoge también la siesta o el rato de sueño de esta tarde-noche
  const rm = suenoDia_(sumarDias_(hoyK_(), 1)); if (rm) Object.assign(siestas, rm.siestas);
  guardarFilas_(SLEEP_SHEET, SLEEP_HEADERS, 0, nuevas, SLEEP_FMT, null, mezclaWithings_(13));
  guardarFilas_(SIESTA_SHEET, SIESTA_HEADERS, 0, siestasSinSalud_(siestas), SIESTA_FMT, 2);
}


// ===================== Recuperar notas históricas del historial de versiones =====================
// Recorre las versiones antiguas de esta hoja (Archivo → Historial de versiones), saca de cada una las filas
// de la pestaña de control con notas del día y las junta en la pestaña «Notas históricas». No toca nada más.
const NOTAS_SHEET = 'Notas históricas';
const NOTAS_HEADERS = ['Fecha', 'Comentarios', 'Desayuno [0..5]', 'Almuerzo [0..5]', 'Cena [0..5]', 'Agua [0..5]', 'Deporte [0..5]',
  'Pecados (comidas) [-5..0]', 'Pecados (bebidas) [-5..0]', 'Versión'];

function versionesHoja_() {
  DriveApp.getFileById(SpreadsheetApp.getActive().getId()); // pide el permiso de Drive
  const id = SpreadsheetApp.getActive().getId(), tok = ScriptApp.getOAuthToken();
  let out = [], page = '';
  do {
    const url = 'https://www.googleapis.com/drive/v3/files/' + id + '/revisions?pageSize=1000&fields=nextPageToken,revisions(id,modifiedTime)' + (page ? '&pageToken=' + page : '');
    const r = JSON.parse(UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + tok } }).getContentText());
    out = out.concat(r.revisions || []); page = r.nextPageToken;
  } while (page);
  return out;
}

function csvVersion_(rev, gid) {
  const id = SpreadsheetApp.getActive().getId();
  const url = 'https://docs.google.com/spreadsheets/d/' + id + '/export?format=csv&gid=' + gid + '&revision=' + rev;
  // Google limita las descargas seguidas (error 429): se espera y se reintenta
  for (let i = 0; i < 5; i++) {
    const res = UrlFetchApp.fetch(url, { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true });
    const c = res.getResponseCode();
    if (c === 200) return Utilities.parseCsv(res.getContentText());
    if (c !== 429 && c < 500) return null;
    Utilities.sleep(3000 * Math.pow(2, i));
  }
  return undefined; // sin respuesta tras varios intentos

}

// prueba: cuántas versiones hay y si se puede leer la más antigua
function probarHistorialNotas() {
  const revs = versionesHoja_();
  Logger.log('Versiones: ' + revs.length + (revs.length ? ' · de ' + revs[0].modifiedTime + ' a ' + revs[revs.length - 1].modifiedTime : ''));
  const gids = SpreadsheetApp.getActive().getSheets().map(s => s.getName() + '=' + s.getSheetId());
  Logger.log('Pestañas: ' + gids.join(', '));
  const sh = SpreadsheetApp.getActive().getSheetByName(SHEET_NAME);
  const mid = revs[Math.floor(revs.length / 2)];
  const csv = csvVersion_(mid.id, sh.getSheetId());
  Logger.log('Versión ' + mid.id + ' (' + mid.modifiedTime + '): ' + (csv ? csv.length + ' filas' : 'no se pudo leer'));
  if (csv) csv.slice(12, 22).forEach(r => Logger.log(r.slice(0, 16).join(' | ')));
  const id = SpreadsheetApp.getActive().getId(), H = { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true };
  const info = JSON.parse(UrlFetchApp.fetch('https://www.googleapis.com/drive/v3/files/' + id + '/revisions/' + mid.id + '?fields=*', H).getContentText());
  Logger.log(JSON.stringify(info).slice(0, 1500));
  Object.keys(info.exportLinks || {}).forEach(k => { const r = UrlFetchApp.fetch(info.exportLinks[k], H); Logger.log(k + ' → ' + r.getResponseCode() + ' · ' + r.getBlob().getBytes().length + ' bytes'); });
  const r2 = UrlFetchApp.fetch('https://docs.google.com/spreadsheets/export?id=' + id + '&revision=' + mid.id + '&exportFormat=csv&gid=' + sh.getSheetId(), H);
  Logger.log('csv gid → ' + r2.getResponseCode() + ' ' + r2.getContentText().slice(0, 200));
}

function diaDeCelda_(v) {
  v = String(v || '').trim(); if (!v) return null; let m;
  if ((m = v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})/))) { let y = +m[3]; if (y < 100) y += 2000; return y + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2); }
  if ((m = v.match(/^(\d{4})-(\d{2})-(\d{2})/))) return m[1] + '-' + m[2] + '-' + m[3];
  const t = v.toLowerCase().replace(/\./g, '').match(/(\d{1,2})[\s-]*(?:de\s+)?([a-zñ]{3})[a-zñ]*[\s-]*(?:de\s+)?(\d{2,4})/);
  if (t && MESES_[t[2]] != null) { let y = +t[3]; if (y < 100) y += 2000; return y + '-' + ('0' + (MESES_[t[2]] + 1)).slice(-2) + '-' + ('0' + t[1]).slice(-2); }
  return null;
}

// extrae las filas con notas de un CSV de la pestaña de control
function notasDeCsv_(csv) {
  const out = {};
  for (let i = 0; i < Math.min(csv.length, 40); i++) {
    const r = csv[i].map(c => String(c).trim().toLowerCase());
    const f = r.indexOf('fecha'); if (f < 0 || !r.some(c => /^desayuno/.test(c))) continue;
    const col = re => r.findIndex(c => re.test(c));
    const C = [col(/^comentarios/), col(/^desayuno/), col(/^(almuerzo|comida)/), col(/^cena/), col(/^agua/), col(/^deporte/), col(/^pecados.*comida/), col(/^pecados.*bebida/)];
    for (let j = i + 1; j < csv.length; j++) {
      const row = csv[j], k = diaDeCelda_(row[f]); if (!k) continue;
      const vals = C.map((c, x) => { if (c < 0) return ''; const v = String(row[c] || '').trim(); if (!v || v === '---') return '';
        if (x === 0) return v; const n = parseFloat(v.replace(',', '.')); return isNaN(n) ? '' : n; });
      if (vals.slice(1).some(v => v !== '')) out[k] = vals; // solo días con alguna nota (no basta un comentario)
    }
    break;
  }
  return out;
}

// recorre las versiones (la última de cada día), de la más reciente a la más antigua; se puede ejecutar varias veces:
// si se acaba el tiempo, guarda por dónde iba y la siguiente ejecución continúa
function recuperarNotasHistoricas() {
  const t0 = Date.now(), props = PropertiesService.getScriptProperties();
  const ss = SpreadsheetApp.getActive(), gids = [ss.getSheetByName(SHEET_NAME).getSheetId()]; // solo la pestaña de control (la de 2013 ya se importa aparte)
  const porDia = {}; versionesHoja_().forEach(r => { porDia[r.modifiedTime.slice(0, 10)] = r; });
  const revs = Object.keys(porDia).sort().reverse().map(d => porDia[d]);
  const hechas = JSON.parse(props.getProperty('notasRevsHechas') || '[]'), set = new Set(hechas);
  const sh = hojaCon_(NOTAS_SHEET, NOTAS_HEADERS), datos = {};
  const prev = leerFilas_(sh, NOTAS_HEADERS, 0); Object.keys(prev).forEach(k => { const d = diaDeCelda_(k); if (d) datos[d] = prev[k]; });
  let nuevas = 0, leidas = 0, fallo = false;
  for (const rev of revs) {
    if (set.has(rev.id)) continue;
    if (Date.now() - t0 > 4.5 * 60 * 1000) break;
    for (const gid of gids) {
      const csv = csvVersion_(rev.id, gid); if (csv === undefined) { fallo = true; break; } if (!csv) continue;
      Utilities.sleep(1500);
      const n = notasDeCsv_(csv);
      // las versiones más recientes mandan: solo se rellenan días que aún no estén
      for (const k of Object.keys(n)) if (!datos[k]) { datos[k] = [fechaComoDia_(k)].concat(n[k], [rev.modifiedTime.slice(0, 10)]); nuevas++; }
    }
    if (fallo) break;
    set.add(rev.id); leidas++;
  }
  props.setProperty('notasRevsHechas', JSON.stringify([...set]));
  const filas = Object.keys(datos).sort().map(k => { const r = datos[k]; r[0] = fechaComoDia_(k); return r; });
  sh.getRange(2, 1, Math.max(sh.getLastRow() - 1, 1), NOTAS_HEADERS.length).clearContent();
  if (filas.length) { sh.getRange(2, 1, filas.length, NOTAS_HEADERS.length).setValues(filas); sh.getRange(2, 1, filas.length, 1).setNumberFormat('yyyy-mm-dd'); }
  const quedan = revs.filter(r => !set.has(r.id)).length;
  const msg = 'Versiones leídas ahora: ' + leidas + ' · días con notas nuevos: ' + nuevas + ' · total días: ' + filas.length + ' · versiones pendientes: ' + quedan + (quedan ? ' (vuelve a ejecutar)' : ' · terminado');
  Logger.log(msg);
  return msg;
}

function reiniciarNotasHistoricas() {
  PropertiesService.getScriptProperties().deleteProperty('notasRevsHechas');
  const sh = SpreadsheetApp.getActive().getSheetByName(NOTAS_SHEET); if (sh && sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, NOTAS_HEADERS.length).clearContent();
}

// ===================== Pesos de hojas antiguas (Excel y hojas de Google de años anteriores) =====================
// Convierte cada archivo a una copia temporal de Google Sheets, busca columnas de fecha y peso, junta todo en la
// pestaña «Pesos históricos» y manda la copia temporal a la papelera. Los archivos originales no se tocan.
const PESOS_SHEET = 'Pesos históricos';
const PESOS_LOG = [];
function logP_(s) { PESOS_LOG.push(String(s)); Logger.log(s); }
const PESOS_FILES = ['1SufKEJTfNBYKenex9o-e7PBWbseGTFn3', '1M5dBVtfGahRVrc9rY7cq4De7eYIcltSP', '1K5-7ms38MDs31biDghPiGNZJ5V-IDmo-',
  '1PKH9SqXZ9SCf2E1N2XmCUTTKfrtsQMuU', '1JBYVDYB1tUrhTMEG6ww9-bt6v-NbIGHa', '1LKivxMacoTyWi4ZHTvgPrItOcj_BQ3Rg', '1VihMaXIoScaNks5tbaL9kCPfhx0dv7ZN',
  '1dvE526mhETpLJNsuxRxnlX-M51Y5e5v3', '1ErNK-ElonGaY-z_SUrvonmEf_Ux7uNHgAORbx1jra6I'];

function pesosDeHoja_(ss, nombre, out) {
  const tz = tz_();
  ss.getSheets().forEach(sh => {
    if (/semanal|gr[aá]fico/i.test(sh.getName())) return;
    const v = sh.getDataRange().getValues(); if (!v.length) return;
    // columnas candidatas: la de fechas y la de peso (cabecera «peso…» o, si no hay, la primera numérica entre 40 y 250 junto a la fecha)
    let hr = -1, fc = -1, pc = -1;
    for (let i = 0; i < Math.min(v.length, 40) && hr < 0; i++) {
      const r = v[i].map(c => String(c).trim().toLowerCase());
      const f = r.findIndex(c => c === 'fecha' || c === 'date' || c === 'día' || c === 'dia');
      const p = r.findIndex(c => /^peso/.test(c) && !/noche/.test(c));
      if (f >= 0 && p >= 0) { hr = i; fc = f; pc = p; }
    }
    if (hr < 0) return;
    let n = 0;
    for (let i = hr + 1; i < v.length; i++) {
      const d = v[i][fc], w = parseFloat(String(v[i][pc]).replace(',', '.'));
      if (!(d instanceof Date) || isNaN(w) || w < 40 || w > 250) continue;
      const k = Utilities.formatDate(d, tz, 'yyyy-MM-dd');
      if (!out[k]) { out[k] = [d, Math.round(w * 10) / 10, nombre + ' · ' + sh.getName()]; n++; }
    }
    logP_(nombre + ' · ' + sh.getName() + ': ' + n + ' pesadas');
  });
}

function extraerPesosAntiguos() {
  const tok = ScriptApp.getOAuthToken(), out = {};
  for (const id of PESOS_FILES) {
    let tmp = null;
    try {
      const f = DriveApp.getFileById(id), nombre = f.getName();
      let ss;
      if (f.getMimeType() === MimeType.GOOGLE_SHEETS) ss = SpreadsheetApp.openById(id);
      else if (/\.xlsx$/i.test(nombre)) { xlsxHojas_(f.getBlob()).forEach(h => logP_(nombre + ' · ' + h.name + ': ' + pesosDeFilas_(h.rows, nombre, out) + ' pesadas')); continue; }
      else if (/\.xls$/i.test(nombre)) { logP_(nombre + ': formato Excel antiguo (.XLS), no se puede leer desde aquí'); continue; }
      else {
        const res = UrlFetchApp.fetch('https://www.googleapis.com/drive/v3/files/' + id + '/copy', { method: 'post', contentType: 'application/json',
          payload: JSON.stringify({ name: 'tmp ' + nombre, mimeType: 'application/vnd.google-apps.spreadsheet' }), headers: { Authorization: 'Bearer ' + tok }, muteHttpExceptions: true });
        if (res.getResponseCode() !== 200) { logP_(nombre + ': no se pudo convertir (' + res.getResponseCode() + ')'); continue; }
        tmp = JSON.parse(res.getContentText()).id; ss = SpreadsheetApp.openById(tmp);
      }
      pesosDeHoja_(ss, nombre, out);
    } catch (e) { logP_(id + ': ' + e); }
    finally { if (tmp) try { DriveApp.getFileById(tmp).setTrashed(true); } catch (e) {} }
  }
  const cab = ['Fecha', 'Peso (kg)', 'Origen'], sh = hojaCon_(PESOS_SHEET, cab);
  const filas = Object.keys(out).sort().map(k => out[k]);
  if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 3).clearContent();
  if (filas.length) { sh.getRange(2, 1, filas.length, 3).setValues(filas); sh.getRange(2, 1, filas.length, 1).setNumberFormat('yyyy-mm-dd'); }
  logP_('Total: ' + filas.length + ' días con peso' + (filas.length ? ' · de ' + Object.keys(out).sort()[0] + ' a ' + Object.keys(out).sort().pop() : ''));
}

// lee un .xlsx sin convertirlo (descomprime el archivo y lee sus hojas en XML)
function xlsxHojas_(blob) {
  const files = {}; Utilities.unzip(blob.setContentType('application/zip')).forEach(f => { files[f.getName()] = f.getDataAsString('UTF-8'); });
  const unesc = s => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
  const ss = []; const sst = files['xl/sharedStrings.xml'] || '';
  sst.replace(/<si>([\s\S]*?)<\/si>/g, (m, inner) => { let t = ''; inner.replace(/<t[^>]*>([\s\S]*?)<\/t>/g, (m2, x) => { t += x; return ''; }); ss.push(unesc(t)); return ''; });
  const colN = s => s.split('').reduce((n, ch) => n * 26 + ch.charCodeAt(0) - 64, 0) - 1;
  const hojas = [];
  Object.keys(files).filter(n => /^xl\/worksheets\/sheet\d+\.xml$/.test(n)).sort().forEach(n => {
    const rows = [];
    files[n].replace(/<row[^>]*>([\s\S]*?)<\/row>/g, (m, inner) => {
      const r = [];
      inner.replace(/<c r="([A-Z]+)\d+"([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g, (m2, col, attrs, body) => {
        const v = body && (body.match(/<v>([\s\S]*?)<\/v>/) || [])[1]; const isT = body && (body.match(/<t[^>]*>([\s\S]*?)<\/t>/) || [])[1];
        let val = null;
        if (/t="s"/.test(attrs) && v != null) val = ss[+v];
        else if (/t="(str|inlineStr)"/.test(attrs)) val = unesc(isT || v || '');
        else if (v != null) val = +v;
        r[colN(col)] = val; return '';
      });
      rows.push(r); return '';
    });
    hojas.push({ name: n.replace(/^.*\//, ''), rows: rows });
  });
  return hojas;
}

function pesosDeFilas_(rows, nombre, out) {
  let hr = -1, fc = -1, pc = -1;
  for (let i = 0; i < Math.min(rows.length, 40) && hr < 0; i++) {
    const r = (rows[i] || []).map(c => String(c == null ? '' : c).trim().toLowerCase());
    const f = r.findIndex(c => c === 'fecha' || c === 'date' || c === 'día' || c === 'dia');
    const p = r.findIndex(c => /^peso/.test(c) && !/noche/.test(c));
    if (f >= 0 && p >= 0) { hr = i; fc = f; pc = p; }
  }
  if (hr < 0) return 0;
  let n = 0;
  for (let i = hr + 1; i < rows.length; i++) {
    const r = rows[i] || [], d = r[fc], w = parseFloat(String(r[pc]).replace(',', '.'));
    if (typeof d !== 'number' || d < 20000 || d > 60000 || isNaN(w) || w < 40 || w > 250) continue;
    const k = Utilities.formatDate(new Date(Date.UTC(1899, 11, 30) + d * 864e5 + 12 * 3600e3), 'UTC', 'yyyy-MM-dd');
    if (!out[k]) { out[k] = [fechaComoDia_(k), Math.round(w * 10) / 10, nombre]; n++; }
  }
  return n;
}


// ====== CORAZÓN Y FORMA FÍSICA -> pestañas «SpO2 y VO2» y «ECG» ======
// SpO2 (tipo 54) y VO2 máx (tipo 123) vienen de las medidas; los ECG, de /v2/heart (lista + señal de cada registro).
const SALUD_SHEET = 'SpO2 y VO2';
const SALUD_HEADERS = ['Fecha y hora', 'Timestamp', 'SpO2 (%)', 'VO2 máx', 'Grupo'];
const ECG_SHEET = 'ECG';
const ECG_HEADERS = ['Fecha y hora', 'Timestamp', 'FC (lpm)', 'Clasificación', 'Señal ID', 'Muestreo (Hz)', 'Señal (µV)', 'Modelo'];
const HEART_URL = 'https://wbsapi.withings.net/v2/heart';
const ECG_CLASES = { 0: 'Ritmo sinusal normal', 1: 'Fibrilación auricular', 2: 'No concluyente' };
const ECG_FMT = [[1, 'yyyy-mm-dd hh:mm']];

function filasSalud_(desde, hasta) {
  const out = {};
  let offset = null;
  for (let p = 0; p < 100; p++) {
    const payload = { action: 'getmeas', meastypes: '54,123', category: 1, startdate: desde, enddate: hasta };
    if (offset !== null) payload.offset = offset;
    const res = UrlFetchApp.fetch(MEASURE_URL, { method: 'post', headers: { Authorization: 'Bearer ' + tokenValido_() }, payload: payload, muteHttpExceptions: true });
    const json = JSON.parse(res.getContentText());
    if (json.status !== 0) throw new Error('Withings (SpO2/VO2): ' + res.getContentText().slice(0, 200));
    (json.body.measuregrps || []).forEach(function (g) {
      let spo = '', vo = '';
      g.measures.forEach(function (m) {
        const x = m.value * Math.pow(10, m.unit);
        if (m.type === 54) spo = Math.round(x * 10) / 10; else if (m.type === 123) vo = Math.round(x * 10) / 10;
      });
      if (spo !== '' || vo !== '') out[String(g.grpid)] = [new Date(g.date * 1000), g.date, spo, vo, String(g.grpid)];
    });
    if (!json.body.more) break;
    offset = json.body.offset;
  }
  return out;
}

function filasECG_(desde, hasta) {
  const ya = leerFilas_(hojaCon_(ECG_SHEET, ECG_HEADERS), ECG_HEADERS, 1);
  const lista = todasLasPaginas_(HEART_URL, { action: 'list', startdate: desde, enddate: hasta }, 'series');
  const out = {};
  lista.forEach(function (s) {
    if (!s.ecg || !s.ecg.signalid) return;
    const key = String(s.timestamp);
    if (ya[key] && String(ya[key][6] || '').length > 100) return; // ya guardado con su señal
    let senal = '', fs = '';
    try {
      const g = llamarV2_(HEART_URL, { action: 'get', signalid: s.ecg.signalid });
      let sig = g.signal || []; fs = g.sampling_frequency || '';
      const paso = fs > 200 ? Math.round(fs / 150) : 1; // a unos 150 Hz, para que quepa en una celda
      if (paso > 1) { sig = sig.filter(function (x, i) { return i % paso === 0; }); fs = Math.round(fs / paso); }
      senal = sig.join(',');
      if (senal.length > 49000) senal = senal.slice(0, 49000).replace(/,[^,]*$/, '');
      Utilities.sleep(300);
    } catch (e) { Logger.log('ECG ' + key + ': ' + e.message); }
    out[key] = [new Date(s.timestamp * 1000), s.timestamp, s.heart_rate || '', ECG_CLASES[s.ecg.afib] || 'Desconocido', String(s.ecg.signalid), fs, senal, s.model || ''];
  });
  return out;
}

function actualizarCorazon_() {
  const ahora = Math.floor(Date.now() / 1000);
  guardarFilas_(SALUD_SHEET, SALUD_HEADERS, 4, filasSalud_(ahora - 30 * 86400, ahora), ECG_FMT, 1);
  guardarFilas_(ECG_SHEET, ECG_HEADERS, 1, filasECG_(ahora - 60 * 86400, ahora), ECG_FMT, 1);
}

// EJECUTAR UNA VEZ: descarga todo el historial de SpO2, VO2 máx y ECG.
function descargarCorazonCompleto() {
  const ahora = Math.floor(Date.now() / 1000);
  const nS = guardarFilas_(SALUD_SHEET, SALUD_HEADERS, 4, filasSalud_(HISTORY_START, ahora), ECG_FMT, 1);
  const nE = guardarFilas_(ECG_SHEET, ECG_HEADERS, 1, filasECG_(HISTORY_START, ahora), ECG_FMT, 1);
  Logger.log('SpO2 y VO2: ' + nS + ' mediciones. ECG: ' + nE + ' registros.');
}



// ====== APPLE SALUD vía Health Auto Export (automatización «API REST», formato JSON, versión 2) ======
// URL para la app: la de esta aplicación web + ?token=… (ejecuta crearTokenSalud() una vez y copia la URL del registro).
// Guarda las métricas en «Salud» (una fila por métrica y momento), los ECG en «ECG» y los avisos en «Avisos de salud».
const SALUDHK_SHEET = 'Salud';
const SALUDHK_HEADERS = ['Fecha y hora', 'Métrica', 'Valor', 'Mín', 'Máx', 'Unidad', 'Origen', 'Clave'];
const AVISOS_SHEET = 'Avisos de salud';
const AVISOS_HEADERS = ['Inicio', 'Fin', 'Tipo', 'Detalle', 'Clave'];
const REG_SHEET = 'Registros de salud';
const REG_HEADERS = ['Inicio', 'Fin', 'Registro', 'Valor', 'Clave'];
const LOG_RE = /sexual|menstrua|intermenstrual|ovulation|cervical|contracept|pregnan|lactation|basal_body|mindful|alcohol|headache|fatigue|pain|bloating|cramps|nausea|sweats|appetite|mood|symptom|toothbrush|handwashing/;
const HK_MAP = [[/^resting_heart_rate$/, 'rhr'], [/^heart_rate_variability/, 'hrv'], [/oxygen_saturation|^spo2/, 'spo2'], [/^respiratory_rate$/, 'rr'],
  [/^vo2_?max$/, 'vo2'], [/wrist_temperature/, 'temp'], [/breathing_disturbances/, 'bdist'], [/time_in_daylight/, 'day'], [/stand_hour/, 'stand'],
  [/^flights_climbed$/, 'flights'], [/walking_heart_rate/, 'whr'], [/^walking_speed$/, 'wspeed'], [/walking_steadiness/, 'steady'],
  [/cardio_recovery|heart_rate_recovery/, 'hrr']];
const ECG_ES = { 'sinus rhythm': 'Ritmo sinusal', 'atrial fibrillation': 'Fibrilación auricular', 'high heart rate': 'Frec. cardiaca alta',
  'low heart rate': 'Frec. cardiaca baja', 'inconclusive': 'No concluyente', 'poor recording': 'Registro deficiente', 'unrecognized': 'No reconocido' };

function crearTokenSalud() {
  const p = PropertiesService.getScriptProperties();
  let t = p.getProperty('SALUD_TOKEN');
  if (!t) { t = Utilities.getUuid().replace(/-/g, ''); p.setProperty('SALUD_TOKEN', t); }
  Logger.log('URL para Health Auto Export: ' + ScriptApp.getService().getUrl() + '?token=' + t);
}
function fechaHAE_(s) {
  if (!s) return null;
  const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?\s*([+-]\d{2}):?(\d{2})?/);
  if (!m) { const d = new Date(s); return isNaN(d) ? null : d; }
  return new Date(m[1] + '-' + m[2] + '-' + m[3] + 'T' + m[4] + ':' + m[5] + ':' + (m[6] || '00') + m[7] + ':' + (m[8] || '00'));
}
function doPost(e) {
  const p = PropertiesService.getScriptProperties();
  const tok = e && e.parameter && e.parameter.token;
  if (!tok || tok !== p.getProperty('SALUD_TOKEN')) return ContentService.createTextOutput(JSON.stringify({ ok: false, error: 'token' })).setMimeType(ContentService.MimeType.JSON);
  let body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return ContentService.createTextOutput(JSON.stringify({ ok: false, error: 'json' })).setMimeType(ContentService.MimeType.JSON); }
  const d = body.data || body;
  const filas = {}, ecgs = {}, avisos = {}, registros = {};
  const suenoMts = [], diasAct = {};
  // otras listas de la exportación (síntomas, ciclo, estado de ánimo, medicamentos…): un registro por elemento
  Object.keys(d).forEach(function (lista) {
    if (['metrics', 'workouts', 'ecg', 'heartRateNotifications'].indexOf(lista) >= 0 || !Array.isArray(d[lista])) return;
    d[lista].forEach(function (x) {
      const ini = fechaHAE_(x.start || x.date || x.startDate); if (!ini) return;
      const tipo = (lista + (x.name ? ':' + x.name : '')).toLowerCase();
      const animo = /mind|mood/i.test(lista);
      if (animo) try { PropertiesService.getScriptProperties().setProperty('HAE_MUESTRA_ANIMO', JSON.stringify(x).slice(0, 4000)); } catch (e2) {}
      // estado de ánimo: se guarda todo (valencia, tipo, emociones y asociaciones) para los paneles de Íntimo
      const val = animo ? JSON.stringify({ v: x.valence != null ? x.valence : x.value, c: x.valenceClassification || '', k: x.kind || '', l: x.labels || [], a: x.associations || [] })
        : x.severity != null ? x.severity : (x.value != null ? x.value : (x.qty != null ? x.qty : (x.valence != null ? x.valence : 1)));
      const k = tipo + '|' + ini.getTime();
      registros[k] = [ini, fechaHAE_(x.end || x.endDate) || ini, tipo, typeof val === 'object' ? JSON.stringify(val) : val, k];
    });
  });
  (d.metrics || []).forEach(function (mt) {
    const nombre = String(mt.name || '').toLowerCase();
    let clave = nombre;
    for (let i = 0; i < HK_MAP.length; i++) if (HK_MAP[i][0].test(nombre)) { clave = HK_MAP[i][1]; break; }
    if (nombre === 'sleep_analysis') { suenoMts.push(mt); return; }
    const esLog = LOG_RE.test(nombre), horaria = HK_HORARIAS.test(nombre), usada = clave !== nombre || horaria;
    if (horaria) (mt.data || []).forEach(function (x) { const f = fechaHAE_(x.date || x.startDate); if (f) diasAct[Utilities.formatDate(f, tz_(), 'yyyy-MM-dd')] = true; });
    const diario = {};
    (mt.data || []).forEach(function (x) {
      const f = fechaHAE_(x.date || x.startDate); if (!f) return;
      if (esLog) { // registros (actividad sexual, ciclo, síntomas…): uno por momento
        const val = x.qty != null ? x.qty : (x.value != null ? x.value : (x.Avg != null ? x.Avg : 1));
        const k = nombre + '|' + f.getTime();
        registros[k] = [f, fechaHAE_(x.endDate || x.end) || f, nombre, typeof val === 'object' ? JSON.stringify(val) : val, k]; return;
      }
      let val = x.qty != null ? x.qty : (x.Avg != null ? x.Avg : (x.avg != null ? x.avg : null));
      const mn = x.Min != null ? x.Min : (x.min != null ? x.min : ''), mx = x.Max != null ? x.Max : (x.max != null ? x.max : '');
      if (val == null && mn === '') return; // sueño y otras métricas sin valor numérico
      if (usada) { const k = clave + '|' + f.getTime(); filas[k] = [f, clave, val == null ? '' : val, mn, mx, mt.units || '', x.source || '', k]; return; }
      // el resto de métricas se guardan resumidas por día, para que la hoja no crezca sin control
      const dia = Utilities.formatDate(f, tz_(), 'yyyy-MM-dd'), a = diario[dia] || (diario[dia] = { n: 0, s: 0, mn: Infinity, mx: -Infinity });
      const vv = val == null ? Number(mn) : Number(val); a.n++; a.s += vv; a.mn = Math.min(a.mn, mn === '' ? vv : Number(mn)); a.mx = Math.max(a.mx, mx === '' ? vv : Number(mx));
    });
    Object.keys(diario).forEach(function (dia) {
      const a = diario[dia], suma = /count|step|energy|distance|flights|time|minutes|stand|calories|kcal/.test(nombre) || /^(count|kcal|km|m|min|kJ)$/.test(mt.units || '');
      const k = nombre + '|' + dia;
      filas[k] = [fechaComoDia_(dia), nombre, suma ? Math.round(a.s * 100) / 100 : Math.round(a.s / a.n * 100) / 100, a.mn, a.mx, mt.units || '', 'día', k];
    });
  });
  (d.ecg || []).forEach(function (g) {
    const f = fechaHAE_(g.start || g.date); if (!f) return;
    const fs0 = Number(g.samplingFrequency) || 512;
    let sig = (g.voltageMeasurements || []).map(function (x) { return typeof x === 'number' ? x : x.voltage; }).filter(function (x) { return typeof x === 'number'; });
    if (sig.length && Math.max.apply(null, sig.slice(0, 2000).map(Math.abs)) < 0.1) sig = sig.map(function (x) { return x * 1e6; }); // voltios -> µV
    const paso = Math.max(1, Math.round(fs0 / 128)), out = [];
    for (let i = 0; i + paso <= sig.length; i += paso) { let s = 0; for (let j = 0; j < paso; j++) s += sig[i + j]; out.push(Math.round(s / paso)); }
    const cls = String(g.classification || '');
    ecgs[String(Math.floor(f.getTime() / 1000))] = [f, Math.floor(f.getTime() / 1000), g.averageHeartRate || '', ECG_ES[cls.toLowerCase()] || cls, 'hae', Math.round(fs0 / paso), out.join(',').slice(0, 49000), g.source || ''];
  });
  (d.heartRateNotifications || []).forEach(function (n) {
    const ini = fechaHAE_(n.start || n.date), fin = fechaHAE_(n.end) || ini; if (!ini) return;
    const txt = JSON.stringify(n).toLowerCase();
    let tipo = /irregular/.test(txt) ? 'irreg' : /low|baja/.test(txt) ? 'lowhr' : /high|alta/.test(txt) ? 'highhr' : '';
    if (!tipo) { const hr = (n.heartRate || []).map(function (h) { return h.hr || h.qty || h.Avg; }).filter(Number); tipo = hr.length && hr.reduce(function (a, b) { return a + b; }, 0) / hr.length < 60 ? 'lowhr' : 'highhr'; }
    const k = tipo + '|' + ini.getTime();
    avisos[k] = [ini, fin, tipo, n.threshold != null ? 'umbral ' + n.threshold : '', k];
  });
  const n1 = Object.keys(filas).length, n2 = Object.keys(ecgs).length, n3 = Object.keys(avisos).length;
  if (n1) guardarFilas_(SALUDHK_SHEET, SALUDHK_HEADERS, 7, filas, [[1, 'yyyy-mm-dd hh:mm']], 0);
  if (n2) guardarFilas_(ECG_SHEET, ECG_HEADERS, 1, ecgs, ECG_FMT, 1);
  if (n3) guardarFilas_(AVISOS_SHEET, AVISOS_HEADERS, 4, avisos, [[1, 'yyyy-mm-dd hh:mm'], [2, 'yyyy-mm-dd hh:mm']], 0);
  const n4 = Object.keys(registros).length;
  if (n4) guardarFilas_(REG_SHEET, REG_HEADERS, 4, registros, [[1, 'yyyy-mm-dd hh:mm'], [2, 'yyyy-mm-dd hh:mm']], 0);
  // Salud como fuente principal: actividad del día, noches y siestas, entrenamientos
  const extra = {};
  try { extra.actividad = actividadDesdeSalud_(Object.keys(diasAct)); } catch (err) { extra.errorActividad = err.message; }
  try { suenoMts.forEach(function (mt) { const r = suenoDesdeSalud_(mt); extra.noches = (extra.noches || 0) + r.noches; extra.siestas = (extra.siestas || 0) + r.siestas; }); } catch (err) { extra.errorSueno = err.message; }
  try { if (d.workouts) extra.entrenos = entrenosDesdeSalud_(d.workouts); } catch (err) { extra.errorEntrenos = err.message; }
  Logger.log('Salud: ' + JSON.stringify(extra));
  return ContentService.createTextOutput(JSON.stringify(Object.assign({ ok: true, metricas: n1, ecg: n2, avisos: n3, registros: n4 }, extra))).setMimeType(ContentService.MimeType.JSON);
}

// ====== APPLE SALUD COMO FUENTE PRINCIPAL (sueño, siestas, actividad y entrenamientos) ======
// Lo que manda Health Auto Export manda; Withings solo rellena lo que Salud no tiene
// (días u horas sin datos de Salud, y los campos que Salud no mide). Peso y composición siguen viniendo de Withings.
const ORIGEN_SALUD = 'Apple Salud';
// métricas que se guardan hora a hora en «Salud» porque con ellas se calcula el día (actividad) o la noche (pulso)
const HK_HORARIAS = /^(step_count|walking_running_distance|active_energy|basal_energy_burned|apple_exercise_time|heart_rate|flights_climbed)$/;
// fases de sueño de Salud, una fila por tramo (para rehacer la noche aunque llegue en varios envíos)
const FASES_SHEET = 'Sueño Salud (fases)';
const FASES_HEADERS = ['Inicio', 'Fin', 'Fase', 'Origen', 'Clave'];

const esSalud_ = function (fila, col) { return fila && String(fila[col]) === ORIGEN_SALUD; };
const vacio_ = function (v) { return v === '' || v === null || v === undefined; };
const aKcal_ = function (v, u) { return /kj/i.test(u || '') ? v / 4.184 : v; };
const aMetros_ = function (v, u) { u = String(u || '').toLowerCase(); return u === 'km' ? v * 1000 : u === 'mi' ? v * 1609.34 : u === 'ft' ? v * 0.3048 : v; };

// --- Actividad del día a partir de las horas guardadas en «Salud» ---
function actividadDesdeSalud_(dias) {
  if (!dias.length) return 0;
  const sh = SpreadsheetApp.getActive().getSheetByName(SALUDHK_SHEET); if (!sh || sh.getLastRow() < 2) return 0;
  const tz = tz_(), quiero = {}; dias.forEach(function (k) { quiero[k] = true; });
  const A = {};
  sh.getRange(2, 1, sh.getLastRow() - 1, SALUDHK_HEADERS.length).getValues().forEach(function (r) {
    if (!(r[0] instanceof Date) || r[6] === 'día') return;
    const k = Utilities.formatDate(r[0], tz, 'yyyy-MM-dd'); if (!quiero[k]) return;
    const m = String(r[1]), v = Number(r[2]), u = String(r[5] || ''); if (r[2] === '' || isNaN(v)) return;
    const a = A[k] || (A[k] = { pasos: 0, dist: 0, pisos: 0, ejer: 0, act: 0, bas: 0, fc: [], fcMin: [], fcMax: [], hay: false });
    if (m === 'step_count') { a.pasos += v; a.hay = true; }
    else if (m === 'walking_running_distance') a.dist += aMetros_(v, u);
    else if (m === 'flights' || m === 'flights_climbed') a.pisos += v;
    else if (m === 'apple_exercise_time') a.ejer += v;
    else if (m === 'active_energy') { a.act += aKcal_(v, u); a.hay = true; }
    else if (m === 'basal_energy_burned') a.bas += aKcal_(v, u);
    else if (m === 'heart_rate') { a.fc.push(v); if (r[3] !== '') a.fcMin.push(Number(r[3])); if (r[4] !== '') a.fcMax.push(Number(r[4])); }
  });
  const filas = {};
  Object.keys(A).forEach(function (k) {
    const a = A[k]; if (!a.hay) return;
    const media = a.fc.length ? Math.round(a.fc.reduce(function (s, x) { return s + x; }, 0) / a.fc.length) : '';
    filas[k] = [fechaComoDia_(k), Math.round(a.pasos), Math.round(a.dist), a.pisos ? Math.round(a.pisos * 3) : '', '', Math.round(a.ejer) || '', '',
      Math.round(a.act), a.bas ? Math.round(a.act + a.bas) : '', media, a.fcMin.length ? Math.min.apply(null, a.fcMin) : '',
      a.fcMax.length ? Math.max.apply(null, a.fcMax) : '', ORIGEN_SALUD];
  });
  // lo de Salud manda; los campos que Salud no tiene (actividad suave e intensa…) se quedan con lo de Withings
  return Object.keys(filas).length ? guardarFilas_(ACT_SHEET, ACT_HEADERS, 0, filas, null, null, function (viejo, nuevo) {
    if (!viejo) return nuevo;
    return nuevo.map(function (v, i) { return vacio_(v) ? viejo[i] : v; });
  }) : 0;
}

// --- Sueño: guarda los tramos de fases y rehace las noches y siestas de los días tocados ---
function suenoDesdeSalud_(mt) {
  const datos = mt.data || []; if (!datos.length) return { noches: 0, siestas: 0 };
  try { PropertiesService.getScriptProperties().setProperty('HAE_MUESTRA_SUENO', JSON.stringify(datos.slice(-4)).slice(0, 8000)); } catch (e) {}
  const tramos = {}, resumen = [];
  datos.forEach(function (x) {
    const fase = String(x.value || x.stage || '').toLowerCase();
    const ini = fechaHAE_(x.startDate || x.start), fin = fechaHAE_(x.endDate || x.end);
    if (fase && ini && fin) { // formato sin resumir: un tramo por fase
      const f = /deep|profund/.test(fase) ? 'deep' : /rem/.test(fase) ? 'rem' : /core|light|ligero/.test(fase) ? 'core' : /awake|despiert/.test(fase) ? 'awake'
        : /in ?bed|en cama/.test(fase) ? 'inbed' : 'asleep';
      const k = (x.source || '') + '|' + f + '|' + ini.getTime();
      tramos[k] = [ini, fin, f, x.source || '', k];
    } else if (x.sleepStart || x.inBedStart || x.totalSleep != null || x.asleep != null) resumen.push(x); // formato resumido: una entrada por noche
  });
  const dias = {};
  if (Object.keys(tramos).length) {
    // cada envío manda en el tramo de tiempo que cubre de cada app: lo que esa app ya no tiene en ese tramo (porque lo rehízo, como AutoSleep al cerrar la noche) se quita
    const cubre = {};
    Object.keys(tramos).forEach(function (k) { const t = tramos[k], c = cubre[t[3]] || (cubre[t[3]] = [Infinity, -Infinity]); c[0] = Math.min(c[0], t[0].getTime()); c[1] = Math.max(c[1], t[1].getTime()); });
    guardarFilas_(FASES_SHEET, FASES_HEADERS, 4, tramos, [[1, 'yyyy-mm-dd hh:mm'], [2, 'yyyy-mm-dd hh:mm']], 0, null, function (r) {
      const c = cubre[r[3]]; if (!c || !(r[0] instanceof Date)) return false;
      if (r[0].getTime() >= c[0] && r[0].getTime() < c[1]) { dias[diaDeNoche_(r[1] instanceof Date ? r[1] : r[0])] = true; return true; } return false;
    });
    Object.keys(tramos).forEach(function (k) { dias[diaDeNoche_(tramos[k][1])] = true; });
    return guardarNochesSalud_(Object.keys(dias));
  }
  // resumido: no hay tramos, se escribe cada noche tal cual (salvo los días que ya se hicieron con tramos, que son más fieles)
  const conTramos = {}, shF = SpreadsheetApp.getActive().getSheetByName(FASES_SHEET);
  if (shF && shF.getLastRow() > 1) shF.getRange(2, 2, shF.getLastRow() - 1, 1).getValues().forEach(function (r) { if (r[0] instanceof Date) conTramos[diaDeNoche_(r[0])] = true; });
  const noches = {};
  resumen.forEach(function (x) {
    const h = function (v) { return v == null || v === '' ? 0 : Number(v) * 60; }; // vienen en horas
    const ini = fechaHAE_(x.sleepStart || x.inBedStart), fin = fechaHAE_(x.sleepEnd || x.inBedEnd); if (!ini || !fin) return;
    const iniC = fechaHAE_(x.inBedStart) || ini, finC = fechaHAE_(x.inBedEnd) || fin;
    const dormido = h(x.totalSleep != null ? x.totalSleep : x.asleep), core = h(x.core), deep = h(x.deep), rem = h(x.rem), desp = h(x.awake);
    if (dormido < 60) return;
    const k = diaDeNoche_(fin); if (conTramos[k]) return;
    const enCama = Math.max(dormido, (Math.max(fin, finC) - Math.min(ini, iniC)) / 60000), fc = pulsoEntre_(ini, fin);
    noches[k] = [fechaComoDia_(k), ini, fin, Math.round(enCama), Math.round(dormido), Math.round(core || Math.max(0, dormido - deep - rem)), Math.round(deep),
      Math.round(rem), Math.round(desp || enCama - dormido), '', Math.round(dormido / enCama * 100), fc.media, fc.min, ORIGEN_SALUD];
  });
  const n = Object.keys(noches).length;
  if (n) guardarFilas_(SLEEP_SHEET, SLEEP_HEADERS, 0, noches, SLEEP_FMT, null, rellenaHuecos_);
  return { noches: n, siestas: 0 };
}
// la noche del día k es la que acaba entre las 17:00 del día anterior y las 17:00 del día k (igual que con Withings)
function diaDeNoche_(fin) {
  const k = Utilities.formatDate(fin, tz_(), 'yyyy-MM-dd');
  return Number(Utilities.formatDate(fin, tz_(), 'H')) >= 17 ? sumarDias_(k, 1) : k;
}
// pulso medio y mínimo entre dos instantes, con las horas de «heart_rate» guardadas en «Salud»
function pulsoEntre_(ini, fin) {
  const sh = SpreadsheetApp.getActive().getSheetByName(SALUDHK_SHEET); if (!sh || sh.getLastRow() < 2) return { media: '', min: '' };
  const n = Math.min(sh.getLastRow() - 1, 6000), v = [], mn = [];
  sh.getRange(sh.getLastRow() - n + 1, 1, n, 4).getValues().forEach(function (r) {
    if (r[1] !== 'heart_rate' || !(r[0] instanceof Date) || r[0] < ini - 3600000 || r[0] >= fin) return;
    if (r[2] !== '') v.push(Number(r[2])); if (r[3] !== '') mn.push(Number(r[3]));
  });
  return { media: v.length ? Math.round(v.reduce(function (s, x) { return s + x; }, 0) / v.length) : '', min: mn.length ? Math.min.apply(null, mn) : '' };
}
// rehace las noches (y siestas) de los días indicados con los tramos guardados en «Sueño Salud (fases)»
function guardarNochesSalud_(dias) {
  const sh = SpreadsheetApp.getActive().getSheetByName(FASES_SHEET); if (!sh || sh.getLastRow() < 2 || !dias.length) return { noches: 0, siestas: 0 };
  const todos = sh.getRange(2, 1, sh.getLastRow() - 1, FASES_HEADERS.length).getValues().filter(function (r) { return r[0] instanceof Date && r[1] instanceof Date; });
  const noches = {}, siestas = {}, diasHechos = {}, ventanas = [];
  dias.forEach(function (k) {
    const finV = Utilities.parseDate(k + ' 17:00', tz_(), 'yyyy-MM-dd HH:mm').getTime(), iniV = finV - 24 * 3600000;
    const dentro = todos.filter(function (r) { return r[1].getTime() > iniV && r[1].getTime() <= finV; });
    if (!dentro.length) return;
    // horario y tiempo dormido: AutoSleep si lo hay; si no, el reloj; si no, la fuente que más sueño registra (las fases salen del reloj, abajo)
    const porFuente = {};
    dentro.forEach(function (r) { (porFuente[r[3]] || (porFuente[r[3]] = [])).push(r); });
    const dormido_ = function (rs) { return rs.reduce(function (a, r) { return a + (/^(core|deep|rem|asleep)$/.test(r[2]) ? r[1] - r[0] : 0); }, 0); };
    let fuente = null;
    const rango_ = function (f) { return dormido_(porFuente[f]) <= 0 ? -1 : /autosleep/i.test(f) ? 2 : /watch/i.test(f) ? 1 : 0; };
    Object.keys(porFuente).forEach(function (f) {
      if (!fuente || rango_(f) > rango_(fuente) || (rango_(f) === rango_(fuente) && dormido_(porFuente[f]) > dormido_(porFuente[fuente]))) fuente = f;
    });
    // si AutoSleep se queda claramente corto frente al reloj (p. ej. aún no ha cerrado la noche), manda el reloj
    if (fuente && /autosleep/i.test(fuente)) Object.keys(porFuente).forEach(function (f) { if (/watch/i.test(f) && dormido_(porFuente[f]) > dormido_(porFuente[fuente]) * 1.2 + 15 * 60000) fuente = f; });
    const rs = porFuente[fuente].sort(function (a, b) { return a[0] - b[0]; });
    const dormidos = rs.filter(function (r) { return /^(core|deep|rem|asleep)$/.test(r[2]); });
    if (!dormidos.length) return;
    const eps = []; let ep = null;
    dormidos.forEach(function (r) {
      if (!ep || r[0] - ep.fin > 90 * 60000) { ep = { ini: r[0].getTime(), fin: r[1].getTime(), sueno: 0 }; eps.push(ep); }
      ep.fin = Math.max(ep.fin, r[1].getTime()); ep.sueno += r[1] - r[0];
    });
    const fases = function (e) {
      const t = { core: 0, deep: 0, rem: 0, asleep: 0, awake: 0, desp: 0 };
      rs.forEach(function (r) {
        if (r[0].getTime() < e.ini || r[1].getTime() > e.fin) return;
        const d = (r[1] - r[0]) / 60000; if (t[r[2]] != null) t[r[2]] += d; if (r[2] === 'awake') t.desp++;
      });
      return t;
    };
    // ratos de la misma noche separados por un desvelo (hasta 4 h, entre las 19:00 y las 12:00): una sola noche, con el desvelo como tiempo despierto
    const nocturna = function (t) { const hh = Number(Utilities.formatDate(new Date(t), tz_(), 'H')); return hh >= 19 || hh < 12; };
    for (let i = eps.length - 1; i > 0; i--) { const a = eps[i - 1], b = eps[i]; if (b.ini - a.fin <= 4 * 3600000 && nocturna(a.fin) && nocturna(b.ini)) { a.fin = Math.max(a.fin, b.fin); a.sueno += b.sueno; a.cortes = (a.cortes || 0) + 1 + (b.cortes || 0); eps.splice(i, 1); } }
    // la noche del día k tiene que acabar después de las 03:00 de ese día: un rato de sueño por la tarde-noche del día anterior es siesta, no la noche
    const tres = Utilities.parseDate(k + ' 03:00', tz_(), 'yyyy-MM-dd HH:mm').getTime();
    const candidatas = eps.filter(function (e) { return e.fin >= tres; });
    const principal = (candidatas.length ? candidatas : eps).reduce(function (a, e) { return e.sueno > a.sueno ? e : a; });
    diasHechos[k] = true; ventanas.push([iniV, finV]);
    if (principal.sueno >= 3600000 && principal.fin >= tres) {
      const f = fases(principal), enCama = (principal.fin - principal.ini) / 60000, dormido = Math.min(enCama, f.core + f.deep + f.rem + f.asleep);
      // mezcla: si la noche sale de AutoSleep (que no distingue fases), el profundo y el REM los pone el reloj en ese mismo horario
      let fDeep = f.deep, fRem = f.rem;
      const reloj = Object.keys(porFuente).filter(function (x) { return x !== fuente && /watch/i.test(x); })[0];
      if (reloj && !/watch/i.test(fuente)) {
        const t = { deep: 0, rem: 0 };
        porFuente[reloj].forEach(function (r) { const a = Math.max(r[0].getTime(), principal.ini), b = Math.min(r[1].getTime(), principal.fin); if (b > a && t[r[2]] != null) t[r[2]] += (b - a) / 60000; });
        fDeep = Math.min(t.deep, dormido); fRem = Math.min(t.rem, Math.max(0, dormido - fDeep));
      }
      const fc = pulsoEntre_(new Date(principal.ini), new Date(principal.fin));
      noches[k] = [fechaComoDia_(k), new Date(principal.ini), new Date(principal.fin), Math.round(enCama), Math.round(dormido), Math.round(Math.max(0, dormido - fDeep - fRem)),
        Math.round(fDeep), Math.round(fRem), Math.round(enCama - dormido), f.desp + (principal.cortes || 0), Math.round(dormido / enCama * 100), fc.media, fc.min, ORIGEN_SALUD, desvelos_(dormidos, principal, k)];
    }
    eps.forEach(function (e) {
      if ((noches[k] && e === principal) || e.sueno < 10 * 60000) return;
      const f = fases(e), dia = Utilities.formatDate(new Date(e.ini), tz_(), 'yyyy-MM-dd'), fc = pulsoEntre_(new Date(e.ini), new Date(e.fin));
      const id = 'hk' + Math.floor(e.ini / 1000);
      siestas[id] = [id, fechaComoDia_(dia), new Date(e.ini), new Date(e.fin), Math.round(f.core + f.deep + f.rem + f.asleep), Math.round(f.deep), Math.round(f.rem), fc.media, ORIGEN_SALUD];
    });
    // siestas que solo detecta otra app (AutoSleep…): sus ratos de sueño que no se solapan con lo que registró la fuente elegida
    const ocupado = eps.map(function (e) { return [e.ini, e.fin]; });
    Object.keys(porFuente).forEach(function (f2) {
      if (f2 === fuente) return;
      const ds = porFuente[f2].filter(function (r) { return /^(core|deep|rem|asleep)$/.test(r[2]); }).sort(function (a, b) { return a[0] - b[0]; });
      const e2 = []; let p = null;
      ds.forEach(function (r) { if (!p || r[0].getTime() - p.fin > 30 * 60000) { p = { ini: r[0].getTime(), fin: r[1].getTime(), sueno: 0 }; e2.push(p); } p.fin = Math.max(p.fin, r[1].getTime()); p.sueno += r[1] - r[0]; });
      e2.forEach(function (e) {
        if (e.sueno < 10 * 60000 || ocupado.some(function (o) { return e.ini < o[1] + 30 * 60000 && o[0] - 30 * 60000 < e.fin; })) return;
        ocupado.push([e.ini, e.fin]);
        const dia = Utilities.formatDate(new Date(e.ini), tz_(), 'yyyy-MM-dd'), fc = pulsoEntre_(new Date(e.ini), new Date(e.fin)), id = 'hk' + Math.floor(e.ini / 1000);
        siestas[id] = [id, fechaComoDia_(dia), new Date(e.ini), new Date(e.fin), Math.round(e.sueno / 60000), 0, 0, fc.media, ORIGEN_SALUD + ' (' + f2 + ')'];
      });
    });
  });
  const nN = Object.keys(noches).length;
  if (nN) guardarFilas_(SLEEP_SHEET, SLEEP_HEADERS, 0, noches, SLEEP_FMT, null, rellenaHuecos_);
  // las siestas de esos días pasan a ser las de Salud: se quitan las que trajo Withings para los mismos días
  const tz = tz_();
  if (Object.keys(diasHechos).length) guardarFilas_(SIESTA_SHEET, SIESTA_HEADERS, 0, siestas, SIESTA_FMT, 2, null, function (r) {
    // solo se rehacen las siestas que empiezan dentro de las ventanas recalculadas (de 17:00 a 17:00)
    const t0 = r[2] instanceof Date ? r[2].getTime() : null;
    return t0 != null && ventanas.some(function (v) { return t0 > v[0] && t0 <= v[1]; }); // las de esos días se rehacen enteras (las que ya no sean siesta, p. ej. porque pasan a formar parte de la noche, se quitan)
  });
  return { noches: nN, siestas: Object.keys(siestas).length };
}

// --- Entrenamientos de Salud (sustituyen a la copia que trae Withings del mismo entreno) ---
const HK_WO_ES = { walking: 'Caminar', 'outdoor walk': 'Caminar', 'indoor walk': 'Caminar en interior', running: 'Correr', 'outdoor run': 'Correr',
  'indoor run': 'Correr en interior', cycling: 'Bicicleta', 'outdoor cycle': 'Bicicleta', 'indoor cycle': 'Bicicleta en interior', hiking: 'Senderismo',
  swimming: 'Natación', 'pool swim': 'Natación', 'open water swim': 'Natación', yoga: 'Yoga', pilates: 'Pilates', elliptical: 'Elíptica', rowing: 'Remo',
  'traditional strength training': 'Pesas', 'functional strength training': 'Fuerza funcional', 'high intensity interval training': 'HIIT',
  'core training': 'Core', dance: 'Baile', 'stair stepper': 'Escaleras', soccer: 'Fútbol', tennis: 'Tenis', padel: 'Pádel', 'paddle sports': 'Pádel',
  cooldown: 'Enfriamiento', 'mixed cardio': 'Cardio', other: 'Otro' };
function entrenosDesdeSalud_(ws) {
  if (!ws || !ws.length) return 0;
  try { PropertiesService.getScriptProperties().setProperty('HAE_MUESTRA_ENTRENO', JSON.stringify(ws[ws.length - 1]).slice(0, 8000)); } catch (e) {}
  const q = function (o) { return o == null ? null : typeof o === 'number' ? o : o.qty != null ? Number(o.qty) : null; };
  const suma = function (a) { return Array.isArray(a) ? a.reduce(function (s, x) { return s + (q(x) || 0); }, 0) : q(a); };
  const filas = {}, rangos = [];
  ws.forEach(function (w) {
    const ini = fechaHAE_(w.start), fin = fechaHAE_(w.end); if (!ini || !fin) return;
    const id = 'hk-' + (w.id || Math.floor(ini.getTime() / 1000));
    const dur = w.duration != null ? Number(w.duration) / 60 : (fin - ini) / 60000;
    const en = w.activeEnergyBurned || w.activeEnergy, kcal = q(en) != null ? aKcal_(q(en), en.units) : suma(w.activeEnergy);
    const dist = w.distance ? aMetros_(q(w.distance), w.distance.units) : null;
    const hr = w.heartRate || {}, fcMed = q(w.avgHeartRate) || q(hr.avg), fcMax = q(w.maxHeartRate) || q(hr.max), fcMin = q(hr.min);
    const nombre = String(w.name || 'Otro'), tipo = HK_WO_ES[nombre.toLowerCase()] || nombre;
    filas[id] = [id, fechaComoDia_(Utilities.formatDate(ini, tz_(), 'yyyy-MM-dd')), ini, fin, Math.round(dur), tipo, kcal != null ? Math.round(kcal) : '',
      w.stepCount != null ? Math.round(suma(w.stepCount)) || '' : '', dist ? Math.round(dist) : '', fcMed ? Math.round(fcMed) : '', fcMin ? Math.round(fcMin) : '',
      fcMax ? Math.round(fcMax) : '', q(w.intensity) != null ? r1_(q(w.intensity)) : ''];
    rangos.push([ini.getTime(), fin.getTime()]);
  });
  // fuera la copia de Withings del mismo entreno (empieza a menos de 10 minutos de uno de Salud)
  return Object.keys(filas).length ? guardarFilas_(WO_SHEET, WO_HEADERS, 0, filas, WO_FMT, 2, null, function (r) {
    if (String(r[0]).indexOf('hk-') === 0 || !(r[2] instanceof Date)) return false;
    return rangos.some(function (x) { return Math.abs(r[2].getTime() - x[0]) < 10 * 60000; });
  }) : 0;
}
// --- Lo que trae Withings ya no pisa lo de Salud ---
// fila de Withings frente a la que ya hay: si la de la pestaña es de Salud, solo se rellenan sus huecos
function mezclaWithings_(colOrigen) {
  return function (viejo, nuevo) {
    if (viejo && esSalud_(viejo, colOrigen)) return viejo.map(function (v, i) { return vacio_(v) ? nuevo[i] : v; });
    return nuevo;
  };
}
// siestas de Withings: fuera las de los días cuya noche ya viene de Salud (Salud trae sus propias siestas)
function siestasSinSalud_(siestas) {
  const sh = SpreadsheetApp.getActive().getSheetByName(SLEEP_SHEET); if (!sh || sh.getLastRow() < 2) return siestas;
  const tz = tz_(), salud = {};
  sh.getRange(2, 1, sh.getLastRow() - 1, SLEEP_HEADERS.length).getValues().forEach(function (r) {
    if (esSalud_(r, 13) && r[0] instanceof Date) salud[Utilities.formatDate(r[0], tz, 'yyyy-MM-dd')] = true;
  });
  const out = {};
  Object.keys(siestas).forEach(function (k) {
    const r = siestas[k], dia = r[1] instanceof Date ? Utilities.formatDate(r[1], tz, 'yyyy-MM-dd') : String(r[1]);
    if (!salud[dia] && !salud[sumarDias_(dia, 1)]) out[k] = r;
  });
  return out;
}
// entrenos de Withings: fuera los que ya están desde Salud (mismo entreno, empieza a menos de 10 minutos)
function sinCopiasDeSalud_(filas) {
  const sh = SpreadsheetApp.getActive().getSheetByName(WO_SHEET); if (!sh || sh.getLastRow() < 2) return filas;
  const hk = sh.getRange(2, 1, sh.getLastRow() - 1, 3).getValues().filter(function (r) { return String(r[0]).indexOf('hk-') === 0 && r[2] instanceof Date; })
    .map(function (r) { return r[2].getTime(); });
  if (!hk.length) return filas;
  const out = {};
  Object.keys(filas).forEach(function (k) {
    const ini = filas[k][2] instanceof Date ? filas[k][2].getTime() : 0;
    if (!hk.some(function (t) { return Math.abs(t - ini) < 10 * 60000; })) out[k] = filas[k];
  });
  return out;
}

// Resumen para la página de «Actualizar»: lo último que hay de cada tipo de dato y de dónde viene
function resumenDatos_() {
  const ss = SpreadsheetApp.getActive(), tz = tz_(), hoy = hoyK_();
  const ultima = function (nombre, n) { const sh = ss.getSheetByName(nombre); if (!sh || sh.getLastRow() < 2) return null; return sh.getRange(sh.getLastRow(), 1, 1, n).getValues()[0]; };
  const dia = function (d) { return d instanceof Date ? Utilities.formatDate(d, tz, 'yyyy-MM-dd') : String(d); };
  const corto = function (d) { const k = dia(d); return k === hoy ? 'hoy' : k === sumarDias_(hoy, -1) ? 'ayer' : Number(k.slice(8)) + '/' + Number(k.slice(5, 7)); };
  const hm = function (min) { min = Math.round(Number(min) || 0); return Math.floor(min / 60) + ' h ' + ('0' + (min % 60)).slice(-2); };
  const de = function (o) { return String(o) === ORIGEN_SALUD ? 'Apple Salud' : 'Withings'; };
  const filas = [];
  const s = ultima(SLEEP_SHEET, SLEEP_HEADERS.length);
  if (s) filas.push(['Sueño', 'noche de ' + corto(s[0]) + ': ' + hm(s[4]) + ' dormido', de(s[13])]);
  const a = ultima(ACT_SHEET, ACT_HEADERS.length);
  if (a) filas.push(['Actividad', corto(a[0]) + ': ' + Number(a[1] || 0).toLocaleString('es-ES') + ' pasos', de(a[12])]);
  const w = ultima(WO_SHEET, WO_HEADERS.length);
  if (w) filas.push(['Entrenamientos', 'último ' + corto(w[1]) + ': ' + w[5] + ' · ' + w[4] + ' min', String(w[0]).indexOf('hk-') === 0 ? 'Apple Salud' : 'Withings']);
  const shS = ss.getSheetByName(SALUDHK_SHEET);
  if (shS && shS.getLastRow() > 1) {
    let max = null; shS.getRange(Math.max(2, shS.getLastRow() - 3000), 1, Math.min(3000, shS.getLastRow() - 1), 7).getValues().forEach(function (r) { if (r[0] instanceof Date && r[6] !== 'día' && r[0] <= new Date() && (!max || r[0] > max)) max = r[0]; });
    if (max) filas.push(['Salud', 'último dato: ' + corto(max) + ' ' + Utilities.formatDate(max, tz, 'HH:mm'), 'Health Auto Export']);
  }
  if (!filas.length) return '';
  return '<table style="margin:18px auto 0;border-collapse:collapse;font-size:15px;text-align:left">' + filas.map(function (f) {
    return '<tr><td style="padding:6px 10px;color:#666">' + f[0] + '</td><td style="padding:6px 10px"><b>' + f[1] + '</b><br><span style="color:#888;font-size:13px">' + f[2] + '</span></td></tr>';
  }).join('') + '</table>';
}
// lo nuevo de Salud manda, pero los huecos (p. ej. despertares que Salud no da) se quedan con lo que ya había
function rellenaHuecos_(viejo, nuevo) { return viejo ? nuevo.map(function (v, i) { return vacio_(v) ? viejo[i] : v; }) : nuevo; }
// EJECUTAR A MANO si cambia el cálculo: rehace con los tramos guardados las noches y siestas de Salud de los últimos 7 días
function rehacerSuenoSalud() { const d = []; for (let i = 0; i < 7; i++) d.push(sumarDias_(hoyK_(), -i)); Logger.log(JSON.stringify(guardarNochesSalud_(d))); }
// ratos despierto de 10 min o más dentro de la noche, en minutos desde la medianoche del día en que te levantas: «107~318;400~412» (con ~ para que la hoja no lo tome por una fecha)
function desvelos_(dormidos, e, k) {
  const base = Utilities.parseDate(k + ' 00:00', tz_(), 'yyyy-MM-dd HH:mm').getTime(), out = []; let fin = null;
  dormidos.filter(function (r) { return r[0].getTime() >= e.ini && r[1].getTime() <= e.fin; }).sort(function (a, b) { return a[0] - b[0]; }).forEach(function (r) {
    if (fin !== null && r[0].getTime() - fin >= 10 * 60000) out.push(Math.round((fin - base) / 60000) + '~' + Math.round((r[0].getTime() - base) / 60000));
    fin = fin === null ? r[1].getTime() : Math.max(fin, r[1].getTime());
  });
  return out.join(';');
}
