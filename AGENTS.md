# AGENTS.md — BodyLens

Instructions for coding agents (Codex, Claude Code…) working in this repository.

## What it is

BodyLens is a multi-user health app: weight and body composition (Withings scale), activity, sleep, heart, meals,
cycle, mood… Every account has its own data; accounts are created by invitation or by an access request approved
by an administrator, and two accounts can be linked as a couple to share and edit the cycle and intimacy records.

It runs in a Docker container on Jaime's NAS (Synology DS920+). Withings, Apple Health (Health Auto Export) and
Android (Health Connect, app in `android/`) send their data straight to the server. The page is the former
claude.ai artifact, served with a compatibility layer (`window.claude`) against the server API. The bridge with the
Google Sheet (Apps Script) is only left for accounts not moved yet and will be retired.

## Language policy

- **English is the official language of the project:** code comments, docstrings, identifiers (variables,
  functions, classes, files), documentation (README, CHANGELOG, help, deployment guide, this file) and commit
  messages.
- **Talk to Jaime always in Spanish** (messages, summaries, questions, reports).
- **Texts the users see** are translated (see "Texts and languages"). The page code still contains its visible texts
  in Spanish, mapped to the English catalog by `locales/es.json`; keep that bridge working when you change them.
- **Documentation is written in English only:** `help/en/`, `README.md` and `CHANGELOG.md`. The Help module of the
  app translates them automatically into each account's language (Claude API, `src/backend/app/help/translate.py`,
  cached until the English text changes).
- **Exception: Spanish.** It is the language most users use, so its translation of every document is kept in the
  repository (`help/i18n/es/`) and needs no translator. When you change an English document, update its Spanish
  translation and run `python3 tools/help_i18n.py stamp es <doc>`; `tools/help_i18n.py check` (also run by `pytest`)
  fails while one is out of date.

## Layout

```
src/backend/app/            FastAPI server (package `app`), one subpackage per module:
  main.py                   startup, common security and the routes of each module
  core/                     settings, SQLite, security, languages, backups, route dependencies
  accounts/                 accounts, sessions, invitations, access requests, "Your account", admin CLI
  admin/                    Administration panel
  couples/                  linking and unlinking couples
  data/                     documents of each account (the app's "db", with what a couple shares) and import
  help/                     the Help module (help, README and changelog, translated automatically)
  sheets/                   the data tabs as server tables and the XLSX workbook the page reads
  sources/                  Withings (OAuth) and Apple Health / Android (posts in Health Auto Export format)
  sync/                     synchronisation, Google bridge and scheduler
  mail/                     outgoing email (SMTP)
  web/                      assembly of the app page and static files
src/frontend/
  app/app_a|b|c.html        the app (the artifact's HTML: styles+views, core, interface)
  compat/claude-shim.js     window.claude layer against the server API
  accounts/ admin/ common/  sign-in, access request, registration, "Your account" and Administration pages
  i18n/                     translator, English catalog and one file per language
  package.json              libraries served without CDN (xlsx, jspdf, html2canvas-pro) and jsdom for the tests
android/                    Android app (Health Connect → server)
assets/branding/            icons and logo (do not change)
tests/<module>/             tests of each module (pytest) and tests/frontend/*.mjs (page and translator in jsdom)
help/en/                    user help, one file per module (English; translated automatically in the app)
docker/                     Dockerfile, compose.yml (NAS), compose.hot.yml, compose.dev.yml, entrypoint
docs/DEPLOYMENT.md          deployment on the NAS
tools/                      deployment, development server and translation tools
```

## Pending work

- Sources status in "Your account": latest data of each kind (weigh-in, night, Apple Health post by type), last
  synchronisation and errors.
- Translate the remaining Spanish code comments and internal identifiers into English.
- Retire the Google bridge (Apps Script, service account, sheet) once Jaime confirms.

## Rules

1. **Do not change the design.** The interface of `src/frontend/app/` must look and behave the same. Frontend
   changes are limited to what it needs to work outside claude.ai: exact replacements in
   `src/backend/app/web/page.py` and the layer `src/frontend/compat/claude-shim.js`. Do not rewrite the app in
   React/Vue or "clean up" its code. Design changes Jaime asks for are made, with the smallest change in
   `src/frontend/app/`.
