# BodyLens — plan de migración a Docker con actualización cada 15 minutos

Estado de partida: noviembre de 2026. Documento de trabajo para el agente (Codex / Claude Code) y para Jaime.

## 0. Decisiones posteriores (19 nov 2026) — mandan sobre el resto del documento

- **Multiusuario desde el principio.** Cada persona tiene su cuenta (usuario + contraseña argon2, sesión en cookie
  HttpOnly de 90 días) y sus datos separados (`docs.user_id`). **Sin registro abierto**: las cuentas se crean con un
  **enlace de invitación** de un solo uso que genera un administrador en «Tu cuenta» (`/cuenta`) o con
  `python -m app.admin invitacion`. La primera cuenta: `python -m app.admin crear-admin <usuario> "<Nombre>"`.
- **Laura tiene su propia cuenta** (se siembra con `--perfil laura` desde `snap.json`). Los perfiles de la app siguen
  existiendo dentro de cada cuenta.
- **Pareja**: dos cuentas pueden unirse (una lo pide en `/cuenta`, la otra lo acepta). Los registros de **ciclo**
  (`menstrual`, `intermenstrual`, `ovulation`, `bbt`, `cervical`, `contraceptive`, `pregnancy`) y de **intimidad**
  (`sexual`) del documento `hklog` pasan a un documento común de la pareja (`shared_docs`): los dos los ven y los
  editan. Al separarse, cada uno se queda con una copia. Lo resuelve el servidor; la página no cambia.
- **Fase 1 (puente Google) por cuenta**: el ID de la hoja y la URL del Apps Script de cada cuenta los configura **solo
  un administrador** (así nadie puede leer la hoja de otro con la cuenta de servicio). El `fileId` de la página se ignora.
- **Imagen en Docker Hub** (`jaimetur/bodylens`), no en GHCR, como DriveTestAnalyzer. Secretos del repo:
  `DOCKERHUB_USERNAME` (opcional, si no el dueño del repo) y `DOCKERHUB_TOKEN`.
- **Despliegue**: stack de Dockhand en el NAS (`/volume1/docker/stacks/bodylens`), datos en
  `/volume1/docker/data/bodylens`, puerto 7280, y **Caddy** del NAS como proxy HTTPS (no el proxy de DSM).
  Ver `docs/DESPLIEGUE.md`.
- Cambios en la página servida: no se tocan `frontend/src/*.html`; el servidor aplica sustituciones exactas al
  montarla (`backend/app/frontend.py`, cada una comprobada en los tests) y añade `frontend/server/claude-shim.js`.

---

## 1. Cómo funciona hoy

```
Báscula Withings ──(API Withings, cada 6 h o botón)──┐
                                                     ├─► Google Apps Script ─► Hoja «Peso Jaime 2026»
iPhone: Health Auto Export ──(POST cada 5 min)───────┘        (Codigo.gs)          (Google Sheets)
                                                                                         │
                                                       conector Google Drive de claude.ai (export XLSX)
                                                                                         ▼
                                                              Artefacto BodyLens en claude.ai (HTML)
                                                              + espacio de datos del artefacto (db «bascula»)
```

- **Hoja**: ID `1aUMgruI3VycOCjbqH4_UvL8nS8i-mt1QFNiz6xaQx2Q`. Pestañas que lee la app: `Withings`, `Actividad`,
  `Sueño`, `Entrenamientos`, `Siestas`, `SpO2 y VO2`, `ECG`, `Salud`, `Avisos de salud`, `Registros de salud`,
  `Sueño Salud (fases)`, `Notas históricas`, `Pesos históricos`, `Control Diario` (las cabeceras exactas están en
  `legacy/apps-script/Codigo.gs` y el parseo en `frontend/src/app_b.html`).
- **Apps Script** (`legacy/apps-script/Codigo.gs`, ~84 KB): OAuth con Withings y descarga de pesadas, composición,
  actividad, entrenos, sueño, SpO2/VO2, ECG; `doPost` recibe Health Auto Export (métricas por horas, sueño en
  tramos sin resumir, entrenos, ECG, avisos de FC, ciclo, ánimo, síntomas, medicación…) y rehace las noches con
  la **mezcla AutoSleep + Apple Watch**. `doGet?accion=sincronizar` fuerza una sincronización.
  Las credenciales de Withings se han sustituido por `REDACTADO` en la copia del repo.
