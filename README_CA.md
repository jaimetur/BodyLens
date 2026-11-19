# BodyLens

[English](README.md) · [Español](README_ES.md) · **Català** · [Français](README_FR.md) · [Italiano](README_IT.md) ·
[Deutsch](README_DE.md) · [Português](README_PT.md) · [Nederlands](README_NL.md) · [中文](README_ZH.md) ·
[日本語](README_JA.md)

**BodyLens** és una aplicació web de salut personal, autoallotjada i multiusuari. Reuneix el pes i la composició
corporal d'una bàscula **Withings** i el que registren el teu mòbil i el teu rellotge (son, activitat, pols, VFC, SpO2,
VO2 màx, ECG, cicle, estat d'ànim…) des d'**Apple Salut** o **Health Connect d'Android**. Funciona en Docker al teu
propi servidor, les dades arriben soles i cada persona veu només les seves.

## Funcions

- **Resum:** pes de tendència, progrés del pla, «avui d'un cop d'ull» (preparació, son, saldo de son, VFC, passos) i
  conclusions i avisos automàtics.
- **Pes:** tendència suavitzada, pla amb ritmes objectiu, projecció, setmanes, calendari i fites; historial de pesos
  al llarg dels anys, intents de pèrdua de pes i rebots.
- **Cos:** composició (greix, múscul, aigua, os), IMC/FFMI amb rangs per edat i sexe, mesures amb cinta, cor (pols en
  repòs, VFC, SpO2, VO2 màx, ECG, avisos de freqüència cardíaca) i benestar.
- **Activitat:** passos, calories i minuts d'exercici amb anells i objectius, entrenaments i la seva relació amb el pes.
- **Son:** l'última nit amb fases, saldo de son de 7 nits, becaines, horari objectiu i anàlisi. Les dades d'AutoSleep i
  d'Apple Watch es barregen amb regles pròpies (finestra de 17:00 a 17:00, desvetllaments, becaines).
- **Àpats:** una puntuació diària del que menges, beus i de l'exercici que fas, i el seu efecte estimat en el teu pes.
- **Íntim:** cicle (amb previsió), activitat sexual i estat d'ànim, protegits amb un PIN privat.
- **Ajuda** dins de l'app: l'ajuda de cada mòdul, aquest README i el registre de canvis, en el teu idioma.
- **Informe PDF** del període triat i **còpies de seguretat completes** en JSON i CSV.
- **Interfície:** temes clar i fosc, pensada per al mòbil (s'instal·la com a app des del navegador), gestos de
  lliscament, disseny per a pantalles amples de fins a 1600 px.
- **Idiomes:** anglès (per defecte), castellà, català, francès, italià, alemany, portuguès, neerlandès, xinès i
  japonès. Cada compte tria el seu; els correus arriben en l'idioma de qui els rep.

### Comptes

- **Diversos comptes**, cadascun amb les seves dades, amb accés mitjançant usuari i contrasenya.
- **Alta:** peticions d'accés des de la pantalla d'entrada, aprovades per un administrador (amb avisos per correu), o
  enllaços d'invitació d'un sol ús.
- **Parelles:** dos comptes es poden unir per compartir i editar junts els registres de cicle i intimitat.
- **Perfils:** cada compte pot tenir diversos perfils (amb un PIN opcional), que es gestionen a *El teu compte*.
- **Administració:** usuaris (usuari, nom, correu, contrasenya, interruptor d'actiu, rol d'administrador), peticions
  d'accés, invitacions, correu (SMTP), credencials de l'aplicació de Withings, còpies de seguretat i fonts de dades.

### Dades que arriben soles

- **Withings:** cada compte es connecta amb OAuth; les pesades, la composició, l'activitat, els entrenaments, el son,
  la SpO2, el VO2 màx i l'ECG es descarreguen cada pocs minuts, i a l'instant quan Withings avisa d'un mesurament nou.
- **Apple Salut:** l'app d'iPhone *Health Auto Export* envia les dades a una adreça personal de cada compte.
- **Android:** l'app BodyLens per a Android (a `android/`) llegeix Health Connect i envia cada hora en el mateix format.
- **Còpia de seguretat diària** de la base de dades a les 03:30 (es conserven les últimes 30).

## Com està construïda

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend:** una sola pàgina (`src/frontend/app/`), nascuda com a artefacte de claude.ai, servida amb una petita
  capa (`src/frontend/compat/claude-shim.js`) que implementa contra l'API del servidor el que la pàgina demanava abans
  a claude.ai (`db`, `user`, `downloads`…).
- **Backend:** Python 3.12, FastAPI, SQLite (WAL) a `/data`, un únic procés amb el planificador a dins.
- **Traduccions:** el catàleg és en anglès (`src/frontend/i18n/catalog.json`) i cada idioma és
  `src/frontend/i18n/locales/<lang>.json`. La pàgina es tradueix al navegador amb `src/frontend/i18n/i18n.js`,
  que també dona format a números i dates; el servidor fa servir els mateixos fitxers per als correus. L'ajuda (`help/en/`), aquest README i el registre de
  canvis estan escrits en anglès i es tradueixen automàticament a l'idioma de cada compte amb l'API de Claude (la
  clau es posa a Administració → Traductor); cada traducció es conserva fins que canvia el text en anglès.
- **Seguretat:** contrasenyes amb argon2, sessions al servidor (cookie HttpOnly/Secure/SameSite), capçalera
  anti-CSRF a cada escriptura, límits de freqüència, cada compte aïllat, tokens d'OAuth xifrats; secrets només en
  variables d'entorn o a la base de dades del servidor.

## Estructura del repositori

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

## Desenvolupament

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
L'última ordre arrenca http://localhost:8000 amb recàrrega en calent: la pàgina es serveix tal qual des de `src/`
(n'hi ha prou de recarregar) i el backend es reinicia en desar. `tools/dev-data.sh` copia les dades del servidor a
`data-dev/` (els canvis fets en desenvolupament no tornen mai). També hi ha
`docker compose -f docker/compose.dev.yml up --build`.

## Desplegament

Cada push a la branca de la versió actual (p. ex. `0.1.0`) executa els tests i publica la imatge
`jaimetur/bodylens:latest` (amd64 i arm64) a Docker Hub; `main` publica `jaimetur/bodylens:main`. Al
servidor: `docker/compose.yml` més un fitxer `.env`. El NAS munta el codi des de la carpeta de l'stack, així que
`tools/deploy.sh` desplega un commit en segons sense esperar una imatge nova. Passos complets (en anglès):
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Col·laborar amb traduccions

Només necessites anglès: consulta [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) (en anglès) per afegir
un idioma o millorar-ne un. L'ajuda, el README i el registre de canvis es tradueixen automàticament: només edites els fitxers en anglès.

## Documentació

- Ajuda d'ús: [`help/`](help/en/README.md) (en anglès; també dins de l'app, a *Ajuda*)
- Canvis de cada versió: [`CHANGELOG.md`](CHANGELOG.md)
- Instruccions per a agents de codi: [`AGENTS.md`](AGENTS.md)

Les dades personals mai no entren al repositori: les bases de dades, les còpies JSON i `.env` són a `.gitignore`.
