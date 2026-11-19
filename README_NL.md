# BodyLens

[English](README.md) · [Español](README_ES.md) · [Català](README_CA.md) · [Français](README_FR.md) · [Italiano](README_IT.md) ·
[Deutsch](README_DE.md) · [Português](README_PT.md) · **Nederlands** · [中文](README_ZH.md) ·
[日本語](README_JA.md)

**BodyLens** is een zelfgehoste persoonlijke gezondheidswebapp voor meerdere gebruikers. Ze brengt het gewicht en de
lichaamssamenstelling van je **Withings**-weegschaal samen met wat je telefoon en horloge registreren (slaap,
activiteit, hartslag, HRV, SpO2, VO2 max, ECG, cyclus, stemming…) uit **Apple Gezondheid** of **Android Health
Connect**. Ze draait in Docker op je eigen server, de gegevens komen vanzelf binnen en iedereen ziet alleen de eigen
gegevens.

## Functies

- **Overzicht:** trendgewicht, voortgang van het plan, “vandaag in één oogopslag” (paraatheid, slaap, slaapsaldo,
  HRV, stappen) en automatische inzichten en meldingen.
- **Gewicht:** afgevlakte trend, plan met streefsnelheden, prognose, weken, kalender en mijlpalen; gewichtsverloop
  door de jaren heen, afvalpogingen en terugvallen.
- **Lichaam:** samenstelling (vet, spieren, water, botten), BMI/FFMI met bereiken per leeftijd en geslacht,
  meetlintmaten, hart (rusthartslag, HRV, SpO2, VO2 max, ECG, hartslagmeldingen) en welzijn.
- **Activiteit:** stappen, calorieën en trainingsminuten met ringen en doelen, workouts en hun verband met het
  gewicht.
- **Slaap:** de afgelopen nacht met fasen, slaapsaldo over 7 nachten, dutjes, streefschema en analyse. Gegevens van
  AutoSleep en Apple Watch worden met eigen regels samengevoegd (venster van 17:00 tot 17:00 uur, wakker worden,
  dutjes).
- **Maaltijden:** een dagscore voor wat je eet, drinkt en aan beweging doet, en het geschatte effect op je gewicht.
- **Intiem:** cyclus (met voorspelling), seksuele activiteit en stemming, beveiligd met een privé-pincode.
- **Help** in de app: de help van elke module, deze README en het wijzigingslogboek, in jouw taal.
- **PDF-rapport** van de gekozen periode en **volledige back-ups** in JSON en CSV.
- **Interface:** licht en donker thema, ontworpen voor de telefoon (te installeren als app vanuit de browser),
  veeggebaren, lay-out voor brede schermen tot 1600 px.
- **Talen:** Engels (standaard), Spaans, Catalaans, Frans, Italiaans, Duits, Portugees, Nederlands, Chinees en
  Japans. Elk account kiest zijn eigen taal; e-mails komen aan in de taal van de ontvanger.

### Accounts

- **Meerdere accounts**, elk met eigen gegevens, inloggen met gebruikersnaam en wachtwoord.
- **Aanmelden:** toegangsverzoeken vanaf de inlogpagina, goedgekeurd door een beheerder (met e-mailmeldingen), of
  uitnodigingslinks voor eenmalig gebruik.
- **Koppels:** twee accounts kunnen worden gekoppeld om de cyclus- en intimiteitsgegevens samen te delen en te
  bewerken.
- **Profielen:** elk account kan meerdere profielen hebben (met optionele pincode), te beheren in *Jouw account*.
- **Beheer:** gebruikers (gebruikersnaam, naam, e-mail, wachtwoord, actief-schakelaar, beheerdersrol),
  toegangsverzoeken, uitnodigingen, e-mail (SMTP), inloggegevens van de Withings-app, back-ups en gegevensbronnen.

### Gegevens die vanzelf binnenkomen

- **Withings:** elk account koppelt via OAuth; wegingen, samenstelling, activiteit, workouts, slaap, SpO2, VO2 max en
  ECG worden om de paar minuten opgehaald, en direct zodra Withings een nieuwe meting meldt.
- **Apple Gezondheid:** de iPhone-app *Health Auto Export* post naar een persoonlijk adres van elk account.
- **Android:** de BodyLens-app voor Android (in `android/`) leest Health Connect en verstuurt elk uur in hetzelfde
  formaat.
- **Dagelijkse back-up** van de database om 03:30 uur (de laatste 30 worden bewaard).

## Hoe het is opgebouwd

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend:** één pagina (`src/frontend/app/`), ontstaan als claude.ai-artefact, geserveerd met een kleine laag
  (`src/frontend/compat/claude-shim.js`) die via de server-API implementeert wat de pagina vroeger aan claude.ai
  vroeg (`db`, `user`, `downloads`…).
- **Backend:** Python 3.12, FastAPI, SQLite (WAL) in `/data`, één proces met de planner erin.
- **Vertalingen:** de catalogus is Engels (`src/frontend/i18n/catalog.json`) en elke taal is
  `src/frontend/i18n/locales/<lang>.json`. De pagina wordt in de browser vertaald door `src/frontend/i18n/i18n.js`,
  dat ook getallen en datums opmaakt; de server gebruikt dezelfde bestanden voor e-mails. De help (`help/en/`), deze README en het
  wijzigingslogboek zijn in het Engels geschreven en worden automatisch vertaald naar de taal van elk account met de
  Claude-API (de sleutel stel je in bij Beheer → Vertaler); elke vertaling blijft bewaard tot de Engelse tekst verandert.
- **Beveiliging:** argon2-wachtwoorden, sessies op de server (HttpOnly/Secure/SameSite-cookie), anti-CSRF-header bij
  elke schrijfactie, frequentielimieten, elk account geïsoleerd, versleutelde OAuth-tokens; geheimen alleen in
  omgevingsvariabelen of in de serverdatabase.

## Structuur van de repository

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

## Ontwikkeling

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
Het laatste commando start http://localhost:8000 met hot reload: de pagina wordt ongewijzigd vanuit `src/`
geserveerd (even herladen is genoeg) en de backend herstart bij het opslaan. `tools/dev-data.sh` kopieert de
servergegevens naar `data-dev/` (wijzigingen tijdens de ontwikkeling gaan nooit terug). Er is ook
`docker compose -f docker/compose.dev.yml up --build`.

## Uitrol

Elke push naar de branch van de huidige versie (bijv. `0.1.0`) voert de tests uit en publiceert de image
`jaimetur/bodylens:latest` (amd64 en arm64) op Docker Hub; `main` publiceert `jaimetur/bodylens:main`. Op de
server: `docker/compose.yml` plus een `.env`-bestand. De NAS koppelt de code vanuit de stackmap, dus
`tools/deploy.sh` rolt een commit in enkele seconden uit zonder op een nieuwe image te wachten. Alle stappen:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) (in het Engels).

## Bijdragen aan vertalingen

Je hebt alleen Engels nodig: zie [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) (in het Engels) om een
taal toe te voegen of er een te verbeteren. De help, de README en het wijzigingslogboek worden automatisch vertaald: je bewerkt alleen de Engelse bestanden.

## Documentatie

- Gebruikershulp: [`help/`](help/en/README.md) (in het Engels; ook in de app, onder *Help*)
- Wijzigingen per versie: [`CHANGELOG.md`](CHANGELOG.md)
- Instructies voor codeeragenten: [`AGENTS.md`](AGENTS.md)

Persoonlijke gegevens komen nooit in de repository: databases, JSON-back-ups en `.env` staan in `.gitignore`.