- **Artefacto**: la página lee la hoja exportada como XLSX a través del conector de Google Drive y guarda lo que
  edita el usuario (ajustes, notas, comidas, medidas, perfiles, entradas manuales…) en el espacio de datos del
  artefacto (colección `bascula`).
- **Problema**: la página solo se actualiza al abrirla o al pulsar «Actualizar» (abre el Apps Script en una
  pestaña), Withings solo se consulta cada 6 h, y todo depende de claude.ai y de Google.

## 2. Cómo debe quedar

```
Báscula Withings ──(API Withings: tarea cada 15 min + webhook opcional)──┐
                                                                         ├─► Servidor BodyLens (Docker)
iPhone: Health Auto Export ──(POST cada 5 min a /api/ingest/hae)─────────┘   FastAPI + SQLite + planificador
                                                                                        │
                                              navegador / iPhone (PWA) ◄── HTTPS (proxy inverso del Synology)
                                              la página se refresca sola cuando cambian los datos
```

Requisitos de Jaime:
1. Desplegar en **su servidor** con Docker (Synology DS920+, x86_64; Container Manager), accesible desde fuera
   por el **proxy inverso del Synology con HTTPS**, como ya hace con PhotoMigrator.
2. **Datos actualizados cada 15 minutos sin pulsar nada.** El botón de actualizar se mantiene para forzarlo.
3. **Mismo diseño y mismas funciones** que el artefacto actual.
4. Repositorio privado en GitHub con **GitHub Actions** que construya la imagen y la publique en Docker Hub.
5. Login propio y **varias cuentas** con invitación (son datos de salud expuestos a internet).

## 3. Arquitectura

### 3.1 Backend
- **Python 3.12, FastAPI, Uvicorn**, `httpx` para llamadas salientes, **SQLite** (modo WAL) en un volumen `/data`.
- **Planificador** dentro del proceso (APScheduler `AsyncIOScheduler`), un solo worker de Uvicorn para que las
  tareas no se dupliquen. Intervalo configurable `SYNC_INTERVAL_MIN` (por defecto **15**).
- Zona horaria `Europe/Madrid` (`TZ` y `zoneinfo`).
- Estructura sugerida:
  ```
  backend/app/main.py          arranque, rutas estáticas, planificador
  backend/app/auth.py          login (una contraseña, cookie de sesión firmada)
  backend/app/docstore.py      almacén de documentos (sustituye al «db» del artefacto)
  backend/app/workbook.py      genera el XLSX que lee la app a partir de las tablas
  backend/app/sources/withings.py   OAuth + descargas (port del Apps Script)
  backend/app/sources/hae.py        ingesta de Health Auto Export (port de doPost)
  backend/app/sleep.py         reglas de sueño (port de guardarNochesSalud_, desvelos_, siestas…)
  backend/app/sync.py          orquesta una sincronización (tarea de 15 min y botón)
  backend/tests/
  ```

### 3.2 Frontend: misma página + capa de compatibilidad
La app usa `window.claude.use(nombre)`. En Docker se sirve la misma página con un **`claude-shim.js`** que
implementa esas capacidades contra la API del servidor, para tocar lo mínimo `app_*.html`:

| Capacidad | Uso en la app | Implementación en Docker |
|---|---|---|
| `user` | `isOwner()`, `id()` | siempre dueño (`true`, id fijo `owner`) tras el login |
| `db` | `collection('bascula')`: `doc(id).get/set/update/delete`, `onSnapshot(cb, err)` con `qs.docs[].id/.data()` y `qs.metadata.fromCache`; `collection('data/users/<id>').get()` (migración antigua: devolver vacío) | REST `GET/PUT/DELETE /api/docs/{coleccion}/{id}`, `GET /api/docs/{coleccion}`; `onSnapshot` = carga inicial + sondeo de `GET /api/docs/{coleccion}?since=<rev>` cada 30 s y al volver a la pestaña |
| `mcp` | `watchTool` / `callTool('Google Drive','download_file_content',{fileId, exportMimeType})` → `{content: base64}` del XLSX | `GET /api/workbook.xlsx` (con `ETag`). `watchTool` sondea `GET /api/workbook/meta` cada 60 s y al recuperar el foco, y vuelve a emitir `{type:'data'}` cuando cambia el ETag → **la página se actualiza sola** |
| `downloads` | `save({filename,data})` (copias JSON, CSV, PDF) | descarga normal del navegador (Blob + `<a download>`) |
| `artifact` | `publish(html)` para guardar la copia de datos dentro de la página | no hace falta: devolver `null` (la app ya contempla `null`) |
| `permissions` | `manage()` | no-op |

