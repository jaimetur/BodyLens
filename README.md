# BodyLens

**BodyLens** is a self-hosted, multi-user personal health web app. It brings together the weight and body
composition from a **Withings** scale and what your phone and watch record (sleep, activity, heart rate, HRV, SpO2,
VO2 max, ECG, cycle, mood…) from **Apple Health** or **Android Health Connect**. It runs in Docker on your own
server, the data arrives on its own, and every person sees only their own data.

## Features

- **Summary:** trend weight, plan progress, “today at a glance” (readiness, sleep, sleep balance, HRV, steps) and
  automatic insights and alerts.
- **Weight:** smoothed trend, plan with target rates, projection, weeks, calendar and milestones; weight history
  over the years, weight-loss attempts and rebounds.
- **Body:** composition (fat, muscle, water, bone), BMI/FFMI with ranges by age and sex, tape measurements, heart
  (resting heart rate, HRV, SpO2, VO2 max, ECG, heart-rate alerts) and wellbeing.
- **Activity:** steps, calories and exercise minutes with rings and goals, workouts and how they relate to weight.
- **Sleep:** last night with stages, 7-night sleep balance, naps, target schedule and analysis. AutoSleep and
  Apple Watch data are merged with their own rules (5 pm → 5 pm window, wake-ups, naps).
- **Meals:** a daily score of what you eat, drink and exercise, and its estimated effect on your weight.
- **Intimate:** cycle (with forecast), sexual activity and mood, protected by a private PIN.
- **Help** inside the app: the help of every module, this README and the changelog, in your language.
- **PDF report** of the chosen period and **full backups** in JSON and CSV.
- **Interface:** light and dark themes, designed for the phone (installs as an app from the browser), swipe
  gestures, wide-screen layout up to 1600 px.
- **Languages:** English (default), Spanish, Catalan, French, Italian, German, Portuguese, Dutch, Chinese and
  Japanese. Each account picks its own; emails arrive in the recipient’s language.

### Accounts

- **Several accounts**, each with its own data, signed in with username and password.
- **Sign-up:** access requests from the sign-in page, approved by an administrator (with email notices), or
  single-use invitation links.
- **Couples:** two accounts can be linked to share and edit the cycle and intimacy records together.
- **Profiles:** each account can keep several profiles (with an optional PIN), managed in *Your account*.
- **Administration:** users (username, name, email, password, active switch, admin role), access requests,
  invitations, email (SMTP), Withings app credentials, backups and data sources.

### Data that arrives on its own

- **Withings:** each account connects with OAuth; weigh-ins, composition, activity, workouts, sleep, SpO2, VO2 max
  and ECG are fetched every few minutes, and at once when Withings notifies a new measurement.
- **Apple Health:** the iPhone app *Health Auto Export* posts to a personal address of each account.
- **Android:** the BodyLens Android app (in `android/`) reads Health Connect and posts every hour in the same format.
- **Daily backup** of the database at 03:30 (the last 30 are kept).

## How it is built

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend:** a single page (`src/frontend/app/`), born as a claude.ai artifact, served with a small layer
  (`src/frontend/compat/claude-shim.js`) that implements what the page used to ask claude.ai for (`db`, `user`,
  `downloads`…) against the server API.
- **Backend:** Python 3.12, FastAPI, SQLite (WAL) in `/data`, one process with the scheduler inside.
- **Translations:** the catalog is English (`src/frontend/i18n/catalog.json`) and each language is
  `src/frontend/i18n/locales/<lang>.json`. The page is translated in the browser by `src/frontend/i18n/i18n.js`,
  which also formats numbers and dates; the server uses the same files for emails. The help (`help/en/`), this README and
  the changelog are written in English and translated automatically into each account's language with the Claude
  API (set the key in Administration → Translator); each translation is kept until the English text changes.
- **Security:** argon2 passwords, server-side sessions (HttpOnly/Secure/SameSite cookie), anti-CSRF header on every
  write, rate limits, every account isolated, OAuth tokens encrypted; secrets only in environment variables or in
  the server database.

## Repository layout

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

## Development

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
The last command starts http://localhost:8000 with hot reload: the page is served as-is from `src/` (just reload)
and the backend restarts on save. `tools/dev-data.sh` copies the server data into `data-dev/` (changes made in
development never go back). There is also `docker compose -f docker/compose.dev.yml up --build`.

## Deployment

Every push to the current version branch (e.g. `0.1.0`) runs the tests and publishes the image
`jaimetur/bodylens:latest` (amd64 and arm64) to Docker Hub; `main` publishes `jaimetur/bodylens:main`. On the
server: `docker/compose.yml` plus a `.env` file. The NAS mounts the code from the stack folder, so
`tools/deploy.sh` deploys a commit in seconds without waiting for a new image. Full steps:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Contributing translations

You only need English: see [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) to add a language or improve
one. The help, the README and the changelog are translated automatically: you only edit the English files.

## Documentation

- User help: [`help/`](help/en/README.md) (also inside the app, in *Help*)
- Changes in each version: [`CHANGELOG.md`](CHANGELOG.md)
- Instructions for coding agents: [`AGENTS.md`](AGENTS.md)

Personal data never goes into the repository: databases, JSON backups and `.env` are in `.gitignore`.
