<!-- en: b45325d17939eef7 -->
# BodyLens

**BodyLens** es una app web de salud personal, multiusuario y autoalojada. Reúne el peso y la composición corporal
de una báscula **Withings** y lo que registran tu móvil y tu reloj (sueño, actividad, frecuencia cardiaca, HRV, SpO2,
VO2 máx, ECG, ciclo, ánimo…) desde **Apple Salud** o **Android Health Connect**. Funciona en Docker en tu propio
servidor, los datos llegan solos y cada persona ve únicamente los suyos.

## Funciones

- **Resumen:** peso de tendencia, progreso del plan, «hoy de un vistazo» (preparación, sueño, saldo de sueño, HRV, pasos) y
  análisis y avisos automáticos.
- **Peso:** tendencia suavizada, plan con ritmos objetivo, proyección, semanas, calendario e hitos; historial de pesos
  a lo largo de los años, intentos de pérdida y rebotes.
- **Cuerpo:** composición (grasa, músculo, agua, hueso), IMC/FFMI con rangos por edad y sexo, medidas con cinta, corazón
  (frecuencia cardiaca en reposo, HRV, SpO2, VO2 máx, ECG, avisos de frecuencia cardiaca) y bienestar.
- **Actividad:** pasos, calorías y minutos de ejercicio con anillos y objetivos, entrenamientos y cómo se relacionan con el peso.
- **Sueño:** la última noche con sus fases, saldo de sueño de 7 noches, siestas, horario objetivo y análisis. Los datos de AutoSleep y
  del Apple Watch se combinan con reglas propias (ventana de 17:00 a 17:00, despertares, siestas).
- **Comidas:** una nota diaria de lo que comes, bebes y haces de ejercicio, y su efecto estimado en tu peso.
- **Íntimo:** ciclo (con previsión), actividad sexual y ánimo, protegidos por un PIN privado.
- **Ayuda** dentro de la app: la ayuda de cada módulo, este README y el registro de cambios, en tu idioma.
- **Informe en PDF** del periodo elegido y **copias de seguridad completas** en JSON y CSV.
- **Interfaz:** temas claro y oscuro, pensada para el móvil (se instala como app desde el navegador), gestos de
  deslizamiento, diseño para pantallas anchas de hasta 1600 px.
- **Idiomas:** inglés (por defecto), español, catalán, francés, italiano, alemán, portugués, neerlandés, chino y
  japonés. Cada cuenta elige el suyo; los correos llegan en el idioma de quien los recibe.

### Cuentas

- **Varias cuentas**, cada una con sus propios datos, con acceso mediante usuario y contraseña.
- **Alta:** peticiones de acceso desde la página de entrada, aprobadas por un administrador (con avisos por correo), o
  enlaces de invitación de un solo uso.
- **Parejas:** dos cuentas se pueden unir para compartir y editar juntas los registros de ciclo e intimidad.
- **Perfiles:** cada cuenta puede tener varios perfiles (con PIN opcional), que se gestionan en *Tu cuenta*.
- **Administración:** usuarios (usuario, nombre, correo, contraseña, interruptor de activo, rol de administrador), peticiones
  de acceso, invitaciones, correo (SMTP), credenciales de la app de Withings, copias de seguridad y fuentes de datos.

### Datos que llegan solos

- **Withings:** cada cuenta se conecta con OAuth; las pesadas, la composición, la actividad, los entrenamientos, el sueño, la SpO2, el VO2 máx
  y el ECG se consultan cada pocos minutos, y al instante cuando Withings avisa de una medición nueva.
- **Apple Salud:** la app de iPhone *Health Auto Export* envía los datos a una dirección personal de cada cuenta.
- **Android:** la app BodyLens para Android (en `android/`) lee Health Connect y envía cada hora en el mismo formato.
- **Copia de seguridad diaria** de la base de datos a las 03:30 (se conservan las últimas 30).

## Cómo está construida

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend:** una única página (`src/frontend/app/`), nacida como artefacto de claude.ai, servida con una pequeña capa
  (`src/frontend/compat/claude-shim.js`) que implementa contra la API del servidor lo que la página pedía antes a claude.ai (`db`, `user`,
  `downloads`…).