Cambios mínimos en `app_*.html` (con un *flag* `window.BODYLENS_SERVER = true` que pone el servidor):
- Botón «Actualizar» (`#pullBtn`, constante `WITHINGS_NOW`): en vez de abrir el Apps Script, `POST /api/sync` y
  mostrar el resumen que devuelva (pesadas nuevas, noches rehechas, etc.) en el aviso de la propia app.
- Textos que mencionan claude.ai («Abre la app en claude.ai», «inicia sesión en claude.ai»…): adaptar.
- La librería XLSX (`xlsx.full.min.js` 0.18.5) y las que se cargan para el PDF: servirlas desde el propio
  servidor (sin CDN) para que funcione sin internet externo.
- Quitar del HTML servido el bloque de datos empaquetados (`"@@PACK@@"` → vacío): ya no hace falta.
- PWA: `manifest.webmanifest`, iconos de `branding/` (ver `docs/TRASPASO-original.md` §3.5).

### 3.3 API del servidor
Toda escritura bajo `/api/` (salvo `/api/ingest/`) exige la cabecera `X-BodyLens: 1` (protección CSRF).
```
POST /api/login            {username, password} → cookie de sesión (HttpOnly, Secure, SameSite=Lax, 90 días)
POST /api/logout
GET  /api/invite/{code}    ¿invitación válida?
POST /api/register         {code, username, name, password}
GET  /api/me               cuenta, pareja, peticiones, fuentes y última sincronización
POST /api/me/password | /api/me/name
POST /api/partner/request | accept | reject | unlink
POST /api/admin/invites    (admin) → enlace de registro
GET  /api/admin/users      (admin)  ·  PUT /api/admin/users/{id}/bridge {sheetId, appsScriptUrl}
GET  /api/docs/{col}[?since=rev]      lista de {id, data, rev}; rev global incremental
GET  /api/docs/{col}/{id}
PUT  /api/docs/{col}/{id}             cuerpo = data (JSON)
DELETE /api/docs/{col}/{id}
GET  /api/workbook.xlsx               XLSX con las mismas pestañas y cabeceras que la hoja de Google (ETag)
GET  /api/workbook/meta               {etag, updatedAt, lastSync, lastSyncResult}
POST /api/sync                        sincroniza ya (mismo trabajo que la tarea de 15 min) → resumen
GET  /api/status                      estado de fuentes: última pesada, último envío de Salud, errores
POST /api/ingest/hae?token=…          Health Auto Export (sin cookie; token = HAE_TOKEN)
GET  /oauth/withings/start            redirige a Withings (solo con sesión)
GET  /oauth/withings/callback         guarda tokens en SQLite (cifrados con SECRET_KEY)
POST /api/withings/notify             webhook de Withings (opcional, fase 2)
GET  /healthz                         para Docker
```
Todo bajo login salvo `/api/login`, `/api/ingest/hae` (token), `/api/withings/notify` y `/healthz`.

### 3.4 Datos en SQLite
- `users`, `sessions`, `invites`, `partner_requests`, `shared_docs` (registros comunes de la pareja), `user_state`
  (ETag del workbook y última sincronización de cada cuenta).
- `docs(user_id, collection TEXT, id TEXT, data JSON, rev INTEGER, updated_at, PRIMARY KEY(user_id,collection,id))`: espejo
  exacto de la colección `bascula` del artefacto (ajustes `peso`, `hist-AAAA`, `com-AAAA`, `medidas`,
  `perfiles`, `pf-<perfil>-…`, etc.).
- Una tabla por pestaña de la hoja (mismas columnas, misma clave que usa `guardarFilas_`): `withings`,
  `actividad`, `sueno`, `entrenamientos`, `siestas`, `spo2_vo2`, `ecg`, `salud`, `avisos_salud`,
  `registros_salud`, `sueno_fases`, `notas_historicas`, `pesos_historicos`.
- `kv(key, value)`: tokens de Withings, `lastSync`, resultado de la última sincronización, muestras de depuración
  (equivalentes a `HAE_MUESTRA_*` de las propiedades del script).
- `workbook.py` genera el XLSX a partir de esas tablas (openpyxl), con fechas como fechas de Excel y los mismos
  formatos, y lo cachea en disco; se regenera cuando cambia algo (y cambia el ETag).

## 4. Fases

