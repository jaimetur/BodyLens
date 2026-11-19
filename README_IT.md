# BodyLens

[English](README.md) · [Español](README_ES.md) · [Català](README_CA.md) · [Français](README_FR.md) · **Italiano** ·
[Deutsch](README_DE.md) · [Português](README_PT.md) · [Nederlands](README_NL.md) · [中文](README_ZH.md) ·
[日本語](README_JA.md)

**BodyLens** è un'app web di salute personale, self-hosted e multiutente. Riunisce il peso e la composizione
corporea di una bilancia **Withings** e ciò che registrano il tuo telefono e il tuo orologio (sonno, attività,
frequenza cardiaca, HRV, SpO2, VO2 max, ECG, ciclo, umore…) da **Apple Salute** o da **Health Connect di Android**.
Funziona in Docker sul tuo server, i dati arrivano da soli e ogni persona vede solo i propri.

## Funzioni

- **Riepilogo:** peso di tendenza, avanzamento del piano, «oggi a colpo d'occhio» (prontezza, sonno, saldo del sonno,
  HRV, passi) e conclusioni e avvisi automatici.
- **Peso:** tendenza smussata, piano con ritmi obiettivo, proiezione, settimane, calendario e traguardi; storico dei
  pesi negli anni, tentativi di perdita di peso e recuperi.
- **Corpo:** composizione (grasso, muscolo, acqua, ossa), IMC/FFMI con intervalli per età e sesso, misure con il
  metro, cuore (frequenza a riposo, HRV, SpO2, VO2 max, ECG, avvisi di frequenza cardiaca) e benessere.
- **Attività:** passi, calorie e minuti di esercizio con anelli e obiettivi, allenamenti e il loro rapporto con il peso.
- **Sonno:** l'ultima notte con le fasi, saldo del sonno su 7 notti, sonnellini, orario obiettivo e analisi. I dati di
  AutoSleep e di Apple Watch vengono uniti con regole proprie (finestra dalle 17:00 alle 17:00, risvegli, sonnellini).
- **Pasti:** un punteggio giornaliero di ciò che mangi, bevi e dell'esercizio che fai, e il suo effetto stimato sul
  tuo peso.
- **Intimo:** ciclo (con previsione), attività sessuale e umore, protetti da un PIN privato.
- **Aiuto** nell'app: l'aiuto di ogni modulo, questo README e il registro delle modifiche, nella tua lingua.
- **Report PDF** del periodo scelto e **backup completi** in JSON e CSV.
- **Interfaccia:** temi chiaro e scuro, pensata per il telefono (si installa come app dal browser), gesti di
  scorrimento, layout per schermi larghi fino a 1600 px.
- **Lingue:** inglese (predefinita), spagnolo, catalano, francese, italiano, tedesco, portoghese, olandese, cinese e
  giapponese. Ogni account sceglie la sua; le e-mail arrivano nella lingua di chi le riceve.

### Account

- **Più account**, ciascuno con i propri dati, con accesso tramite nome utente e password.
- **Registrazione:** richieste di accesso dalla pagina di accesso, approvate da un amministratore (con avvisi via
  e-mail), oppure link di invito monouso.
- **Coppie:** due account possono essere collegati per condividere e modificare insieme i registri di ciclo e
  intimità.
- **Profili:** ogni account può avere più profili (con un PIN facoltativo), gestiti in *Il tuo account*.
- **Amministrazione:** utenti (nome utente, nome, e-mail, password, interruttore di attivo, ruolo di amministratore),
  richieste di accesso, inviti, e-mail (SMTP), credenziali dell'app Withings, backup e fonti di dati.

### Dati che arrivano da soli

- **Withings:** ogni account si collega con OAuth; pesate, composizione, attività, allenamenti, sonno, SpO2, VO2 max
  ed ECG vengono scaricati ogni pochi minuti, e subito quando Withings segnala una nuova misurazione.
- **Apple Salute:** l'app per iPhone *Health Auto Export* invia i dati a un indirizzo personale di ogni account.
- **Android:** l'app BodyLens per Android (in `android/`) legge Health Connect e invia ogni ora nello stesso formato.
- **Backup giornaliero** del database alle 03:30 (vengono conservati gli ultimi 30).

## Come è costruita

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend:** una sola pagina (`src/frontend/app/`), nata come artefatto di claude.ai, servita con un piccolo
  livello (`src/frontend/compat/claude-shim.js`) che implementa tramite l'API del server ciò che la pagina chiedeva
  prima a claude.ai (`db`, `user`, `downloads`…).
- **Backend:** Python 3.12, FastAPI, SQLite (WAL) in `/data`, un unico processo con lo scheduler all'interno.
- **Traduzioni:** il catalogo è in inglese (`src/frontend/i18n/catalog.json`) e ogni lingua è
  `src/frontend/i18n/locales/<lang>.json`. La pagina viene tradotta nel browser da `src/frontend/i18n/i18n.js`,
  che formatta anche numeri e date; il server usa gli stessi file per le e-mail. L'aiuto (`help/en/`), questo README e il registro delle
  modifiche sono scritti in inglese e tradotti automaticamente nella lingua di ogni account con l'API di Claude (la
  chiave si imposta in Amministrazione → Traduttore); ogni traduzione si conserva finché il testo inglese non cambia.
- **Sicurezza:** password con argon2, sessioni lato server (cookie HttpOnly/Secure/SameSite), header anti-CSRF a ogni
  scrittura, limiti di frequenza, ogni account isolato, token OAuth cifrati; segreti solo in variabili d'ambiente o
  nel database del server.

## Struttura del repository

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

## Sviluppo

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
L'ultimo comando avvia http://localhost:8000 con ricarica a caldo: la pagina viene servita così com'è da `src/`
(basta ricaricare) e il backend si riavvia al salvataggio. `tools/dev-data.sh` copia i dati del server in
`data-dev/` (le modifiche fatte in sviluppo non tornano mai indietro). Esiste anche
`docker compose -f docker/compose.dev.yml up --build`.

## Distribuzione

Ogni push sul ramo della versione corrente (ad es. `0.1.0`) esegue i test e pubblica l'immagine
`jaimetur/bodylens:latest` (amd64 e arm64) su Docker Hub; `main` pubblica `jaimetur/bodylens:main`. Sul
server: `docker/compose.yml` più un file `.env`. Il NAS monta il codice dalla cartella dello stack, quindi
`tools/deploy.sh` distribuisce un commit in pochi secondi senza attendere una nuova immagine. Passaggi completi:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) (in inglese).

## Contribuire alle traduzioni

Ti basta l'inglese: consulta [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) (in inglese) per aggiungere
una lingua o migliorarne una. L'aiuto, il README e il registro delle modifiche si traducono automaticamente: modifichi solo i file in inglese.

## Documentazione

- Aiuto all'uso: [`help/`](help/en/README.md) (in inglese; anche nell'app, in *Aiuto*)
- Modifiche di ogni versione: [`CHANGELOG.md`](CHANGELOG.md)
- Istruzioni per gli agenti di codice: [`AGENTS.md`](AGENTS.md)

I dati personali non entrano mai nel repository: i database, i backup JSON e `.env` sono in `.gitignore`.