- **Backend:** Python 3.12, FastAPI, SQLite (WAL) en `/data`, un solo proceso con el planificador dentro.
- **Traducciones:** el catálogo es en inglés (`src/frontend/i18n/catalog.json`) y cada idioma es
  `src/frontend/i18n/locales/<lang>.json`. La página se traduce en el navegador con `src/frontend/i18n/i18n.js`,
  que también da formato a números y fechas; el servidor usa los mismos ficheros para los correos. La ayuda (`help/en/`), este README y
  el registro de cambios están escritos en inglés y se traducen automáticamente al idioma de cada cuenta con la API de
  Claude (pon la clave en Administración → Traductor); cada traducción se conserva hasta que cambia el texto en inglés.
- **Seguridad:** contraseñas con argon2, sesiones en el servidor (cookie HttpOnly/Secure/SameSite), cabecera anti-CSRF en cada
  escritura, límites de frecuencia, cada cuenta aislada, tokens de OAuth cifrados; secretos solo en variables de entorno o en
  la base de datos del servidor.

## Estructura del repositorio

```
src/backend/app/        server (package "app"), one subpackage per module:
  core/                 settings, SQLite, security, languages, backups, route dependencies
  accounts/             accounts, sessions, invitations, access requests, admin CLI
  admin/                Administration panel
  couples/              couples
  data/                 documents of each account and backup import
  help/                 the Help module (help, README and changelog, translated automatically)
  sheets/               the data tables and the XLSX workbook the page reads
  sources/              Withings and Apple Health / Android ingestion
  sync/                 synchronisation and scheduler
  mail/                 SMTP email
  web/                  page assembly and static files
src/frontend/
  app/                  the app (app_a: styles and views, app_b: core, app_c: interface)
  compat/               window.claude layer
  accounts/ admin/ common/   sign-in, request, registration, Your account and Administration pages
  i18n/                 translator, English catalog and one file per language
android/                Android app (Health Connect → server)
assets/branding/        icons and logo
tests/<module>/         tests (pytest) and tests/frontend/*.mjs (page and translator in jsdom)
help/en/                user help, one file per module (English; translated automatically in the app)
docker/                 Dockerfile and compose files (NAS, hot reload, development)
docs/DEPLOYMENT.md      deployment on a Synology NAS
tools/                  deployment, development server and translation tools
```

## Desarrollo

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'
```
```bash
.venv/bin/python -m pytest -q
```
```bash
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs && node tests/frontend/i18n.mjs
```
```bash
tools/dev-data.sh && tools/dev.sh
```
El último comando arranca http://localhost:8000 con recarga en caliente: la página se sirve tal cual desde `src/` (basta con recargar)
y el backend se reinicia al guardar. `tools/dev-data.sh` copia los datos del servidor en `data-dev/` (los cambios hechos en
desarrollo nunca vuelven). También existe `docker compose -f docker/compose.dev.yml up --build`.

## Despliegue

Cada push a la rama de la versión actual (p. ej. `0.1.0`) ejecuta los tests y publica la imagen
`jaimetur/bodylens:latest` (amd64 y arm64) en Docker Hub; `main` publica `jaimetur/bodylens:main`. En el
servidor: `docker/compose.yml` más un fichero `.env`. El NAS monta el código desde la carpeta del stack, así que
`tools/deploy.sh` despliega un commit en segundos sin esperar a una imagen nueva. Pasos completos:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Contribuir con traducciones

Solo necesitas el inglés: mira [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) para añadir un idioma o mejorar
uno. La ayuda, el README y el registro de cambios se traducen automáticamente: solo editas los ficheros en inglés.

## Documentación

- Ayuda de usuario: [`help/`](help/en/README.md) (también dentro de la app, en *Ayuda*)
- Cambios de cada versión: [`CHANGELOG.md`](CHANGELOG.md)
- Instrucciones para agentes de código: [`AGENTS.md`](AGENTS.md)

Los datos personales nunca van al repositorio: las bases de datos, las copias JSON y `.env` están en `.gitignore`.