### Fase 0 — Repositorio, contenedor y CI
- `docker/Dockerfile` (multi-stage, `python:3.12-slim`, usuario sin privilegios, `HEALTHCHECK` a `/healthz`).
- `docker/compose.yml` (producción: imagen de GHCR, volumen `/data`, `env_file`, `restart: unless-stopped`,
  puerto interno 8000) y `docker/compose.dev.yml` (código montado, `uvicorn --reload`, frontend servido desde
  `frontend/src` sin compilar).
- `.github/workflows/docker.yml`: tests + build multi-arch (`linux/amd64,linux/arm64`) con Buildx y push a
  Docker Hub `jaimetur/bodylens` con etiquetas `latest`, `sha-<7>` y versión en tags `v*`.
- `.env.example` con todas las variables (sección 6).

### Fase 1 — La app funcionando en Docker con la hoja de Google como fuente (puente)
Objetivo: **en cuanto esté desplegada, Jaime ya tiene datos frescos cada 15 min**, sin cambiar nada en el iPhone
ni en Withings.
1. Servir la página (a+b+c unidos en tiempo de petición o al construir) con `claude-shim.js` y login.
2. Sembrar `docs` con una copia de los datos del artefacto:
   - `snap.json` (copia completa embebida en la página, incluye perfiles en `prof`/`profs`), y/o
   - la «Copia completa (JSON)» que se descarga en **Ajustes → Copia de seguridad** del artefacto
     (formato `{app:'bascula', v:1, doc, hist, med, act, slp, wo, food, hk, ecg, hkev, hklog, nap}`).
   Script `python -m app.seed <fichero>` idempotente, que acepte ambos formatos.
3. Tarea cada 15 min:
   a. `GET` a la URL del Apps Script `?accion=sincronizar` (`APPS_SCRIPT_SYNC_URL`) para que traiga Withings y
      rehaga las últimas noches. (La aplicación web está publicada con acceso «Cualquier usuario».)
   b. Exportar la hoja a XLSX con la **API de Google Drive** (`files.export`, cuenta de servicio con la hoja
      compartida en solo lectura; credenciales en `GOOGLE_SERVICE_ACCOUNT_JSON`) y guardarla como el workbook
      actual. Si no ha cambiado (hash), no se toca el ETag.
4. `/api/workbook.xlsx` sirve ese fichero; la página se refresca sola gracias al `watchTool` del shim.
5. `POST /api/sync` hace 3a + 3b al momento.

### Fase 2 — Independizarse de Google (port del Apps Script)
1. **Withings** directo desde el servidor: OAuth (scope `user.metrics,user.activity`; el refresh token rota: se
   guarda siempre el nuevo), y port de `actualizarHistorialWithings`, `actualizarActividad_`, `actualizarSueno_`,
   `actualizarCorazon_` (SpO2, VO2, ECG) y su lógica de mezcla (`mezclaWithings_`, `rellenaHuecos_`,
   `siestasSinSalud_`, `sinCopiasDeSalud_`). **Siempre volver a pedir las últimas 3 noches** y sobrescribirlas.
   Tarea cada 15 min + webhook `notify/subscribe` opcional.
2. **Health Auto Export** directo: `POST /api/ingest/hae?token=` con el port completo de `doPost` y de
   `suenoDesdeSalud_`, `guardarNochesSalud_`, `desvelos_`, `actividadDesdeSalud_`, `entrenosDesdeSalud_`, etc.
   Debe aceptar cargas grandes (varios MB) y responder rápido (procesar en segundo plano si hace falta).
3. Las tablas de SQLite pasan a ser la fuente; el workbook se genera desde ellas.
4. **Importación inicial** de toda la hoja de Google a las tablas (una vez), para no perder historial.
5. Prueba de paridad: con la misma entrada, el workbook generado por el servidor y la hoja de Google deben dar
   **los mismos números en la app** (mismas noches, siestas, pesadas, pasos por día…).
6. Cuando la paridad esté comprobada: Jaime cambia las URL de Health Auto Export al servidor, registra la nueva
   redirect URI en el panel de desarrollador de Withings y autoriza desde `/oauth/withings/start`.
   Después se desactivan los disparadores del Apps Script (la hoja queda como copia, opcional).

### Fase 3 — Pulido
- Estado de las fuentes (bloque en Ajustes o página propia): última pesada, último envío de Salud por tipo
  (sueño, métricas…), última sincronización y errores. Ayuda a detectar casos como «el Watch aún no ha pasado la
  noche al iPhone».