2. **Data parity before improvements.** The data logic comes from the original Apps Script (`Codigo.gs`, no longer
   in the repository) and is ported in `src/backend/app/sources/` and `src/backend/app/sheets/rules.py`, with tests.
   Do not change it without a reason. Rules to keep:
   - **Night of day k:** the one ending between 17:00 of day k-1 and 17:00 of day k, and after 03:00 of day k;
     anything ending earlier is a nap.
   - **Episodes:** sleep separated by more than 90 min are different episodes; two night episodes (19:00–12:00)
     separated by ≤ 4 h are joined and the gap counts as a wake-up.
   - **Merging the night:** schedule, time asleep and wake-ups from AutoSleep if present; otherwise from the Apple
     Watch; otherwise from the source with most sleep. If the Watch records clearly more (> 1.2 × AutoSleep +
     15 min), the Watch wins. Deep and REM come from the Watch.
   - **Re-sends:** each post rules over the time span it covers, per source (what that source no longer sends in
     that span is deleted).
   - **Naps:** episodes ≥ 10 min outside the night. **Wake-ups:** gaps ≥ 10 min inside the night.
   - **Sources:** Apple Health rules; Withings only for weight and composition and to fill gaps.
3. **Texts the users see are translated** into every supported language (see "Texts and languages"), error messages
   and emails included.
4. **Secrets out of the code.** Withings (client id/secret, tokens), Health Auto Export tokens, passwords, Google
   credentials: only in environment variables or in the server database. Never in the frontend, the repository or
   the logs.
5. **Personal data out of the repository.** `data/`, `*.db`, `snap.json`, JSON backups and Health exports are in
   `.gitignore`. Test fixtures must be synthetic or minimal.
6. **Time zone `Europe/Madrid`** for every calculation of days and nights.
7. Small commits, with tests.

## Texts and languages

The **base language of the translations is English:** `src/frontend/i18n/catalog.json` has every message in English
and each language is `src/frontend/i18n/locales/<lang>.json` = `{"English message": "translation"}` (variable parts
are `{0}`, `{1}`…). Translators only need English: see `src/frontend/i18n/README.md`.

The page code is written in Spanish, so `locales/es.json` is the bridge: each English message maps to the Spanish
text **exactly as it is in the code** (or a list, when several Spanish texts share one message). With it the server
builds the browser dictionary (Spanish text → chosen language; a missing translation shows in English) and uses it
for the emails too. Default language of new accounts: English.

When you add or change visible texts (page, server pages, error messages, emails):
1. `python3 tools/i18n_extract.py` lists the texts of the code without an English message yet (`i18n/new.json`).
2. For each one, add the English message to `locales/es.json` (`{"English": "text in the code"}`) and run
   `python3 tools/i18n_catalog.py` to rebuild `catalog.json`.
3. Add the translations to every file in `locales/` (same tone and terms as the rest).
4. `python3 tools/i18n_check.py` must print OK (`pytest` checks it too).

## Changelog

- Every big change, new feature, enhancement or user-visible fix updates `CHANGELOG.md` (English) in the **current
  version** (the branch's), and its Spanish copy `help/i18n/es/changelog.md` in the same way; then run
  `python3 tools/help_i18n.py stamp es changelog`.
- Sections, in this order: Breaking Changes, New Features, Enhancements, Bug fixes, Documentation. If the release has
  Breaking Changes, that section always goes first, right after the release date.
- Add a new entry as the **last bullet** of its section.
- Keep it concise and describe the **final state** of the implementation, not the sequence of intermediate changes.
- Within the current (unreleased) version, do not add several bullets for incremental changes, fixes or refinements of
  the same functionality: if a bullet already describes it, update or rewrite that bullet so it reflects the final
  behaviour.
- No entries for internal changes with no user-facing or developer-facing impact.
- No blank lines between bullets of a section, nor between the section name and its first bullet.

## Documentation

- Whenever you implement or change a feature, review all the documentation related to it (`help/en/`, its Spanish
  copy in `help/i18n/es/`, `README.md`, `docs/DEPLOYMENT.md`) and update whatever is no longer accurate.
- Documentation describes the final supported behaviour, not intermediate attempts or temporary states.

## Commands

```
tools/dev-data.sh && tools/dev.sh                      # hot-reload development (http://localhost:8000) with a copy of the NAS data
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'   # local environment (PyCharm uses .venv)
.venv/bin/python -m pytest -q                          # backend tests
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs   # page start-up
node tests/frontend/i18n.mjs                           # translator
```

## Definition of done (for any change)

- `pytest` green and the frontend start-up and translator tests without errors.
- The image builds (`docker build -f docker/Dockerfile .`).
- Work on the **current version branch** (e.g. `0.1.0`), never directly on `main` (Jaime brings it up to date).
  Every push to that branch builds `jaimetur/bodylens:latest`. After pushing, deploy to the NAS with
  `tools/deploy.sh` (hot; it only waits for the image when dependencies or the Dockerfile change; see
  `docs/DEPLOYMENT.md`) and check that the `bodylens` container is `healthy`.
- No secret or personal data added to the repository.
- If the deployment changes, `docs/DEPLOYMENT.md` is updated; if the usage changes, the help in `help/`.
- `CHANGELOG.md` (and its Spanish copy) up to date following the "Changelog" rules above, and the related
  documentation reviewed following the "Documentation" rules.