- Copia de seguridad diaria de la base (`/data/backups/bodylens-AAAA-MM-DD.db`, conservar 30).
- Exportación opcional a la hoja de Google (escritura) si Jaime quiere mantenerla como copia.

### Fuera de alcance de esta tarea (documentado para después)
Módulo Android (Health Connect → `/api/ingest`), informe PDF nuevo, más datos de Withings
(ver `docs/TRASPASO-original.md` §3.1, §3.6 y §3.7).

## 5. Reglas de negocio que hay que conservar (resumen; la referencia es `Codigo.gs`)

- **Noche del día k**: la que acaba entre las 17:00 del día k-1 y las 17:00 del día k. Debe acabar después de
  las 03:00 del día k; lo que acabe antes es siesta.
- **Episodios**: ratos de sueño separados por más de 90 min son episodios distintos; dos episodios nocturnos
  (19:00–12:00) separados por ≤ 4 h se unen y el hueco cuenta como desvelo.
- **Fuente de la noche (mezcla)**: horario, tiempo dormido y desvelos de **AutoSleep** si lo hay; si no, del
  **Apple Watch**; si no, de la fuente con más sueño. Si el Watch registra claramente más sueño que AutoSleep
  (> 1,2 × AutoSleep + 15 min), manda el Watch. Profundo y REM salen del Watch en el horario de la noche.
- **Reenvíos**: cada envío de Health Auto Export manda en el tramo de tiempo que cubre por fuente: los tramos de
  esa fuente dentro de ese intervalo que no vengan en el envío se borran (AutoSleep rehace la noche al despertar).
- **Siestas**: episodios ≥ 10 min fuera de la noche; también los de otras fuentes que no se solapen (±30 min).
  En la tarjeta de siestas del frontend, el día va de las 20:00 de la víspera a las 20:00.
- **Desvelos**: huecos ≥ 10 min dentro de la noche, guardados como `"a~b;c~d"` en minutos desde la medianoche del
  día en que te levantas.
- **Métricas por horas** de Salud (`step_count`, `walking_running_distance`, `active_energy`,
  `basal_energy_burned`, `apple_exercise_time`, `heart_rate`, `flights_climbed`): se guardan por hora.
- Salud es la fuente de verdad; Withings solo para peso/composición y para rellenar huecos.

## 6. Variables de entorno

Ver `.env.example`. Resumen:

```
TZ=Europe/Madrid
PUBLIC_URL=https://bodylens.<dominio>
BODYLENS_PASSWORD_HASH=          # argon2 de la contraseña de acceso (script: python -m app.hashpw)
SECRET_KEY=                      # firma de cookies y cifrado de tokens
SYNC_INTERVAL_MIN=15
APPS_SCRIPT_SYNC_URL=…?accion=sincronizar        # fase 1
GOOGLE_SHEET_ID=1aUMgruI3VycOCjbqH4_UvL8nS8i-mt1QFNiz6xaQx2Q
GOOGLE_SERVICE_ACCOUNT_JSON=/data/secrets/google-sa.json
WITHINGS_CLIENT_ID= / WITHINGS_CLIENT_SECRET= / WITHINGS_REDIRECT_URI=   # fase 2
HAE_TOKEN=                       # token largo aleatorio para la URL de Health Auto Export
```

## 7. Criterios de aceptación

1. `docker compose up` en el Synology deja la app en `https://bodylens.<dominio>` tras el login, idéntica al
   artefacto (comprobar Resumen, Peso, Sueño con reloj y siestas, Actividad, Íntimo con PIN, Ajustes).
2. Sin tocar nada, una pesada nueva o una noche nueva aparece en la página abierta en **≤ 16 minutos** (fase 1) y
   en ≤ 1 min tras llegar al servidor (fase 2, por el sondeo del shim).
3. El botón «Actualizar» sincroniza al momento y muestra el resumen dentro de la app, sin abrir pestañas.
4. Las ediciones (ajustes, notas, comidas, medidas, perfiles, entradas manuales de sueño) persisten tras
   reiniciar el contenedor.
5. Fase 2: paridad comprobada con la hoja para al menos los últimos 60 días; tests de las reglas de sueño con
   fixtures sintéticos (casos: noche solo AutoSleep; AutoSleep corto frente al Watch; siesta antes de medianoche;
   reenvío que corrige tramos; noche sin datos).
6. CI publica la imagen en GHCR; ningún secreto en el repo ni en la imagen.
